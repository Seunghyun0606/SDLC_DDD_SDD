#!/usr/bin/env python3
"""Bidirectional 전체작업목록 Markdown/XLSX sync (stdlib only)."""
from __future__ import annotations
import argparse, json, math, re, sys, zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

SHEET = "전체작업목록"
MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKGREL = "http://schemas.openxmlformats.org/package/2006/relationships"
GENERATED = {"revision", "updated_at"}
NUMERIC = {"revision", "estimated_effort", "actual_effort"}

@dataclass(frozen=True)
class Column:
    key: str
    label: str
    required: bool = False
    generated: bool = False

def now():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def columns(path: Path):
    out, cur, active = [], None, False
    for raw in path.read_text(encoding="utf-8").splitlines():
        s = raw.strip()
        if not s or s.startswith("#"): continue
        if s == "columns:": active = True; continue
        if not active: continue
        if raw.startswith("  - "):
            if cur: out.append(cur)
            cur = {}
            k, v = raw[4:].split(":", 1); cur[k.strip()] = v.strip()
        elif cur is not None and raw.startswith("    ") and ":" in s:
            k, v = s.split(":", 1); cur[k.strip()] = v.strip()
    if cur: out.append(cur)
    def scalar(v):
        if v.lower() in ("true", "false"): return v.lower() == "true"
        return v[1:-1] if len(v) > 1 and v[0] == v[-1] and v[0] in "\"'" else v
    specs = [Column(str(scalar(x["key"])), str(scalar(x["label"])), bool(scalar(x.get("required","false"))), bool(scalar(x.get("generated","false")))) for x in out]
    if not specs or specs[0].key != "work_item_id": raise ValueError("work_item_id must be first")
    if len({x.key for x in specs}) != len(specs) or len({x.label for x in specs}) != len(specs): raise ValueError("duplicate column")
    return specs

def coerce(key, value):
    if value in (None, ""): return ""
    if key == "revision":
        try: return int(float(value))
        except (TypeError, ValueError): return 0
    if key in NUMERIC:
        try:
            n = float(value); return int(n) if n.is_integer() else n
        except (TypeError, ValueError): pass
    return str(value)

def norm(row, specs): return {c.key: coerce(c.key, row.get(c.key,"")) for c in specs}

def validate(rows, specs):
    req, seen = [c for c in specs if c.required], set()
    for i, row in enumerate(rows, 1):
        for c in req:
            if row.get(c.key,"") == "": raise ValueError(f"row {i}: {c.label} required")
        wid = str(row.get("work_item_id",""))
        if wid in seen: raise ValueError(f"duplicate work_item_id: {wid}")
        seen.add(wid)

def md_cells(line):
    t=line.strip().strip("|"); cells=[]; buf=[]; esc=False
    for ch in t:
        if esc: buf.append(ch); esc=False
        elif ch=="\\": esc=True
        elif ch=="|": cells.append("".join(buf).strip()); buf=[]
        else: buf.append(ch)
    cells.append("".join(buf).strip()); return cells

def read_md(path, specs):
    lines=path.read_text(encoding="utf-8").splitlines(); labels=[c.label for c in specs]; header=None
    for i,line in enumerate(lines[:-1]):
        cells=md_cells(line) if line.lstrip().startswith("|") else []
        if cells and cells[0]==labels[0] and all(re.fullmatch(r":?-{3,}:?",x.strip()) for x in md_cells(lines[i+1])):
            header=(i,cells); break
    if not header: raise ValueError("work-list Markdown table not found")
    i, heads=header; key={c.label:c.key for c in specs}
    unknown=[h for h in heads if h not in key]
    if unknown: raise ValueError(f"unknown Markdown columns: {unknown}")
    rows=[]
    for line in lines[i+2:]:
        if not line.lstrip().startswith("|"): break
        vals=md_cells(line)
        if not any(vals): continue
        vals += [""]*(len(heads)-len(vals)); rows.append(norm({key[h]:vals[j].replace("<br>","\n") for j,h in enumerate(heads)}, specs))
    validate(rows,specs); return rows

def md_escape(v): return str(v or "").replace("\\","\\\\").replace("|","\\|").replace("\n","<br>")

