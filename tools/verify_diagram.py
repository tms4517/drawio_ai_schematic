#!/usr/bin/env python3
"""Verify an RTL-Whiteboard .drawio against the drawing conventions.

Usage:  python3 tools/verify_diagram.py <diagram.drawio>

Reads the diagram, classifies its cells (shapes, wires, net names, ports,
captions, containers), runs every convention check, and prints a PASS/FAIL log
with the offending coordinates. Exit code is 0 only when every check passes, so
the log can be fed back to the LLM to improve the diagram.

Checks (mirror tools/verifyDiagram.md + conventions.md):
  1  Net names do not overlap each other
  2  Net names are inside the module boundary
  3  Net names are not within shapes
  4  Shapes are connected (no floating shape)
  5  Inputs start / outputs end on the module boundary
  6  Wires never pass through a shape or text
  7  An arrowhead and a junction circle are never directly connected
  8  Net labels sit a uniform gap above their net
  9  Wires are orthogonal (no diagonal segments)
 10  No two net segments lie stacked on top of each other
 23  A net name is never crossed by a wire
 24  Edge-label net names float over a horizontal segment, not a vertical one
 25  A module instanced N>1 times is drawn as a deck of cards
 26  Module inputs enter on the left edge, outputs exit on the right edge
 27  No stray descriptive caption inside a module
"""
import sys, re, html, base64, zlib, urllib.parse, statistics, math
import xml.etree.ElementTree as ET

TOL = 3.0           # endpoint / boundary snapping
SHAPE_INSET = 2.0   # shrink shapes so boundary-touching endpoints are allowed
TEXT_INSET = 1.0
GAP_MAX = 30.0      # how far below a label we look for its wire
GAP_UNIFORM = 3.0   # allowed spread of label->wire gaps
DECO_MAX = 14.0     # glyphs this small (clock notch, junction) are not shapes
PORT_TOKENS = {"D", "Q", "T", "EN", "ARST", "SRST", "CLK", "A", "B", "R", "S", "J", "K",
               "A > B", "A < B", "A == B", ">", "<", "=", "+", "-", "*"}


# ===================== parsing =====================
def load_model(path):
    root = ET.fromstring(open(path, encoding="utf-8").read())
    if root.tag == "mxGraphModel":
        return root
    diagram = root.find(".//diagram")
    if diagram is None:
        raise SystemExit("no <diagram> found")
    inner = diagram.find("mxGraphModel")
    if inner is not None:
        return inner
    data = base64.b64decode((diagram.text or "").strip())
    return ET.fromstring(urllib.parse.unquote(zlib.decompress(data, -15).decode("utf-8")))


def strip(v):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(v or ""))).strip()


class Cell:
    __slots__ = ("id", "style", "value", "rawval", "edge", "x", "y", "w", "h", "pts",
                 "src", "tgt", "sp", "tp", "mids")


def parse(model):
    cells = {}
    for c in model.iter("mxCell"):
        o = Cell()
        o.id = c.get("id"); o.style = c.get("style") or ""
        o.value = strip(c.get("value")); o.rawval = c.get("value") or ""
        o.edge = c.get("edge") == "1"
        o.src = c.get("source"); o.tgt = c.get("target")
        o.x = o.y = o.w = o.h = None; o.pts = []; o.sp = o.tp = None; o.mids = []
        g = c.find("mxGeometry")
        if g is not None:
            if not o.edge and g.get("x") is not None and g.get("y") is not None:
                o.x = float(g.get("x")); o.y = float(g.get("y"))
                o.w = float(g.get("width") or 0); o.h = float(g.get("height") or 0)
            for p in g.findall("mxPoint"):
                xy = (float(p.get("x") or 0), float(p.get("y") or 0))
                if p.get("as") == "sourcePoint": o.sp = xy
                elif p.get("as") == "targetPoint": o.tp = xy
            arr = g.find("Array")
            if arr is not None:
                o.mids = [(float(p.get("x") or 0), float(p.get("y") or 0)) for p in arr.findall("mxPoint")]
        cells[o.id] = o

    # resolve each edge's polyline (prefer the connected shape's exit/entry point)
    def frac(style, a):
        m = re.search(rf"\b{a}=([-\d.]+)", style)
        return float(m.group(1)) if m else None
    cc = lambda s: (s.x + s.w / 2, s.y + s.h / 2)
    for o in cells.values():
        if not o.edge:
            continue
        start, end = o.sp, o.tp
        s = cells.get(o.src) if o.src else None
        if s is not None and s.x is not None:
            fx, fy = frac(o.style, "exitX"), frac(o.style, "exitY")
            start = (s.x + fx * s.w, s.y + fy * s.h) if fx is not None and fy is not None else (start or cc(s))
        t = cells.get(o.tgt) if o.tgt else None
        if t is not None and t.x is not None:
            fx, fy = frac(o.style, "entryX"), frac(o.style, "entryY")
            end = (t.x + fx * t.w, t.y + fy * t.h) if fx is not None and fy is not None else (end or cc(t))
        o.pts = ([start] if start else []) + o.mids + ([end] if end else [])
    return cells


