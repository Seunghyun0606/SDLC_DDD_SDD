#!/usr/bin/env python3
"""Cross-platform subprocess execution with lossless output decoding.

Captured process output is always bytes-first. The Harness does not rely on ``text=True`` or the
host locale for stdout/stderr. CMD/PowerShell handling is explicit and ``shell=True`` is forbidden.
"""
from __future__ import annotations

import codecs
import hashlib
import locale
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


class DecodeResult:
    def __init__(
        self,
        text: str,
        status: str,
        encoding: str | None,
        lossy: bool,
        byte_length: int,
        sha256: str,
        error: str | None = None,
    ) -> None:
        self.text = text
        self.status = status
        self.encoding = encoding
        self.lossy = lossy
        self.byte_length = byte_length
        self.sha256 = sha256
        self.error = error

    def metadata(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "encoding": self.encoding,
            "lossy": self.lossy,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
            **({"error": self.error} if self.error else {}),
        }


class ProcessResult:
    def __init__(
        self,
        *,
        original_command: list[str],
        resolved_command: list[str],
        execution_mode: str,
        returncode: int,
        stdout: str,
        stderr: str,
        stdout_decode: DecodeResult,
        stderr_decode: DecodeResult,
    ) -> None:
        self.original_command = original_command
        self.resolved_command = resolved_command
        self.execution_mode = execution_mode
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.stdout_decode = stdout_decode
        self.stderr_decode = stderr_decode

    @property
    def output_decode_ok(self) -> bool:
        return self.stdout_decode.status != "UNDECODABLE" and self.stderr_decode.status != "UNDECODABLE"


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _dedupe_encodings(values: Sequence[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw in values:
        value = str(raw or "").strip()
        if not value:
            continue
        try:
            canonical = codecs.lookup(value).name
        except LookupError:
            continue
        if canonical not in seen:
            seen.add(canonical)
            result.append(value)
    return result


def _windows_code_page_encodings() -> list[str]:
    if os.name != "nt":
        return []
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        pages = [int(kernel32.GetOEMCP()), int(kernel32.GetACP())]
        return [f"cp{page}" for page in pages if page > 0]
    except Exception:
        return []


def _utf16_without_bom_candidate(data: bytes) -> str | None:
    """Detect likely UTF-16 output without a BOM using byte-lane NUL dominance.

    PowerShell/Windows tools can emit UTF-16LE without a BOM. Korean UTF-16 code units may contain
    an occasional zero byte in the non-dominant lane, so a zero-tolerance threshold is too strict.
    We require a clearly dominant NUL lane instead of requiring the opposite lane to be almost empty.
    """
    if len(data) < 4 or len(data) % 2:
        return None
    pairs = max(len(data) // 2, 1)
    even_ratio = sum(1 for i in range(0, len(data), 2) if data[i] == 0) / pairs
    odd_ratio = sum(1 for i in range(1, len(data), 2) if data[i] == 0) / pairs

    def dominant(primary: float, secondary: float) -> bool:
        return primary >= 0.30 and (primary - secondary) >= 0.20 and primary >= max(secondary * 3.0, 0.30)

    if dominant(odd_ratio, even_ratio):
        return "utf-16-le"
    if dominant(even_ratio, odd_ratio):
        return "utf-16-be"
    return None


def _valid_decoded_text(text: str, encoding: str, *, allow_nul: bool = False) -> bool:
    if "\ufffd" in text:
        return False
    if "\x00" in text and not allow_nul and not encoding.lower().startswith("utf-16"):
        return False
    disallowed_controls = sum(1 for ch in text if ord(ch) < 32 and ch not in "\r\n\t\x00")
    if disallowed_controls > max(1, len(text) // 20):
        return False
    return True


def decode_process_bytes(
    data: bytes | None,
    *,
    preferred_encodings: Sequence[str] | None = None,
    allow_nul: bool = False,
) -> DecodeResult:
    raw = bytes(data or b"")
    digest = _sha256_bytes(raw)
    if not raw:
        return DecodeResult("", "EMPTY", None, False, 0, digest)

    bom_cases = [
        (codecs.BOM_UTF8, "utf-8-sig", "utf-8-sig"),
        (codecs.BOM_UTF16_LE, "utf-16", "utf-16-le"),
        (codecs.BOM_UTF16_BE, "utf-16", "utf-16-be"),
    ]
    for bom, decoder, reported in bom_cases:
        if raw.startswith(bom):
            try:
                text = raw.decode(decoder, errors="strict")
            except UnicodeDecodeError as exc:
                return DecodeResult("", "UNDECODABLE", reported, False, len(raw), digest, str(exc))
            if not _valid_decoded_text(text, reported, allow_nul=allow_nul):
                return DecodeResult("", "UNDECODABLE", reported, False, len(raw), digest, "invalid decoded text")
            return DecodeResult(text, "DECODED_BOM", reported, False, len(raw), digest)

    utf16_guess = _utf16_without_bom_candidate(raw)
    candidates: list[str | None] = [
        utf16_guess,
        "utf-8",
        *(preferred_encodings or []),
        *_windows_code_page_encodings(),
        locale.getpreferredencoding(False),
        "cp949",
        "euc-kr",
    ]
    errors: list[str] = []
    for encoding in _dedupe_encodings(candidates):
        try:
            text = raw.decode(encoding, errors="strict")
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}:{exc.start}")
            continue
        if not _valid_decoded_text(text, encoding, allow_nul=allow_nul):
            errors.append(f"{encoding}:invalid-text")
            continue
        status = "DECODED_PRIMARY" if codecs.lookup(encoding).name == "utf-8" else "DECODED_STRICT_FALLBACK"
        return DecodeResult(text, status, encoding, False, len(raw), digest)

    return DecodeResult(
        "",
        "UNDECODABLE",
        None,
        False,
        len(raw),
        digest,
        "safe subprocess output decoding failed; attempts=" + ",".join(errors),
    )


def _strip_outer_command_quotes(value: str) -> str:
    """Remove one outer quote layer, including config-escaped ``\"path\"`` wrappers.

    Only a quote pair wrapping the entire argv token is removed. Interior escaping is preserved.
    This makes values surviving JSON/YAML/Windows command configuration safe at the execution edge.
    """
    text = str(value)
    if len(text) >= 4 and text[:2] in {"\\\"", "\\'"} and text[-2:] == text[:2]:
        return text[2:-2]
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


def _basename(token: str) -> str:
    normalized = _strip_outer_command_quotes(str(token).strip()).replace("\\", "/")
    return normalized.rsplit("/", 1)[-1].lower()


def _find_executable(candidates: Sequence[str], which_fn: Callable[[str], str | None]) -> str | None:
    for candidate in candidates:
        found = which_fn(candidate)
        if found:
            return found
    return None


def prepare_command(
    command: Sequence[str],
    *,
    platform_name: str | None = None,
    env: Mapping[str, str] | None = None,
    which_fn: Callable[[str], str | None] = shutil.which,
) -> tuple[list[str], str]:
    original = [_strip_outer_command_quotes(str(part)) for part in command]
    if not original or not all(part for part in original):
        raise ValueError("process command must contain non-empty argv strings")

    platform_name = platform_name or os.name
    first = _basename(original[0])
    if first in {"cmd", "cmd.exe"}:
        return original, "CMD_EXPLICIT"
    if first in {"powershell", "powershell.exe"}:
        return original, "POWERSHELL_EXPLICIT"
    if first in {"pwsh", "pwsh.exe"}:
        return original, "PWSH_EXPLICIT"

    suffix = Path(first).suffix.lower()
    if suffix in {".cmd", ".bat"} and platform_name == "nt":
        source_env = dict(os.environ)
        if env:
            source_env.update({str(k): str(v) for k, v in env.items()})
        comspec = source_env.get("COMSPEC") or which_fn("cmd.exe") or "cmd.exe"
        return [comspec, "/d", "/s", "/c", subprocess.list2cmdline(original)], "CMD_AUTO"

    if suffix == ".ps1":
        candidates = ["pwsh.exe", "pwsh", "powershell.exe", "powershell"] if platform_name == "nt" else ["pwsh"]
        resolved = _find_executable(candidates, which_fn)
        if not resolved:
            raise FileNotFoundError("PowerShell host not found for .ps1 command; configure pwsh/powershell explicitly")
        mode = "PWSH_AUTO" if _basename(resolved) in {"pwsh", "pwsh.exe"} else "POWERSHELL_AUTO"
        return [
            resolved,
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-File",
            original[0],
            *original[1:],
        ], mode

    return original, "DIRECT"


def run_process(
    command: Sequence[str],
    *,
    cwd: str | Path,
    timeout: int | float,
    env: Mapping[str, str] | None = None,
    platform_name: str | None = None,
    preferred_encodings: Sequence[str] | None = None,
    allow_nul: bool = False,
    which_fn: Callable[[str], str | None] = shutil.which,
) -> ProcessResult:
    original = [_strip_outer_command_quotes(str(part)) for part in command]
    child_env = None
    if env is not None:
        child_env = dict(os.environ)
        child_env.update({str(k): str(v) for k, v in env.items()})
    resolved, mode = prepare_command(
        original,
        platform_name=platform_name,
        env=child_env,
        which_fn=which_fn,
    )
    completed = subprocess.run(
        resolved,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=False,
        timeout=timeout,
        check=False,
        env=child_env,
    )
    stdout_decoded = decode_process_bytes(
        completed.stdout,
        preferred_encodings=preferred_encodings,
        allow_nul=allow_nul,
    )
    stderr_decoded = decode_process_bytes(
        completed.stderr,
        preferred_encodings=preferred_encodings,
        allow_nul=allow_nul,
    )
    return ProcessResult(
        original_command=original,
        resolved_command=resolved,
        execution_mode=mode,
        returncode=int(completed.returncode),
        stdout=stdout_decoded.text,
        stderr=stderr_decoded.text,
        stdout_decode=stdout_decoded,
        stderr_decode=stderr_decoded,
    )
