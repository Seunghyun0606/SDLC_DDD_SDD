#!/usr/bin/env python3
"""Bidirectional MD/XLSX Worklist sync with revision-aware conflict detection.

Canonical YAML is the runtime authority. MD/XLSX are human-editable views. A changed existing
row must increment 변경버전. Same revision + different values is SYNC_CONFLICT and is never
silently overwritten.
"""
from __future__ import annotations
import argparse, copy, datetime as dt, re, sys, zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape
import yaml

NS="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG="http://schemas.openxmlformats.org/package/2006/relationships"

def load_yaml(p:Path): return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def columns(config): return config.get("columns") or []
def label_to_key(config): return {str(x["label"]):str(x["key"]) for x in columns(config)}
def key_to_label(config): return {str(x["key"]):str(x["label"]) for x in columns(config)}
def ordered_keys(config): return [str(x["key"]) for x in columns(config)]

def clean(v): return "" if v is None else str(v).strip()
def rev(row):
    try: return int(clean(row.get("revision")) or 0)
    except ValueError: return -1

def comparable(row, keys): return tuple(clean(row.get(k)) for k in keys if k!="updated_at")

def validate_rows(rows, config, source):
    errors=[]; ids=set()
    required=[x["key"] for x in columns(config) if x.get("required")]
    for i,row in enumerate(rows,1):
        wid=clean(row.get("work_item_id"))
        if not wid: errors.append(f"{source}[{i}]: 작업ID required"); continue
        if wid in ids: errors.append(f"{source}[{i}]: duplicate 작업ID {wid}")
        ids.add(wid)
        for key in required:
            if not clean(row.get(key)): errors.append(f"{source}[{i}] {wid}: required field missing: {key}")
        if rev(row)<0: errors.append(f"{source}[{i}] {wid}: invalid revision")
    return errors

def parse_md(path:Path, config):
    if not path.exists(): return []
    lines=path.read_text(encoding="utf-8").splitlines(); header=None; rows=[]; mapping=label_to_key(config)
    for idx,line in enumerate(lines):
        if not line.strip().startswith("|"): continue
        cells=[x.strip() for x in line.strip().strip("|").split("|")]
        if header is None and "작업ID" in cells:
            header=cells; continue
        if header is None: continue
        if all(re.fullmatch(r":?-{3,}:?",x or "") for x in cells): continue
        if len(cells)<len(header): cells += [""]*(len(header)-len(cells))
        row={mapping[h]:cells[i] for i,h in enumerate(header) if h in mapping}
        if clean(row.get("work_item_id")): rows.append(row)
    return rows

def shared_strings(zf):
    if "xl/sharedStrings.xml" not in zf.namelist(): return []
    root=ET.fromstring(zf.read("xl/sharedStrings.xml")); out=[]
    for si in root.findall(f"{{{NS}}}si"):
        out.append("".join((t.text or "") for t in si.iter(f"{{{NS}}}t")))
    return out

def col_index(ref):
    m=re.match(r"([A-Z]+)",ref or ""); n=0
    if not m: return 0
    for ch in m.group(1): n=n*26+ord(ch)-64
    return n-1

def xlsx_rows(path:Path):
    if not path.exists(): return []
    with zipfile.ZipFile(path) as zf:
        ss=shared_strings(zf)
        wb=ET.fromstring(zf.read("xl/workbook.xml")); rels=ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        relmap={x.attrib["Id"]:x.attrib["Target"] for x in rels.findall(f"{{{PKG}}}Relationship")}
        sheet=wb.find(f"{{{NS}}}sheets/{{{NS}}}sheet")
        rid=sheet.attrib[f"{{{REL}}}id"]; target=relmap[rid].lstrip("/")
        if not target.startswith("xl/"): target="xl/"+target
        root=ET.fromstring(zf.read(target)); result=[]
        for r in root.findall(f".//{{{NS}}}sheetData/{{{NS}}}row"):
            vals={}
            for c in r.findall(f"{{{NS}}}c"):
                idx=col_index(c.attrib.get("r","A1")); typ=c.attrib.get("t"); v=c.find(f"{{{NS}}}v"); value=""
                if typ=="inlineStr":
                    value="".join((t.text or "") for t in c.iter(f"{{{NS}}}t"))
                elif v is not None:
                    raw=v.text or ""; value=ss[int(raw)] if typ=="s" and raw.isdigit() and int(raw)<len(ss) else raw
                vals[idx]=value
            if vals: result.append([vals.get(i,"") for i in range(max(vals)+1)])
        return result