def render_md(rows,specs):
    labels=[c.label for c in specs]
    body=["| "+" | ".join(md_escape(r.get(c.key,"")) for c in specs)+" |" for r in rows]
    return "\n".join(["# 전체 작업 목록","","> 이 파일은 `전체작업목록.xlsx`와 동일한 Canonical Work Item의 사용자 View다. 담당자/일정/공수는 선택 입력이다.","","```mermaid","flowchart LR",'    P["프로젝트"] --> M["마일스톤"]','    M --> R["요구사항"]','    R --> F["세부기능"]','    F --> G["프로그램"]','    G --> T["작업"]','    T --> V["완료기준/테스트"]',"```","","| "+" | ".join(labels)+" |","|"+"|".join("---" for _ in labels)+"|",*body,""])

def write_md(path,rows,specs): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(render_md(rows,specs),encoding="utf-8")

def colname(n):
    s=""
    while n: n,r=divmod(n-1,26); s=chr(65+r)+s
    return s

def colnum(ref):
    s=re.match(r"[A-Z]+",ref).group(); n=0
    for ch in s: n=n*26+ord(ch)-64
    return n

def cell(ref,v,style=0):
    st=f' s="{style}"' if style else ""
    if v in (None,""): return f'<c r="{ref}"{st} t="inlineStr"><is><t></t></is></c>'
    if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(float(v)): return f'<c r="{ref}"{st}><v>{v}</v></c>'
    t=escape(str(v)); return f'<c r="{ref}"{st} t="inlineStr"><is><t>{t}</t></is></c>'

def sheet_xml(rows,specs):
    cols="".join(f'<col min="{i}" max="{i}" width="{min(max(len(c.label)*2+2,12),32)}" customWidth="1"/>' for i,c in enumerate(specs,1))
    data=['<row r="1" ht="24" customHeight="1">'+"".join(cell(f"{colname(i)}1",c.label,1) for i,c in enumerate(specs,1))+"</row>"]
    for r,row in enumerate(rows,2): data.append(f'<row r="{r}">'+"".join(cell(f"{colname(i)}{r}",row.get(c.key,"")) for i,c in enumerate(specs,1))+"</row>")
    return f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><worksheet xmlns="{MAIN}"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols>{cols}</cols><sheetData>{''.join(data)}</sheetData><autoFilter ref="A1:{colname(len(specs))}{max(1,len(rows)+1)}"/></worksheet>'''

CONTENT='''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>'''
ROOTREL='''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'''
WORKBOOK=f'''<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{MAIN}" xmlns:r="{REL}"><sheets><sheet name="{SHEET}" sheetId="1" r:id="rId1"/></sheets></workbook>'''
WBRELS='''<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'''
STYLES=f'''<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="{MAIN}"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill><fill><patternFill patternType="solid"><fgColor rgb="FF1F4E78"/></patternFill></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"><alignment horizontal="center" vertical="center" wrapText="1"/></xf></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'''

def write_xlsx(path,rows,specs):
    path.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path,"w",zipfile.ZIP_DEFLATED) as z:
        for n,v in {"[Content_Types].xml":CONTENT,"_rels/.rels":ROOTREL,"xl/workbook.xml":WORKBOOK,"xl/_rels/workbook.xml.rels":WBRELS,"xl/styles.xml":STYLES,"xl/worksheets/sheet1.xml":sheet_xml(rows,specs)}.items(): z.writestr(n,v)

def cell_value(c,shared):
    typ=c.attrib.get("t")
    if typ=="inlineStr": return "".join(x.text or "" for x in c.iter(f"{{{MAIN}}}t"))
    v=c.find(f"{{{MAIN}}}v"); raw="" if v is None or v.text is None else v.text
    if typ=="s": return shared[int(raw)] if raw else ""
    if raw=="": return ""
    try: n=float(raw); return int(n) if n.is_integer() else n
    except ValueError: return raw

def read_xlsx(path,specs):
    with zipfile.ZipFile(path) as z:
        shared=[]
        if "xl/sharedStrings.xml" in z.namelist():
            root=ET.fromstring(z.read("xl/sharedStrings.xml")); shared=["".join(t.text or "" for t in si.iter(f"{{{MAIN}}}t")) for si in root.findall(f"{{{MAIN}}}si")]
        wb=ET.fromstring(z.read("xl/workbook.xml")); rid=wb.find(f".//{{{MAIN}}}sheet").attrib[f"{{{REL}}}id"]
        rels=ET.fromstring(z.read("xl/_rels/workbook.xml.rels")); target=next(r.attrib["Target"] for r in rels.findall(f"{{{PKGREL}}}Relationship") if r.attrib.get("Id")==rid); target=target.lstrip("/"); target=target if target.startswith("xl/") else "xl/"+target
        root=ET.fromstring(z.read(target)); matrix=[]
        for row in root.findall(f".//{{{MAIN}}}row"):
            vals={colnum(c.attrib.get("r","A1")):cell_value(c,shared) for c in row.findall(f"{{{MAIN}}}c")}; matrix.append([vals.get(i,"") for i in range(1,max(vals,default=0)+1)])
    if not matrix: return []
    heads=[str(x) for x in matrix[0]]; mapping={c.label:c.key for c in specs}; unknown=[x for x in heads if x and x not in mapping]
    if unknown: raise ValueError(f"unknown Excel columns: {unknown}")
    rows=[]
    for row in matrix[1:]:
        if not any(x!="" for x in row): continue
        rows.append(norm({mapping[h]:(row[i] if i<len(row) else "") for i,h in enumerate(heads) if h in mapping},specs))
    validate(rows,specs); return rows