# ===================== geometry helpers =====================
def bbox(c): return (c.x, c.y, c.x + c.w, c.y + c.h)
def center(c): return (c.x + c.w / 2, c.y + c.h / 2)

def overlap(a, b, inset=0.0):
    return not (a[2] <= b[0] + inset or a[0] >= b[2] - inset or
                a[3] <= b[1] + inset or a[1] >= b[3] - inset)

def inside(a, outer, tol=TOL):
    return (a[0] >= outer[0] - tol and a[1] >= outer[1] - tol and
            a[2] <= outer[2] + tol and a[3] <= outer[3] + tol)

def pt_in(p, b, inset=0.0):
    return b[0] + inset <= p[0] <= b[2] - inset and b[1] + inset <= p[1] <= b[3] - inset

def seg_hits_rect(x1, y1, x2, y2, b, inset):
    bx0, by0, bx1, by1 = b[0] + inset, b[1] + inset, b[2] - inset, b[3] - inset
    if bx0 >= bx1 or by0 >= by1:
        return False
    if abs(y1 - y2) < 1e-6:
        lo, hi = sorted((x1, x2)); return by0 <= y1 <= by1 and lo < bx1 and hi > bx0
    if abs(x1 - x2) < 1e-6:
        lo, hi = sorted((y1, y2)); return bx0 <= x1 <= bx1 and lo < by1 and hi > by0
    return False

def near_perim(p, b, tol=TOL):
    on_x = (abs(p[0] - b[0]) <= tol or abs(p[0] - b[2]) <= tol) and b[1] - tol <= p[1] <= b[3] + tol
    on_y = (abs(p[1] - b[1]) <= tol or abs(p[1] - b[3]) <= tol) and b[0] - tol <= p[0] <= b[2] + tol
    return on_x or on_y


# ===================== style helpers =====================
def sattr(style, key):
    m = re.search(rf"\b{key}=([^;]+)", style)
    return m.group(1).strip() if m else None

def is_monospace(style, raw):
    fam = sattr(style, "fontFamily")
    if fam is not None:
        return "mono" in fam.lower()
    m = re.search(r'face="([^"]*)"', raw or "", re.I) or re.search(r"font-family:\s*([^;\"']+)", raw or "", re.I)
    return "mono" in m.group(1).lower() if m else False

def is_black(style, raw):
    fc = sattr(style, "fontColor")
    if fc and fc.lower() not in ("#000000", "#000", "black"):
        return False
    m = re.search(r"(?<!background-)color:\s*(#[0-9a-fA-F]{3,6})", raw or "")
    return not (m and m.group(1).lower() not in ("#000000", "#000"))

def luminance(hexs):
    hexs = hexs.lstrip("#")
    if len(hexs) == 3:
        hexs = "".join(ch * 2 for ch in hexs)
    try:
        r, g, b = int(hexs[0:2], 16), int(hexs[2:4], 16), int(hexs[4:6], 16)
    except ValueError:
        return 1.0
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255

def edge_below(label, edges):
    cx = label.x + label.w / 2
    lb = label.y + label.h
    best, bg = None, None
    for e in edges:
        for (x1, y1), (x2, y2) in zip(e.pts, e.pts[1:]):
            if abs(y1 - y2) < 1e-6 and min(x1, x2) - 2 <= cx <= max(x1, x2) + 2:
                if y1 >= lb - 1 and y1 - lb <= GAP_MAX and (bg is None or y1 - lb < bg):
                    bg, best = y1 - lb, e
    return best


