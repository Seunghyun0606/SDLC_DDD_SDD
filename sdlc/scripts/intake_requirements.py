#!/usr/bin/env python3
"""Official zero-to-one Requirement intake. User entry: `harness.py intake requirements.xlsx`."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent

def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    mod = importlib.util.module_from_spec(spec); assert spec and spec.loader
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod

PARSER = _load("requirement_intake_parser", "import_requirements.py")
APPLY = _load("requirement_intake_apply", "apply_canonical_delta.py")
MAIN, REL = PARSER.MAIN, PARSER.REL


def _existing(store: dict, kind: str) -> dict[str, str]:
    return {
        str(e.get("fields", {}).get("intake_stable_key")): eid
        for eid, e in store.get("entities", {}).items()
        if e.get("entity_type") == kind and e.get("fields", {}).get("intake_stable_key")
    }


def _ids(store: dict, prefix: str):
    pattern = re.compile(rf"^{prefix}-(\d+)$")
    n = max([int(m.group(1)) for eid in store.get("entities", {}) if (m := pattern.match(eid))] or [0])
    while True:
        n += 1
        yield f"{prefix}-{n:03d}"


def _locator(rows: list[dict], source_ids: list[str]) -> str:
    wanted = set(source_ids); found = [r for r in rows if r.get("source_record_id") in wanted]
    if not found: return "OPEN"
    return f'{found[0].get("source_sheet", "Sheet1")}!rows:' + ",".join(str(r["source_row"]) for r in found)


def build_delta(data: dict, store: dict, source_name: str) -> tuple[dict, dict]:
    rq_old, fr_old = _existing(store, "RQ"), _existing(store, "FR")
    rq_new, fr_new = _ids(store, "RQ"), _ids(store, "FR")
    rows, source_hash = data["source_records"], data["source_metadata"]["source_hash"]
    ops, targets, parent, preserved = [], [], {}, []
    external_counts: dict[str, int] = {}
    for fr in data["fr_candidates"]:
        ext = str(fr.get("external_requirement_id") or "")
        external_counts[ext] = external_counts.get(ext, 0) + 1

    def entity(eid: str, kind: str, fields: dict, loc: str):
        evidence = {"evidence_class":"GIVEN", "locator":loc, "source_hash":source_hash,
                    "note":"Requirement Source evidence; not Business Truth confirmation."}
        old = store.get("entities", {}).get(eid)
        if old and old.get("truth_status") == "CONFIRMED_BUSINESS":
            ops.append({"op":"ADD_PROVENANCE", "id":eid, **evidence}); preserved.append(eid); return
        ops.append({"op":"UPSERT_ENTITY", "id":eid, "entity_type":kind, "fields":fields,
                    "truth_status":"CANDIDATE", **evidence})

    for rq in data["rq_candidates"]:
        stable = rq.get("stable_key") or PARSER.stable_group_key((rq["level1"], rq["level2"], rq["name"]))
        eid = rq_old.get(stable) or next(rq_new); parent[rq["candidate_id"]] = eid; targets.append(eid)
        source_ids = rq["source_record_ids"]
        entity(eid, "RQ", {
            "name":rq["name"], "level1":rq["level1"], "level2":rq["level2"],
            "external_requirement_ids":rq["external_requirement_ids"], "intake_stable_key":stable,
            "source_record_ids":source_ids, "current_problem":"OPEN", "desired_result":"OPEN",
            "business_rules":"OPEN", "review_status":"AGENT_DRAFT_THEN_HUMAN_CONFIRM",
        }, _locator(rows, source_ids))

    for fr in data["fr_candidates"]:
        base_stable = fr.get("stable_key") or f'external:{fr["external_requirement_id"]}'
        # Duplicate external IDs are explicitly a review condition. Keep each source row
        # as a separate FR candidate instead of silently collapsing them on re-intake.
        stable = base_stable
        if external_counts.get(str(fr.get("external_requirement_id") or ""), 0) > 1:
            stable = f'{base_stable}|source:{fr["source_record_id"]}'
        eid = fr_old.get(stable) or next(fr_new); source_ids = [fr["source_record_id"]]
        entity(eid, "FR", {"name":fr["name"], "external_requirement_id":fr["external_requirement_id"],
                           "intake_stable_key":stable, "source_record_id":fr["source_record_id"],
                           "review_status":"CANDIDATE"}, _locator(rows, source_ids))
        ops.append({"op":"UPSERT_RELATION", "from":parent[fr["parent_rq_candidate_id"]],
                    "kind":"HAS_FR_CANDIDATE", "to":eid, "evidence_class":"GIVEN",
                    "locator":_locator(rows, source_ids), "source_hash":source_hash,
                    "note":"Source grouping candidate; not approved decomposition."})

    semantic = json.dumps(ops, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    token = f"{source_name}\x1f{source_hash}\x1f{semantic}".encode()
    delta = {"schema_version":1, "delta_id":"INTAKE-"+hashlib.sha256(token).hexdigest()[:24],
             "base_revision":int(store.get("revision",0)), "stage":"INTAKE",
             "source_artifact":source_name, "operations":ops}
    if not ops: delta["no_change_reason"] = "No valid requirement rows."
    return delta, {"rq_target_ids":targets, "confirmed_entities_preserved":sorted(set(preserved))}


def report(data: dict, source_name: str) -> str:
    r, c = data["import_result"], data["canonical"]; targets = c.get("rq_target_ids", [])
    lines = ["# 요구사항 인입 결과", "", f"> 제공 자료: `{source_name}`", "", "## 한눈에 보기", "",
             "| 항목 | 결과 |", "|---|---:|", f'| 원본 요구 행 | {r["source_rows"]} |',
             f'| 정상 인입 | {r["imported_rows"]} |', f'| RQ 후보 | {r["rq_candidate_count"]} |',
             f'| FR 후보 | {r["fr_candidate_count"]} |', f'| 유사 그룹 확인 필요 | {r["grouping_review_count"]} |',
             f'| 중복 외부 ID | {r["duplicate_external_ids"]} |', f'| 형식 오류 행 | {r["invalid_rows"]} |', "",
             "## Agent가 다음 단계에서 초안할 내용", "", "- 현재 문제·기대 결과·BR은 근거가 없으면 OPEN 유지",
             "- Source의 기능 행을 근거로 FR/AC 초안 생성", "", "## 사람이 확인해야 할 항목만", "",
             "1. 유사 RQ 실제 병합 여부", "2. 중복 외부 ID의 기준 원문", "3. 업무 정책·범위·승인 등 판단권한 항목",
             "4. Invalid 행 보정 여부", "5. 확정 Business Truth 변경 승인 여부", "",
             "사람이 빈 Requirement Template을 직접 채우는 것은 기본 절차가 아니다.", "", "## 유사 그룹 확인", ""]
    if data["grouping_reviews"]:
        lines += ["| 후보 A | 후보 B | 유사도 | 자동병합 |", "|---|---|---:|---|"]
        lines += [f'| {x["name_a"]} | {x["name_b"]} | {x["similarity"]:.4f} | 아니오 |' for x in data["grouping_reviews"]]
    else: lines += ["- 없음"]
    lines += ["", "## 생성된 작업 대상", ""]
    lines += [f'- `{t}` → `python sdlc/scripts/harness.py work --target {t}`' for t in targets] or ["- 없음"]
    lines += ["", "## 다음 작업", ""]
    if targets:
        lines += ["```bash", f"python sdlc/scripts/harness.py work --target {targets[0]}", "```"]
    lines += ["", "## 근거 보존 원칙", "", "- 유사 제목 자동 병합 금지", "- 원문/외부 ID/Sheet/Row/Source Hash 보존",
              "- Source는 CANDIDATE이며 CONFIRMED_BUSINESS로 자동 승격하지 않음",
              "- 기존 CONFIRMED_BUSINESS는 재인입 Source로 덮어쓰거나 낮추지 않음", ""]
    return "\n".join(lines)


def run_intake(xlsx: Path, *, profile_path: Path|None, json_out: Path, report_out: Path|None,
               store_path: Path, apply_to_canonical: bool=True) -> dict:
    profile = PARSER.load_profile(profile_path) if profile_path else PARSER.IntakeProfile()
    sheet, matrix = PARSER.read_xlsx_matrix(xlsx); h = PARSER.source_hash(xlsx)
    rows, invalid = PARSER.map_rows(matrix, profile, xlsx.name, sheet, h)
    data = PARSER.transform(rows, invalid)
    data["source_metadata"] = PARSER.build_source_metadata(matrix, profile, xlsx.name, sheet, h)
    for rq in data["rq_candidates"]: rq["current_problem"] = rq["desired_result_status"] = "OPEN"
    if apply_to_canonical:
        delta, mapping = build_delta(data, APPLY.load_store(store_path), xlsx.name)
        result, resulting = APPLY.apply_delta_to_store(store_path, delta)
        if result.get("status") not in {"APPLIED","IDEMPOTENT","NO_CHANGE"}: raise ValueError(f"Canonical intake failed: {result}")
        data["canonical"] = {"status":result["status"], "store_revision":resulting.get("revision"),
                             "delta_id":delta["delta_id"], **mapping}
    else: data["canonical"] = {"status":"CANDIDATE_ONLY", "rq_target_ids":[], "confirmed_entities_preserved":[]}
    json_out.parent.mkdir(parents=True, exist_ok=True); json_out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if report_out:
        report_out.parent.mkdir(parents=True, exist_ok=True); report_out.write_text(report(data,xlsx.name),encoding="utf-8")
    return data


def main(argv: list[str]|None=None) -> int:
    p=argparse.ArgumentParser(description="Requirement XLSX → safe Canonical candidates → concrete RQ target")
    p.add_argument("xlsx"); p.add_argument("--root",default="."); p.add_argument("--profile")
    p.add_argument("--store",default="sdlc/canonical/store.json"); p.add_argument("--json-out",default="sdlc/runtime/intake/requirements-import.json")
    p.add_argument("--report-out",default="docs/00_관리/요구사항_인입결과.md"); p.add_argument("--candidate-only",action="store_true")
    a=p.parse_args(argv); root=Path(a.root).resolve()
    def path(v):
        if v is None: return None
        x=Path(v); return x if x.is_absolute() else root/x
    try:
        xlsx=path(a.xlsx)
        if not xlsx or not xlsx.is_file(): raise ValueError(f"requirement file not found: {xlsx}")
        if xlsx.suffix.lower() != ".xlsx": raise ValueError("Core intake accepts structured XLSX; use document evidence extraction for other formats")
        data=run_intake(xlsx,profile_path=path(a.profile),json_out=path(a.json_out),report_out=path(a.report_out),store_path=path(a.store),apply_to_canonical=not a.candidate_only)
    except (OSError,ValueError,KeyError,zipfile.BadZipFile,json.JSONDecodeError) as e:
        print(json.dumps({"status":"INTAKE_FAILED","error":str(e)},ensure_ascii=False,indent=2)); return 2
    targets=data["canonical"].get("rq_target_ids",[])
    out={"status":"INTAKE_READY_FOR_WORK" if targets else "INTAKE_NO_TARGET","import_result":data["import_result"],"canonical":data["canonical"],
         "human_report":a.report_out,"first_target":targets[0] if targets else None,
         "next_command":f"python sdlc/scripts/harness.py work --target {targets[0]}" if targets else None,
         "plan_command":f"python sdlc/scripts/harness.py work --target {targets[0]} --plan-only" if targets else None}
    print(json.dumps(out,ensure_ascii=False,indent=2)); return 0 if targets or a.candidate_only else 3

if __name__ == "__main__": raise SystemExit(main())
