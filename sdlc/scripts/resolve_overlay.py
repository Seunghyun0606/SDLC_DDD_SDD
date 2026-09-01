#!/usr/bin/env python3
"""Materialize effective AI-SDLC Harness files from Core + ordered overlays.

The resolver intentionally uses only the Python standard library. Overlay manifests
are JSON so the portable Harness does not require a project-specific YAML package.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

CORE_RULE_ROOT = Path('.cursor/rules')
CORE_SKILL_ROOT = Path('.cursor/skills')
CORE_TEMPLATE_ROOT = Path('sdlc/templates/core')


def _safe_relative(value: str) -> Path:
    p = Path(value)
    if p.is_absolute() or '..' in p.parts:
        raise ValueError(f'unsafe overlay path: {value}')
    return p


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _split_sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    lines = text.splitlines(keepends=True)
    preamble: list[str] = []
    sections: list[tuple[str, list[str]]] = []
    current: tuple[str, list[str]] | None = None
    for line in lines:
        if line.startswith('## '):
            current = (line.strip(), [line])
            sections.append(current)
        elif current is None:
            preamble.append(line)
        else:
            current[1].append(line)
    return ''.join(preamble), [(heading, ''.join(body)) for heading, body in sections]


def _append_to_section(text: str, heading: str, addition: str) -> str:
    preamble, sections = _split_sections(text)
    found = False
    out: list[str] = [preamble]
    for section_heading, body in sections:
        if section_heading == heading:
            found = True
            body = body.rstrip() + '\n\n' + addition.strip() + '\n'
        out.append(body)
    if not found:
        raise ValueError(f'overlay section not found: {heading}')
    return ''.join(out)


def _insert_section_after(text: str, heading: str, new_heading: str, content: str) -> str:
    preamble, sections = _split_sections(text)
    if any(h == new_heading for h, _ in sections):
        raise ValueError(f'duplicate inserted section: {new_heading}')
    found = False
    out: list[str] = [preamble]
    for section_heading, body in sections:
        out.append(body)
        if section_heading == heading:
            found = True
            out.append(f'\n{new_heading}\n{content.strip()}\n')
    if not found:
        raise ValueError(f'overlay insertion anchor not found: {heading}')
    return ''.join(out)


def _apply_file_patch(text: str, patch: dict[str, Any]) -> str:
    for token, value in patch.get('replace_tokens', {}).items():
        text = text.replace(token, str(value))
    for heading, addition in patch.get('append_sections', {}).items():
        text = _append_to_section(text, heading, str(addition))
    for item in patch.get('insert_sections_after', []):
        text = _insert_section_after(text, item['after'], item['heading'], item['content'])
    return text


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    for path in src.rglob('*'):
        if path.is_file():
            rel = path.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def _load_overlay(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding='utf-8'))
    if data.get('schema_version') != 1:
        raise ValueError(f'unsupported overlay schema: {path}')
    return data


def materialize(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding='utf-8'))
    if config.get('schema_version') != 1:
        raise ValueError('unsupported overlay resolution config schema')

    if output.exists():
        shutil.rmtree(output)
    (output / 'rules').mkdir(parents=True, exist_ok=True)
    (output / 'skills').mkdir(parents=True, exist_ok=True)
    (output / 'templates').mkdir(parents=True, exist_ok=True)
    (output / 'standards').mkdir(parents=True, exist_ok=True)

    _copy_tree(root / CORE_RULE_ROOT, output / 'rules')
    _copy_tree(root / CORE_SKILL_ROOT, output / 'skills')
    _copy_tree(root / CORE_TEMPLATE_ROOT, output / 'templates')

    provenance: list[dict[str, Any]] = [{"layer": "core", "path": "builtin"}]
    applied_files: list[dict[str, Any]] = []
    overlay_paths: list[tuple[str, Path]] = []

    for key in ('preset_overlay', 'project_overlay'):
        value = config.get(key)
        if value:
            overlay_paths.append((key, root / _safe_relative(value)))
    for value in config.get('domain_overlays', []):
        overlay_paths.append(('domain_overlay', root / _safe_relative(value)))
    value = config.get('local_override')
    if value:
        overlay_paths.append(('local_override', root / _safe_relative(value)))

    for layer, path in overlay_paths:
        overlay = _load_overlay(path)
        provenance.append({"layer": layer, "name": overlay.get('name'), "path": str(path.relative_to(root))})

        for target_key, target_root in (('templates', output / 'templates'), ('skills', output / 'skills')):
            for rel_text, patch in overlay.get(target_key, {}).items():
                rel = _safe_relative(rel_text)
                target = target_root / rel
                if not target.is_file():
                    raise ValueError(f'overlay target missing: {target_key}/{rel}')
                before = target.read_text(encoding='utf-8')
                after = _apply_file_patch(before, patch)
                target.write_text(after, encoding='utf-8')
                applied_files.append({
                    'layer': layer,
                    'target': f'{target_key}/{rel.as_posix()}',
                    'before_sha256': _sha256_text(before),
                    'after_sha256': _sha256_text(after),
                })

        manifest_dir = path.parent
        for rel_text in overlay.get('rule_fragments', []):
            rel = _safe_relative(rel_text)
            src = manifest_dir / rel
            if not src.is_file():
                raise ValueError(f'rule fragment missing: {src}')
            prefix = f"{len(provenance):02d}-{layer}"
            dst = output / 'rules' / f'{prefix}-{src.name}'
            shutil.copy2(src, dst)
            applied_files.append({'layer': layer, 'target': f'rules/{dst.name}', 'after_sha256': hashlib.sha256(dst.read_bytes()).hexdigest()})

        for rel_text in overlay.get('standard_files', []):
            rel = _safe_relative(rel_text)
            src = manifest_dir / rel
            if not src.is_file():
                raise ValueError(f'standard file missing: {src}')
            dst = output / 'standards' / layer / rel.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            applied_files.append({'layer': layer, 'target': f'standards/{layer}/{rel.name}', 'after_sha256': hashlib.sha256(dst.read_bytes()).hexdigest()})

    manifest = {
        'schema_version': 1,
        'resolution_order': [p['layer'] for p in provenance],
        'provenance': provenance,
        'applied_files': applied_files,
    }
    (output / 'effective-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='.')
    parser.add_argument('--config', default='sdlc/config/overlay-resolution.example.json')
    parser.add_argument('--output', default='sdlc/runtime/effective')
    args = parser.parse_args()
    root = Path(args.root).resolve()
    config = (root / args.config).resolve()
    output = (root / args.output).resolve()
    manifest = materialize(root, config, output)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