def canonical(path):
    if not path.exists(): return {"schema_version":1,"updated_at":now(),"items":{},"conflicts":[]}
    d=json.loads(path.read_text(encoding="utf-8")); d.setdefault("items",{}); d.setdefault("conflicts",[]); return d

def save(path,data): path.parent.mkdir(parents=True,exist_ok=True); data["updated_at"]=now(); path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def meaningful(r,specs): return {c.key:r.get(c.key,"") for c in specs if c.key not in GENERATED}

def merge(data,incoming,specs,source):
    conflicts=[]; items=data.setdefault("items",{})
    for raw in incoming:
        r=norm(raw,specs); wid=str(r["work_item_id"]); cur=items.get(wid)
        if cur is None:
            r["revision"]=int(r.get("revision") or 1); r["updated_at"]=r.get("updated_at") or now(); items[wid]=r; continue
        cur=norm(cur,specs)
        if meaningful(cur,specs)==meaningful(r,specs): continue
        cr,ir=int(cur.get("revision") or 0),int(r.get("revision") or 0); ct,it=str(cur.get("updated_at") or ""),str(r.get("updated_at") or "")
        if ir==cr and it==ct: r["revision"]=cr+1; r["updated_at"]=now(); items[wid]=r; continue
        if ir>cr: r["updated_at"]=r.get("updated_at") or now(); items[wid]=r; continue
        c={"type":"SYNC_CONFLICT","work_item_id":wid,"source":source,"detected_at":now(),"canonical_revision":cr,"incoming_revision":ir,"canonical_updated_at":ct,"incoming_updated_at":it,"canonical":cur,"incoming":r}; conflicts.append(c); data["conflicts"].append(c)
    return conflicts

def rows(data,specs): return [norm(data["items"][k],specs) for k in sorted(data.get("items",{}))]
def conflict_log(path,items):
    if not items: return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as f:
        for x in items: f.write(json.dumps(x,ensure_ascii=False)+"\n")

def main(argv=None):
    p=argparse.ArgumentParser(); sub=p.add_subparsers(dest="cmd",required=True)
    def common(x): x.add_argument("--config",default="sdlc/config/worklist-columns.yaml"); x.add_argument("--md",default="docs/00_관리/전체작업목록.md"); x.add_argument("--xlsx",default="docs/00_관리/전체작업목록.xlsx")
    a=sub.add_parser("md-to-xlsx"); common(a); b=sub.add_parser("xlsx-to-md"); common(b); s=sub.add_parser("sync"); common(s); s.add_argument("--source",choices=["md","xlsx"],required=True); s.add_argument("--canonical",default="sdlc/canonical/work-items.json"); s.add_argument("--conflicts",default="sdlc/runtime/sync-conflicts.jsonl"); s.add_argument("--strict",action="store_true")
    x=p.parse_args(argv); specs=columns(Path(x.config))
    if x.cmd=="md-to-xlsx": incoming=read_md(Path(x.md),specs); write_xlsx(Path(x.xlsx),incoming,specs); return 0
    if x.cmd=="xlsx-to-md": incoming=read_xlsx(Path(x.xlsx),specs); write_md(Path(x.md),incoming,specs); return 0
    incoming=read_md(Path(x.md),specs) if x.source=="md" else read_xlsx(Path(x.xlsx),specs); data=canonical(Path(x.canonical)); conflicts=merge(data,incoming,specs,x.source); save(Path(x.canonical),data); conflict_log(Path(x.conflicts),conflicts)
    if conflicts:
        print(f"SYNC_CONFLICT: {len(conflicts)} item(s) recorded; views were not overwritten.",file=sys.stderr); return 2 if x.strict else 0
    current=rows(data,specs); write_md(Path(x.md),current,specs); write_xlsx(Path(x.xlsx),current,specs); return 0

if __name__=="__main__": raise SystemExit(main())
