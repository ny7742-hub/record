# -*- coding: utf-8 -*-
"""아난티 4매장 거래명세서 원본 → 내장 템플릿(base64)으로 가공.
   - 공유수식(shared formula)을 행마다 풀어 쓴 수식으로 바꾼다(행을 늘리고 줄여도 안 깨지게)
   - 샘플 품목 값·캐시값을 지운다
   - 품목행을 10~49(40줄)로 넓히고 총합계를 50행으로 옮긴다(병합·수식·인쇄영역 같이)
   - 노란 음영(FFFFFF00) 제거, calcChain 제거
"""
import zipfile, re, io, sys, base64, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
# 아난티가 보낸 원본 명세서 폴더 — 새 원본이 오면 SRC의 파일명·총합계 행 번호도 맞게 고칠 것
D = r"C:\Users\user\Documents\카카오톡 받은 파일"
# 결과(매장별 _tpl.xlsx와 tpl_b64.json)는 이 스크립트 옆 an_tpl_out/ 에 만든다.
# tpl_b64.json의 값을 index.html의 AN_TPLS[매장].b64에 붙여넣으면 된다.
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "an_tpl_out")
import os
os.makedirs(OUT, exist_ok=True)

SRC = {
 "ANC": ("리테일 거래명세서_위탁(아난티 코브_살롱)_화이트샌즈260820.xlsx", 39),
 "ANV": ("리테일 거래명세서_위탁(빌라쥬 드 아난티_살롱)_화이트샌즈260714_2.xlsx", 36),
 "ANG": ("리테일 거래명세서_위탁(아난티 코드_살롱)_화이트샌즈260722.xlsx", 26),
 "ANT": ("아난티 남해 거래명세서_260820.xlsx", 30),
}
FIRST = 10
NEW_LAST = 49
NEW_TOTAL = 50
# 샘플 값을 지울 열 (수식이 아닌 칸은 전부 값 삭제)

def col_num(c):
    n = 0
    for ch in c: n = n * 26 + (ord(ch) - 64)
    return n

REF = re.compile(r'(?<![A-Za-z_$])(\$?)([A-Z]{1,3})(\$?)(\d+)(?![\d(])')

def shift_formula(f, off):
    """행 상대참조만 off만큼 옮긴다($행은 그대로). 문자열 리터럴 안은 건드리지 않는다."""
    parts = re.split(r'("[^"]*")', f)
    out = []
    for p in parts:
        if p.startswith('"'):
            out.append(p); continue
        out.append(REF.sub(lambda m: m.group(1) + m.group(2) + m.group(3) + (m.group(4) if m.group(3) else str(int(m.group(4)) + off)), p))
    return "".join(out)

def set_row_formula_rows(f, old, new):
    """같은 행 참조(old행) → new행 (절대참조 제외)"""
    parts = re.split(r'("[^"]*")', f)
    out = []
    for p in parts:
        if p.startswith('"'):
            out.append(p); continue
        out.append(REF.sub(lambda m: m.group(0) if (m.group(3) or int(m.group(4)) != old) else m.group(1) + m.group(2) + str(new), p))
    return "".join(out)

def cells_of(rx):
    return re.findall(r'<c r="[A-Z]+\d+"[^>]*?/>|<c r="[A-Z]+\d+"[^>]*?>.*?</c>', rx, re.S)

def cell_col(c):
    return re.match(r'<c r="([A-Z]+)', c).group(1)

def cell_attrs(c):
    return re.match(r'<c r="[A-Z]+\d+"([^>]*?)/?>', c).group(1)

