#!/usr/bin/env python3
"""Cross-platform subprocess execution with lossless output decoding.

The Harness never relies on ``text=True`` / host locale for captured process output.
It captures bytes, decodes stdout/stderr independently, and records the decoder used.

Shell handling is explicit:
- DIRECT: normal executable argv
- CMD_AUTO: .cmd/.bat on Windows via COMSPEC /d /s /c
- POWERSHELL_AUTO / PWSH_AUTO: .ps1 via an available PowerShell host
- *_EXPLICIT: caller already supplied cmd.exe / powershell.exe / pwsh

``shell=True`` is intentionally not used.
"""
from __future__ import annotations

import codecs
import hashlib
import locale
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


@dataclass(frozen=True)
class DecodeResult:
    text: str
    status: str
    encoding: str | None
    lossy: bool
    byte_length: int
    sha256: str
    error: str | None = None

    def metadata(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "encoding": self.encoding,
            "lossy": self.lossy,
            "byte_length": self.byte_length,
            "sha256": self.sha256,
            **({"error": self.error} if self.error else {}),
        }


@dataclass(frozen=True)
class ProcessResult:
    original_command: list[str]
    resolved_command: list[str]
    execution_mode: str
    returncode: int
    stdout: str
    stderr: str
    stdout_decode: DecodeResult
    stderr_decode: DecodeResult

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
    if len(data) < 4 or len(data) % 2:
        return None
    pairs = max(len(data) // 2, 1)
    even_nuls = sum(1 for i in range(0, len(data), 2) if data[i] == 0)
    odd_nuls = sum(1 for i in range(1, len(data), 2) if data[i] == 0)
    if odd_nuls / pairs >= 0.35 and even_nuls / pairs <= 0.05:
        return "utf-16-le"
    if even_nuls / pairs >= 0.35 and odd_nuls / pairs <= 0.05:
        return "utf-16-be"
    return None


def _valid_decoded_text(text: str, encoding: str) -> bool:
    if "\ufffd" in text:
        return False
    if "\x00" in text and not encoding.lower().startswith("utf-16"):
        return False
    return True


def decode_process_bytes(
    data: bytes | None,
    *,
    preferred_encodings: Sequence[str] | None = None,
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
            if not _valid_decoded_text(text, reported):
                return DecodeResult("", "UNDECODABLE", reported, False, len(raw), digest, "invalid decoded text")
            return DecodeResult(text, "DECODED_BOM", reported, False, len(raw), digest)

    utf16_guess = _utf16_without_bom_candidate(raw)
    candidates: list[str | None] = [
        "utf-8",
        utf16_guess,
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
        if not _valid_decoded_text(text, encoding):
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


def _basename(token: str) -> str:
    normalized = str(token).strip().strip('"').replace("\\", "/")
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
    original = [str(part) for part in command]
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
    which_fn: Callable[[str], str | None] = shutil.which,
) -> ProcessResult:
    original = [str(part) for part in command]
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
    stdout_decoded = decode_process_bytes(completed.stdout, preferred_encodings=preferred_encodings)
    stderr_decoded = decode_process_bytes(completed.stderr, preferred_encodings=preferred_encodings)
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