def parse_xlsx(path:Path, config):
    matrix=xlsx_rows(path)
    if not matrix: return []
    mapping=label_to_key(config); header_idx=None
    for i,row in enumerate(matrix):
        if "작업ID" in row: header_idx=i; break
    if header_idx is None: raise ValueError("XLSX header 작업ID not found")
    header=matrix[header_idx]; out=[]
    for raw in matrix[header_idx+1:]:
        raw=raw+[""]*(len(header)-len(raw)); row={mapping[h]:raw[i] for i,h in enumerate(header) if h in mapping}
        if clean(row.get("work_item_id")): out.append(row)
    return out

def canonical_rows(path:Path):
    if not path.exists(): return []
    return ((load_yaml(path).get("worklist_canonical") or {}).get("items") or [])

def merge(md, xls, canonical, config):
    keys=ordered_keys(config)
    sources={"MD":md,"XLSX":xls,"CANONICAL":canonical}
    maps={name:{clean(r.get("work_item_id")):copy.deepcopy(r) for r in rows} for name,rows in sources.items()}
    conflicts=[]; merged=[]; changed_ids=[]
    for wid in sorted(set().union(*(set(m) for m in maps.values()))):
        can=maps["CANONICAL"].get(wid)
        views=[(name,maps[name][wid]) for name in ("MD","XLSX") if wid in maps[name]]
        if can is None:
            if not views:
                continue
            maxrev=max(max(rev(r),1) for _,r in views)
            top=[(n,r) for n,r in views if max(rev(r),1)==maxrev]
            variants={comparable(r,keys) for _,r in top}
            if len(variants)>1:
                conflicts.append({"work_item_id":wid,"revision":maxrev,"sources":[n for n,_ in top],"code":"SYNC_CONFLICT"})
                continue
            chosen=copy.deepcopy(top[0][1]); chosen["revision"]=str(maxrev); chosen["updated_at"]=now(); changed_ids.append(wid)
            merged.append({k:clean(chosen.get(k)) for k in keys}); continue

        can_rev=rev(can)
        changed_views=[]
        for name,row in views:
            row_changed=comparable(row,keys)!=comparable(can,keys)
            row_rev=rev(row)
            if row_changed and row_rev<=can_rev:
                conflicts.append({"work_item_id":wid,"revision":row_rev,"canonical_revision":can_rev,"sources":[name,"CANONICAL"],"code":"UNVERSIONED_EDIT"})
            elif row_changed:
                changed_views.append((name,row))
        if any(c["work_item_id"]==wid for c in conflicts):
            continue
        if not changed_views:
            chosen=copy.deepcopy(can)
            if not clean(chosen.get("updated_at")): chosen["updated_at"]=now()
            merged.append({k:clean(chosen.get(k)) for k in keys}); continue

        maxrev=max(rev(r) for _,r in changed_views)
        top=[(n,r) for n,r in changed_views if rev(r)==maxrev]
        variants={comparable(r,keys) for _,r in top}
        if len(variants)>1:
            conflicts.append({"work_item_id":wid,"revision":maxrev,"sources":[n for n,_ in top],"code":"SYNC_CONFLICT"})
            continue
        chosen=copy.deepcopy(top[0][1]); chosen["revision"]=str(maxrev); chosen["updated_at"]=now(); changed_ids.append(wid)
        merged.append({k:clean(chosen.get(k)) for k in keys})
    return merged,conflicts,changed_ids

def md_escape(v): return clean(v).replace("|","\\|").replace("\n","<br>")
def write_md(path, rows, config):
    labels=[key_to_label(config)[k] for k in ordered_keys(config)]; keys=ordered_keys(config)
    lines=["# 전체 작업 목록","","> 이 파일은 Canonical Work Item의 사용자 View다. MD/XLSX 어느 쪽을 수정하든 `변경버전`을 올린 뒤 Sync한다.","", "| "+" | ".join(labels)+" |", "|"+"|".join(["---"]*len(labels))+"|"]
    for row in rows: lines.append("| "+" | ".join(md_escape(row.get(k)) for k in keys)+" |")
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text("\n".join(lines)+"\n",encoding="utf-8")