# ===================== classification =====================
def classify(cells):
    verts = [c for c in cells.values() if c.id not in ("0", "1") and not c.edge and c.x is not None]
    edges = [c for c in cells.values() if c.edge and len(c.pts) >= 2]
    texts = [c for c in verts if c.style.startswith("text;")]
    nontext = [c for c in verts if not c.style.startswith("text;")]

    junctions = [c for c in nontext if "ellipse" in c.style and max(c.w, c.h) <= DECO_MAX]
    decorations = [c for c in nontext if c not in junctions and
                   ("triangle" in c.style or max(c.w, c.h) <= DECO_MAX)]
    significant = [c for c in nontext if c not in junctions and c not in decorations]

    def is_container(c):
        bb = bbox(c)
        return any(o is not c and pt_in(center(o), bb) for o in significant)
    containers = [c for c in significant if is_container(c)]
    shapes = [c for c in significant if c not in containers]      # FF / gate / sync box
    module = max(containers, key=lambda c: c.w * c.h) if containers else None

    shape_boxes = [bbox(s) for s in shapes]
    ports = [t for t in texts if any(pt_in(center(t), b) for b in shape_boxes) or t.value in PORT_TOKENS]
    labels = [t for t in texts if t not in ports]

    def is_caption(l):                                            # a shape sits just above it
        lb = bbox(l)
        for s in shapes:
            sb = bbox(s)
            if sb[0] - 4 <= center(l)[0] <= sb[2] + 4 and 0 <= lb[1] - sb[3] <= 14:
                return True
        return False
    captions = [l for l in labels if is_caption(l)]
    netlabels = [l for l in labels if l not in captions]

    return dict(edges=edges, junctions=junctions, shapes=shapes, module=module,
                containers=containers, ports=ports, labels=labels, captions=captions,
                netlabels=netlabels)


def wire_below(label, edges):
    cx = label.x + label.w / 2
    lb = label.y + label.h
    best = None
    for e in edges:
        for (x1, y1), (x2, y2) in zip(e.pts, e.pts[1:]):
            if abs(y1 - y2) < 1e-6 and min(x1, x2) - 2 <= cx <= max(x1, x2) + 2:
                if y1 >= lb - 1 and y1 - lb <= GAP_MAX:
                    g = y1 - (label.y + label.h / 2)
                    best = g if best is None else min(best, g)
    return best


# ===================== checks =====================
class Log:
    def __init__(self): self.fail = 0; self.total = 0
    def check(self, ok, n, desc, details=()):
        self.total += 1
        print(f"[{'PASS' if ok else 'FAIL'}] {n:>2}. {desc}")
        if not ok:
            self.fail += 1
            for d in details:
                print(f"         - {d}")