def build(code):
    fn, total = SRC[code]
    zin = zipfile.ZipFile(os.path.join(D, fn))
    files = {n: zin.read(n) for n in zin.namelist()}
    order = zin.namelist()
    sheet_name = [n for n in order if re.match(r"xl/worksheets/sheet\d+\.xml$", n)][0]
    x = files[sheet_name].decode("utf-8")
    last = total - 1

    # ── 1) 공유수식 풀기: master 수식 텍스트를 si별로 모아 두고, 각 셀에 행 차이만큼 옮긴 수식을 쓴다
    masters = {}
    for m in re.finditer(r'<c r="([A-Z]+)(\d+)"[^>]*>\s*<f t="shared" ref="[^"]*" si="(\d+)">(.*?)</f>', x, re.S):
        masters[m.group(3)] = (int(m.group(2)), m.group(4))
    def unshare(m):
        rown = int(m.group(1)); si = m.group(3)
        base_row, text = masters[si]
        return "<f>" + shift_formula(text, rown - base_row) + "</f>"
    x = re.sub(r'(?<=<c r=")([A-Z]+\d+)', lambda m: m.group(1), x)  # noop anchor
    def unshare_cell(cm):
        c = cm.group(0)
        rown = int(re.match(r'<c r="[A-Z]+(\d+)"', c).group(1))
        fm = re.search(r'<f t="shared"(?: ref="[^"]*")? si="(\d+)"\s*(?:/>|>(.*?)</f>)', c, re.S)
        if not fm: return c
        base_row, text = masters[fm.group(1)]
        return c[:fm.start()] + "<f>" + shift_formula(text, rown - base_row) + "</f>" + c[fm.end():]
    # 자체닫힘 셀(<c .../>)은 건너뛴다 — 안 그러면 다음 셀까지 삼켜 행 번호를 잘못 읽는다
    x = re.sub(r'<c r="[A-Z]+\d+"[^>]*?(?<!/)>.*?</c>', unshare_cell, x, flags=re.S)
    assert 't="shared"' not in x, code

    # ── 2) 행 분해
    sd = re.search(r"<sheetData>(.*?)</sheetData>", x, re.S)
    rows = re.findall(r'<row [^>]*?/>|<row [^>]*?>.*?</row>', sd.group(1), re.S)
    by = {}
    for rx in rows:
        by[int(re.search(r'\br="(\d+)"', rx).group(1))] = rx

    def clear_row(rx, keep_formula=True):
        """값·캐시·타입 지우기(수식은 남김). 서식(s)만 남긴다."""
        out = []
        for c in cells_of(rx):
            ref = re.match(r'<c r="([A-Z]+\d+)"', c).group(1)
            s = re.search(r'\ss="(\d+)"', cell_attrs(c))
            sattr = (' s="%s"' % s.group(1)) if s else ""
            f = re.search(r"<f>(.*?)</f>", c, re.S)
            if f and keep_formula:
                out.append('<c r="%s"%s><f>%s</f></c>' % (ref, sattr, f.group(1)))
            else:
                out.append('<c r="%s"%s/>' % (ref, sattr))
        head = re.match(r"<row [^>]*?>", rx).group(0) if not rx.endswith("/>") else rx[:-2] + ">"
        return head + "".join(out) + "</row>"

    def renumber(rx, old, new):
        rx = re.sub(r'(<row [^>]*?\br=")%d(")' % old, r"\g<1>%d\2" % new, rx)
        rx = re.sub(r'(<c r="[A-Z]+)%d(")' % old, r"\g<1>%d\2" % new, rx)
        rx = re.sub(r"<f>(.*?)</f>", lambda m: "<f>" + set_row_formula_rows(m.group(1), old, new) + "</f>", rx, flags=re.S)
        return rx

    p_first = clear_row(by[FIRST])
    p_mid = clear_row(by[FIRST + 1])
    p_last = clear_row(by[last])
    # 첫 줄 수식이 기준 — 가운데·마지막 줄에 수식이 빠진 열이 있으면 첫 줄 것을 채운다
    fcols = {cell_col(c): re.search(r"<f>(.*?)</f>", c, re.S).group(1) for c in cells_of(p_first) if "<f>" in c}
    def ensure_formulas(rx, rown):
        cs = cells_of(rx)
        have = {cell_col(c) for c in cs if "<f>" in c}
        out = []
        for c in cs:
            col = cell_col(c)
            if col in fcols and col not in have:
                s = re.search(r'\ss="(\d+)"', cell_attrs(c))
                sattr = (' s="%s"' % s.group(1)) if s else ""
                c = '<c r="%s%d"%s><f>%s</f></c>' % (col, rown, sattr, set_row_formula_rows(fcols[col], FIRST, rown))
            out.append(c)
        head = re.match(r"<row [^>]*?>", rx).group(0)
        return head + "".join(out) + "</row>"

    new_items = {}
    for r in range(FIRST, NEW_LAST + 1):
        if r == FIRST:
            rx = p_first
        elif r == NEW_LAST:
            rx = renumber(p_last, last, r)
        else:
            rx = renumber(p_mid, FIRST + 1, r)
        rx = ensure_formulas(rx, r)
        # 마지막 줄만 thickBot 유지
        if r != NEW_LAST:
            rx = re.sub(r'\sthickBot="1"', "", rx, count=1)
        new_items[r] = rx

    # 총합계 행
    tot = by[total]
    tot = renumber(tot, total, NEW_TOTAL)
    tot = re.sub(r"<f>(.*?)</f>", lambda m: "<f>" + re.sub(r"([A-Z]+)%d:([A-Z]+)%d(?!\d)" % (FIRST, last), r"\g<1>%d:\g<2>%d" % (FIRST, NEW_LAST), m.group(1)) + "</f>", tot, flags=re.S)
    tot = re.sub(r"(<f>.*?</f>)\s*<v>.*?</v>", r"\1", tot, flags=re.S)

    nb = {k: v for k, v in by.items() if k < FIRST}
    nb.update(new_items)
    nb[NEW_TOTAL] = tot
    # 총합계 아래 빈 서식 행(원본 40~48행 등)은 버린다 — 남기면 PDF 아래에 빈 공간이 생긴다
    for k, v in by.items():
        if k > total:
            assert "<v>" not in v and "<f>" not in v, (code, k)
    # 위쪽(1~9행) 수식에서 총합계 행 참조 옮기기 + C3 샘플 날짜 지우기
    for k in list(nb):
        if k < FIRST:
            nb[k] = re.sub(r"<f>(.*?)</f>", lambda m: "<f>" + re.sub(r"([A-Z]{1,3})%d(?!\d)" % total, r"\g<1>%d" % NEW_TOTAL, m.group(1)) + "</f>", nb[k], flags=re.S)
    nb[3] = re.sub(r'(<c r="C3"[^>]*?)>\s*<v>[^<]*</v>\s*</c>', r"\1/>", nb[3])
    new_sd = "<sheetData>" + "".join(nb[k] for k in sorted(nb)) + "</sheetData>"
    x = x[:sd.start()] + new_sd + x[sd.end():]

    # ── 3) 병합: 품목행(10~last) 병합은 10행 패턴으로 다시 만들고, 총합계 행은 옮긴다
    mc = re.search(r'<mergeCells count="\d+">(.*?)</mergeCells>', x, re.S)
    refs = re.findall(r'<mergeCell ref="([^"]+)"/>', mc.group(1))
    keep, pattern = [], []
    for ref in refs:
        m = re.match(r"([A-Z]+)(\d+):([A-Z]+)(\d+)$", ref)
        if not m:
            keep.append(ref); continue
        r1, r2 = int(m.group(2)), int(m.group(4))
        if FIRST <= r1 <= last and r1 == r2:
            if r1 == FIRST: pattern.append((m.group(1), m.group(3)))
            continue
        if r1 == total and r2 == total:
            keep.append("%s%d:%s%d" % (m.group(1), NEW_TOTAL, m.group(3), NEW_TOTAL)); continue
        if r1 >= FIRST:
            raise Exception("unexpected merge %s" % ref)
        keep.append(ref)
    for r in range(FIRST, NEW_LAST + 1):
        for a, b in pattern:
            keep.append("%s%d:%s%d" % (a, r, b, r))
    x = x[:mc.start()] + '<mergeCells count="%d">' % len(keep) + "".join('<mergeCell ref="%s"/>' % r for r in keep) + "</mergeCells>" + x[mc.end():]
    x = re.sub(r'(<dimension ref="[A-Z]+\d+:[A-Z]+)(\d+)(")', lambda m: m.group(1) + str(NEW_TOTAL) + m.group(3), x)
    files[sheet_name] = x.encode("utf-8")

    # ── 4) 인쇄영역·필터 범위
    wb = files["xl/workbook.xml"].decode("utf-8")
    wb = re.sub(r"(_xlnm\.(?:Print_Area|_FilterDatabase)\"[^>]*>[^<]*?\$[A-Z]+\$)(\d+)(<)", lambda m: m.group(1) + (str(NEW_TOTAL) if int(m.group(2)) == total else m.group(2)) + m.group(3), wb)
    files["xl/workbook.xml"] = wb.encode("utf-8")

    # ── 5) 노란 음영 제거
    st = files["xl/styles.xml"].decode("utf-8")
    st = re.sub(r'<fill><patternFill patternType="solid"><fgColor rgb="FFFFFF00"/><bgColor indexed="64"/></patternFill></fill>',
                '<fill><patternFill patternType="none"/></fill>', st)
    files["xl/styles.xml"] = st.encode("utf-8")

    # ── 6) calcChain 제거(행이 바뀌어 맞지 않는다)
    drop = [n for n in order if n.lower() == "xl/calcchain.xml"]
    for n in drop:
        del files[n]
    ct = files["[Content_Types].xml"].decode("utf-8")
    ct = re.sub(r'<Override PartName="/xl/calcChain\.xml"[^>]*/>', "", ct)
    files["[Content_Types].xml"] = ct.encode("utf-8")
    rel = "xl/_rels/workbook.xml.rels"
    rr = files[rel].decode("utf-8")
    rr = re.sub(r'<Relationship [^>]*Target="calcChain\.xml"[^>]*/>', "", rr)
    files[rel] = rr.encode("utf-8")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in order:
            if n in files:
                zo.writestr(n, files[n])
    data = buf.getvalue()
    open(os.path.join(OUT, code + "_tpl.xlsx"), "wb").write(data)
    return data, sheet_name

res = {}
for code in SRC:
    data, sn = build(code)
    res[code] = base64.b64encode(data).decode("ascii")
    print(code, sn, len(data), "bytes")
json.dump(res, open(os.path.join(OUT, "tpl_b64.json"), "w"))
print("ok")