def cell_ref(col,row):
    s=""; n=col
    while n: n,rem=divmod(n-1,26); s=chr(65+rem)+s
    return f"{s}{row}"
def write_xlsx(path, rows, config):
    labels=[key_to_label(config)[k] for k in ordered_keys(config)]; keys=ordered_keys(config); matrix=[labels]+[[clean(r.get(k)) for k in keys] for r in rows]
    xmlrows=[]
    for rno,row in enumerate(matrix,1):
        cells=[]
        for cno,val in enumerate(row,1):
            ref=cell_ref(cno,rno); cells.append(f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{escape(val)}</t></is></c>')
        xmlrows.append(f'<row r="{rno}">'+"".join(cells)+"</row>")
    cols=[]
    for i,key in enumerate(keys,1):
        width=14
        if key in {"name","alerts","note"}: width=28
        elif key in {"updated_at"}: width=24
        cols.append(f'<col min="{i}" max="{i}" width="{width}" customWidth="1"/>')
    sheet='<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="'+NS+'"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols>'+"".join(cols)+'</cols><sheetData>'+"".join(xmlrows)+'</sheetData><autoFilter ref="A1:'+cell_ref(len(keys),len(matrix))+'"/></worksheet>'
    files={
      '[Content_Types].xml':'<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',
      '_rels/.rels':'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="'+PKG+'"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',
      'xl/workbook.xml':'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="'+NS+'" xmlns:r="'+REL+'"><sheets><sheet name="전체작업목록" sheetId="1" r:id="rId1"/></sheets></workbook>',
      'xl/_rels/workbook.xml.rels':'<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="'+PKG+'"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',
      'xl/worksheets/sheet1.xml':sheet,
    }
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as zf:
        for name,data in files.items(): zf.writestr(name,data.encode('utf-8'))

def main():
    p=argparse.ArgumentParser(); p.add_argument("--md",type=Path,required=True); p.add_argument("--xlsx",type=Path,required=True); p.add_argument("--canonical",type=Path,required=True); p.add_argument("--config","--columns",dest="config",type=Path,default=Path("sdlc/config/worklist-columns.yaml")); p.add_argument("--conflicts",type=Path); a=p.parse_args(); cfg=load_yaml(a.config)
    try: md=parse_md(a.md,cfg); xls=parse_xlsx(a.xlsx,cfg); can=canonical_rows(a.canonical)
    except Exception as exc: print(f"WORKLIST_LOAD_ERROR: {exc}",file=sys.stderr); return 2
    errors=validate_rows(md,cfg,"MD")+validate_rows(xls,cfg,"XLSX")+validate_rows(can,cfg,"CANONICAL")
    if errors: print("\n".join(errors),file=sys.stderr); return 2
    merged,conflicts,changed_ids=merge(md,xls,can,cfg)
    if conflicts:
        out={"schema_version":1,"artifact_type":"WORKLIST_SYNC_CONFLICT","conflicts":conflicts}
        target=a.conflicts or a.canonical.with_name("worklist-sync-conflicts.yaml"); target.parent.mkdir(parents=True,exist_ok=True); target.write_text(yaml.safe_dump(out,allow_unicode=True,sort_keys=False),encoding="utf-8")
        print(f"SYNC_CONFLICT: {len(conflicts)} conflict(s); no view overwritten",file=sys.stderr); return 3
    canout={"schema_version":1,"artifact_type":"WORKLIST_CANONICAL","worklist_canonical":{"items":merged,"item_count":len(merged),"synced_at":now(),"views":[str(a.md),str(a.xlsx)]}}
    a.canonical.parent.mkdir(parents=True,exist_ok=True); a.canonical.write_text(yaml.safe_dump(canout,allow_unicode=True,sort_keys=False),encoding="utf-8")
    write_md(a.md,merged,cfg); write_xlsx(a.xlsx,merged,cfg)
    print(f"OK: worklist sync complete items={len(merged)} changed={len(changed_ids)} canonical={a.canonical}"); return 0
if __name__=="__main__": raise SystemExit(main())