def run(path):
    model = load_model(path)
    cells = parse(model)
    c = classify(cells)
    log = Log()
    shapes, edges, junc = c["shapes"], c["edges"], c["junctions"]
    netlabels, mod = c["netlabels"], c["module"]

    print(f"Diagram: {path}")
    print(f"Classified: {len(shapes)} shapes, {len(junc)} junctions, {len(edges)} wires, "
          f"{len(netlabels)} net names, {len(c['captions'])} captions, {len(c['ports'])} ports")
    if mod is None:
        print("[FAIL]  0. No module boundary found — cannot verify.")
        return 1
    mb = bbox(mod)
    print(f"Module boundary: {mod.value or '(unnamed)'} {tuple(round(v) for v in mb)}\n")

    # 1
    bad = [f"'{a.value}' overlaps '{b.value}'"
           for i, a in enumerate(netlabels) for b in netlabels[i + 1:] if overlap(bbox(a), bbox(b))]
    log.check(not bad, 1, "Net names do not overlap each other", bad)

    # 2
    bad = [f"'{l.value}' at {tuple(round(v) for v in bbox(l))}" for l in netlabels if not inside(bbox(l), mb)]
    log.check(not bad, 2, "Net names are inside the module boundary", bad)

    # 3
    bad = [f"'{l.value}' overlaps shape {tuple(round(v) for v in bbox(s))}"
           for l in netlabels for s in shapes if overlap(bbox(l), bbox(s))]
    log.check(not bad, 3, "Net names are not within shapes", bad)

    # 4
    allpts = [p for e in edges for p in e.pts]
    bad = [f"shape '{s.value or '(unnamed)'}' {tuple(round(v) for v in bbox(s))} has no wire"
           for s in shapes if not any(near_perim(p, bbox(s)) or pt_in(p, bbox(s)) for p in allpts)]
    log.check(not bad, 4, "Shapes are connected (no floating shape)", bad)

    # 5
    def on_shape(p): return any(near_perim(p, bbox(s)) or pt_in(p, bbox(s)) for s in shapes)
    def on_junc(p): return any(pt_in(p, bbox(j), -3) or near_perim(p, bbox(j), 4) for j in junc)
    def on_bound(p): return (abs(p[0] - mb[0]) <= TOL or abs(p[0] - mb[2]) <= TOL or
                             abs(p[1] - mb[1]) <= TOL or abs(p[1] - mb[3]) <= TOL)
    bad = [f"wire endpoint {tuple(round(v) for v in p)} not on a shape, junction or boundary"
           for e in edges for p in (e.pts[0], e.pts[-1])
           if not on_shape(p) and not on_junc(p) and not on_bound(p)]
    log.check(not bad, 5, "Inputs start / outputs end on the module boundary", bad)

    # 6
    txt = [(t.value, bbox(t)) for t in c["labels"] + c["ports"]]
    bad = []
    for e in edges:
        eps = {e.pts[0], e.pts[-1]}
        for (x1, y1), (x2, y2) in zip(e.pts, e.pts[1:]):
            for s in shapes:
                b = bbox(s)
                if ((x1, y1) in eps and near_perim((x1, y1), b)) or ((x2, y2) in eps and near_perim((x2, y2), b)):
                    continue
                if seg_hits_rect(x1, y1, x2, y2, b, SHAPE_INSET):
                    bad.append(f"wire ({x1:.0f},{y1:.0f})-({x2:.0f},{y2:.0f}) crosses shape '{s.value or '(unnamed)'}'")
            for name, b in txt:
                if seg_hits_rect(x1, y1, x2, y2, b, TEXT_INSET):
                    bad.append(f"wire ({x1:.0f},{y1:.0f})-({x2:.0f},{y2:.0f}) crosses text '{name}'")
    log.check(not bad, 6, "Wires never pass through a shape or text", bad)

    # 7
    bad = []
    for e in edges:
        if "endArrow=none" not in e.style:
            end = e.pts[-1]
            for j in junc:
                if pt_in(end, bbox(j), -3) or near_perim(end, bbox(j), 4):
                    bad.append(f"wire ends with an arrow on junction {tuple(round(v) for v in center(j))}")
    log.check(not bad, 7, "An arrowhead and a junction circle are never directly connected", bad)

    # 8
    gaps = {l.value: wire_below(l, edges) for l in netlabels if wire_below(l, edges) is not None}
    detail = [f"label '{l.value}' is not above any net" for l in netlabels if wire_below(l, edges) is None]
    if gaps:
        med = statistics.median(gaps.values())
        detail += [f"'{n}' gap {g:.0f}px (expected ~{med:.0f}px)" for n, g in gaps.items() if abs(g - med) > GAP_UNIFORM]
    log.check(not detail, 8, "Net labels sit a uniform gap above their net", detail)

    # 9  (only straight-routed edges can render a visible diagonal; orthogonal
    #     edges are auto-bent by Drawio, so a sub-pixel skew there is harmless)
    bad = []
    for e in edges:
        ortho = "orthogonalEdgeStyle" in e.style
        for (x1, y1), (x2, y2) in zip(e.pts, e.pts[1:]):
            if abs(x1 - x2) > 2 and abs(y1 - y2) > 2 and not ortho:
                bad.append(f"diagonal ({x1:.0f},{y1:.0f})-({x2:.0f},{y2:.0f}) on {e.id}")
    log.check(not bad, 9, "Wires are orthogonal (no diagonal segments)", bad)

    # 10
    segs = []
    for e in edges:
        for (x1, y1), (x2, y2) in zip(e.pts, e.pts[1:]):
            if abs(x1 - x2) < 1e-6: segs.append(("V", x1, min(y1, y2), max(y1, y2), e.id))
            elif abs(y1 - y2) < 1e-6: segs.append(("H", y1, min(x1, x2), max(x1, x2), e.id))
    bad = []
    for i, (o1, f1, lo1, hi1, w1) in enumerate(segs):
        for o2, f2, lo2, hi2, w2 in segs[i + 1:]:
            if o1 == o2 and w1 != w2 and abs(f1 - f2) <= 1 and min(hi1, hi2) - max(lo1, lo2) > 2:
                bad.append(f"{w1} and {w2} stacked {o1}@{f1:.0f}")
    log.check(not bad, 10, "No two net segments lie stacked on top of each other", bad)

    # ---- style / text / colour / paper conventions ----
    conts = c["containers"]
    syncs = [s for s in shapes if "rounded=1" in s.style]            # module-instance boxes
    prims = [s for s in shapes if s not in syncs]                    # FF rects + gates
    texted = [t for t in cells.values() if t.value and not t.edge and t.x is not None]

    # 11 monospace
    bad = [f"'{t.value}' is not Monospace" for t in texted if not is_monospace(t.style, t.rawval)]
    log.check(not bad, 11, "All text is Monospace", bad)

    # 12 black text
    bad = [f"'{t.value}' is not black" for t in texted if not is_black(t.style, t.rawval)]
    log.check(not bad, 12, "All text is black", bad)

    # 13 no legend / paragraph
    bad = [f"'{t.value[:50]}...'" for t in texted if len(t.value) > 50 or t.value.count(". ") >= 1]
    log.check(not bad, 13, "No legend or paragraph text", bad)

    # 14 net names 8px
    bad = [f"'{l.value}' fontSize={sattr(l.style, 'fontSize')}" for l in netlabels if sattr(l.style, "fontSize") != "8"]
    log.check(not bad, 14, "Net names are 8px", bad)

    # 15 single-bit nets have no [1]
    bad = [f"'{l.value}'" for l in netlabels if re.search(r"\[1\]$", l.value)]
    log.check(not bad, 15, "Single-bit nets have no [1] suffix", bad)

    # 16 buses drawn thick
    bad = []
    for l in netlabels:
        m = re.search(r"\[([^\]]+)\]$", l.value)
        if m and m.group(1) != "1":
            e = edge_below(l, edges)
            sw = sattr(e.style, "strokeWidth") if e else None
            if sw is None or float(sw) < 2:
                bad.append(f"bus '{l.value}' wire strokeWidth={sw} (need >=2)")
    log.check(not bad, 16, "Buses are drawn with strokeWidth>=2", bad)

    # 17 transparent net labels
    bad = [f"'{l.value}' labelBackgroundColor={sattr(l.style, 'labelBackgroundColor')}"
           for l in netlabels if sattr(l.style, "labelBackgroundColor") != "none"]
    log.check(not bad, 17, "Net labels have a transparent background", bad)

    # 18 primitives white fill / black border
    bad = []
    for s in prims:
        fc, st = sattr(s.style, "fillColor"), sattr(s.style, "strokeColor")
        if fc and fc.lower() not in ("#ffffff", "#fff", "white", "none"):
            bad.append(f"primitive {tuple(round(v) for v in bbox(s))} fill {fc}")
        if st and st.lower() not in ("#000000", "#000", "black"):
            bad.append(f"primitive {tuple(round(v) for v in bbox(s))} stroke {st}")
    log.check(not bad, 18, "Primitives have a white fill and black border", bad)

    # 19 containers rounded (arcSize=5); CDC domains borderless
    bad = []
    for cont in conts:
        if "rounded=1" not in cont.style:
            bad.append(f"container '{cont.value}' is not a rounded rectangle")
        elif sattr(cont.style, "arcSize") != "5":
            bad.append(f"container '{cont.value}' arcSize={sattr(cont.style, 'arcSize')} (need 5)")
        if cont is not mod and sattr(cont.style, "strokeColor") != "none":
            bad.append(f"CDC domain '{cont.value}' has a border (should be borderless)")
    log.check(not bad, 19, "Containers are rounded (arcSize=5); CDC domains borderless", bad)

    # 20 module/instance names top-right, 10px
    bad = []
    for n in conts + syncs:
        if not n.value:
            continue
        if sattr(n.style, "align") != "right":
            bad.append(f"'{n.value}' is not right-aligned")
        if sattr(n.style, "verticalAlign") != "top":
            bad.append(f"'{n.value}' is not top-aligned")
        if sattr(n.style, "fontSize") != "10":
            bad.append(f"'{n.value}' fontSize={sattr(n.style, 'fontSize')} (need 10)")
    log.check(not bad, 20, "Module / instance names are top-right, 10px", bad)

    # 21 light backgrounds
    bad = [f"'{s.value or '(unnamed)'}' dark fill {sattr(s.style, 'fillColor')}"
           for s in conts + shapes
           if sattr(s.style, "fillColor") and sattr(s.style, "fillColor").startswith("#")
           and luminance(sattr(s.style, "fillColor")) < 0.5]
    log.check(not bad, 21, "Background colours are light", bad)

    # 22 landscape A4 page
    pw, ph = float(model.get("pageWidth") or 0), float(model.get("pageHeight") or 0)
    bad = [] if (pw and ph and pw > ph) else [f"page {pw:.0f}x{ph:.0f} is not landscape"]
    log.check(not bad, 22, "Page is landscape (A4)", bad)

    # 23 net names never crossed by a wire (own wire sits below with a gap, so
    #    skip it; any other segment through the label box is a collision)
    bad = []
    for l in netlabels:
        own = edge_below(l, edges)
        lb = bbox(l)
        for e in edges:
            if e is own:
                continue
            if any(seg_hits_rect(x1, y1, x2, y2, lb, 0.0)
                   for (x1, y1), (x2, y2) in zip(e.pts, e.pts[1:])):
                bad.append(f"net name '{l.value}' is crossed by wire {e.id}")
                break
    log.check(not bad, 23, "A net name is never crossed by a wire", bad)

    # 24 edge-label net names must float over a HORIZONTAL segment. Drawio drops
    #    an edge's value label on the mid-length segment of the routed wire; if
    #    that segment is vertical the horizontally-centred text lands across the
    #    wire. Flag any labelled edge whose mid-length segment is vertical.
    bad = []
    for e in edges:
        if not e.value or len(e.pts) < 2:
            continue
        segs = list(zip(e.pts, e.pts[1:]))
        total = sum(math.hypot(x2 - x1, y2 - y1) for (x1, y1), (x2, y2) in segs)
        if total == 0:
            continue
        acc, half = 0.0, total / 2
        for (x1, y1), (x2, y2) in segs:
            L = math.hypot(x2 - x1, y2 - y1)
            if acc + L >= half:
                if abs(x2 - x1) < abs(y2 - y1):
                    bad.append(f"net name '{e.value}' sits on a vertical segment of wire {e.id}")
                break
            acc += L
    log.check(not bad, 24, "Edge-label net names float over a horizontal segment, not a vertical one", bad)

    # 25 a module instanced N>1 times must be drawn as a deck of cards: >=3
    #    equally-sized rounded rectangles stacked with a small diagonal offset
    #    (clone primitives/modules/module_deck). The "N = <num>" marker (rule 8)
    #    does NOT replace the deck visual (rule 7) -- a single box with the label
    #    is still a single box.
    N_RE = re.compile(r"\bN\s*=\s*(\d+)\b")
    rrects = [v for v in cells.values()
              if v.x is not None and not v.edge and "rounded=1" in v.style]

    def similar(a, b):
        return (abs(a.w - b.w) <= 0.2 * max(a.w, b.w) and
                abs(a.h - b.h) <= 0.2 * max(a.h, b.h))

    def is_stacked(a, b):
        (ax, ay), (bx, by) = center(a), center(b)
        d = math.hypot(ax - bx, ay - by)
        return similar(a, b) and 2 < d < 0.6 * min(a.w, a.h, b.w, b.h)

    comp = {v.id: v.id for v in rrects}

    def find(i):
        while comp[i] != i:
            comp[i] = comp[comp[i]]
            i = comp[i]
        return i
    for i, a in enumerate(rrects):
        for b in rrects[i + 1:]:
            if is_stacked(a, b):
                comp[find(a.id)] = find(b.id)
    groups = {}
    for v in rrects:
        groups.setdefault(find(v.id), []).append(v)
    decks = []
    for g in groups.values():
        if len(g) >= 3:
            bbs = [bbox(v) for v in g]
            decks.append([min(b[0] for b in bbs), min(b[1] for b in bbs),
                          max(b[2] for b in bbs), max(b[3] for b in bbs)])
    bad = []
    for v in cells.values():
        if v.x is None or v.edge:
            continue
        txt = strip(v.value)
        m = N_RE.search(txt)
        if not m or int(m.group(1)) <= 1:
            continue
        if not any(pt_in(center(v), d) for d in decks):
            name = txt.split("N =")[0].strip() or txt.split("N=")[0].strip() or txt
            bad.append(f"module '{name}' is instanced N={m.group(1)} but is not drawn as a deck of cards")
    log.check(not bad, 25, "Modules instanced N>1 times are drawn as a deck of cards", bad)

    # 26 module-boundary ports enter/leave on the correct side (conventions
    #    Arrows 5-6): inputs (i_*) must touch the LEFT edge of the outer module,
    #    outputs (o_*) the RIGHT edge. Flag the unambiguous wrong-side case -- an
    #    input whose boundary endpoint is on the right edge, or an output whose
    #    boundary endpoint is on the left edge. (Top/bottom are left alone.)
    def on_vedge(p, xref):
        return abs(p[0] - xref) <= TOL and mb[1] - TOL <= p[1] <= mb[3] + TOL
    bad = []
    for e in edges:
        name = strip(e.value)
        if not name:
            continue
        ends = (e.pts[0], e.pts[-1])
        if name.startswith("i_") and any(on_vedge(p, mb[2]) for p in ends):
            bad.append(f"input '{name}' enters on the right edge (inputs must enter on the left)")
        elif name.startswith("o_") and any(on_vedge(p, mb[0]) for p in ends):
            bad.append(f"output '{name}' leaves on the left edge (outputs must exit on the right)")
    log.check(not bad, 26, "Module inputs enter on the left edge, outputs exit on the right", bad)

    # 27 a module is labelled by its box name only (Modules 6) and the schematic
    #    carries no explanatory text (Text 3). Flag a separate text cell sitting
    #    in a module's title band that spans most of the box width yet is neither
    #    a port, a wired net name, nor the instance-count (N=) marker -- i.e. a
    #    descriptive sub-caption like "round-robin" under an arbiter.
    BAND = 30.0
    named = [v for v in rrects if strip(v.value)]        # rounded-rect module boxes

    def portish(s):
        return (s in PORT_TOKENS or re.match(r"^[io]_", s) is not None
                or re.search(r"\[[^\]]+\]$", s) is not None)

    def wired(t):
        tb = bbox(t)
        for e in edges:
            for p in (e.pts[0], e.pts[-1]):
                if tb[0] - TOL <= p[0] <= tb[2] + TOL and tb[1] - TOL <= p[1] <= tb[3] + TOL:
                    return True
        return edge_below(t, edges) is not None
    bad = []
    for t in cells.values():
        if t.x is None or t.edge or not t.style.startswith("text;"):
            continue
        val = strip(t.value)
        if not val or portish(val) or re.search(r"\bN\s*=\s*\d+", val) or wired(t):
            continue
        ctr = center(t)
        host = min((m for m in named if pt_in(ctr, bbox(m))),
                   key=lambda m: m.w * m.h, default=None)
        if host is None:
            continue
        hb = bbox(host)
        if (ctr[1] - hb[1]) <= BAND and t.w >= 0.5 * (hb[2] - hb[0]):
            bad.append(f"stray caption '{val}' in module '{strip(host.value)}'")
    log.check(not bad, 27, "No stray descriptive caption inside a module", bad)

    passed = log.total - log.fail
    print(f"\n{'ALL %d CHECKS PASSED' % log.total if log.fail == 0 else f'{log.fail}/{log.total} CHECKS FAILED'}")
    return 1 if log.fail else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_diagram.py <diagram.drawio>")
    sys.exit(run(sys.argv[1]))
