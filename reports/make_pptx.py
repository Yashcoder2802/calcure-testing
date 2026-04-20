"""Generate presentation.pptx — structured exactly as report sections 2.1 → 2.4"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import os

# ── Palette ───────────────────────────────────────────────────────────────────
BG      = RGBColor(0x0D, 0x11, 0x17)
SURFACE = RGBColor(0x16, 0x1B, 0x22)
CARD2   = RGBColor(0x1C, 0x23, 0x2C)
BORDER  = RGBColor(0x30, 0x36, 0x3D)
ACCENT  = RGBColor(0x58, 0xA6, 0xFF)   # blue
GREEN   = RGBColor(0x3F, 0xB9, 0x50)
ORANGE  = RGBColor(0xE3, 0xB3, 0x41)
RED     = RGBColor(0xF8, 0x51, 0x49)
PURPLE  = RGBColor(0xBC, 0x8C, 0xFF)
TEAL    = RGBColor(0x39, 0xD3, 0xC3)
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
MUTED   = RGBColor(0x89, 0x93, 0x9E)
DIM     = RGBColor(0x48, 0x4F, 0x58)

SW = Inches(13.333)
SH = Inches(7.5)

prs = Presentation()
prs.slide_width  = SW
prs.slide_height = SH
blank = prs.slide_layouts[6]

# ── Helpers ───────────────────────────────────────────────────────────────────
def add_slide():
    sl = prs.slides.add_slide(blank)
    sl.background.fill.solid()
    sl.background.fill.fore_color.rgb = BG
    return sl

def box(sl, x, y, w, h, color, lc=None, lp=0):
    s = sl.shapes.add_shape(1, x, y, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = color
    if lc: s.line.color.rgb = lc; s.line.width = Pt(lp)
    else:  s.line.fill.background()
    return s

def card(sl, x, y, w, h, color=None):
    s = sl.shapes.add_shape(1, x, y, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = color or SURFACE
    s.line.color.rgb = BORDER; s.line.width = Pt(0.75)
    return s

def txt(sl, text, x, y, w, h, size=14, bold=False, color=WHITE,
        align=PP_ALIGN.LEFT, italic=False):
    t = sl.shapes.add_textbox(x, y, w, h)
    tf = t.text_frame; tf.word_wrap = True
    p  = tf.paragraphs[0]; p.alignment = align
    r  = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold
    r.font.italic = italic; r.font.color.rgb = color
    return t

def pill(sl, label, x, y, w, h, color, size=11):
    s = sl.shapes.add_shape(1, x, y, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background()
    p = s.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = label
    r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = WHITE

def header(sl, section_tag, title, sub=None, color=ACCENT):
    # top bar
    box(sl, 0, 0, SW, Inches(0.07), color)
    # section tag
    pill(sl, section_tag, Inches(0.4), Inches(0.14), Inches(1.0), Inches(0.32), color, size=10)
    txt(sl, title, Inches(1.55), Inches(0.14), Inches(11.4), Inches(0.4),
        size=22, bold=True, color=WHITE)
    if sub:
        txt(sl, sub, Inches(1.55), Inches(0.55), Inches(11.4), Inches(0.35),
            size=12, color=MUTED)
    box(sl, 0, SH - Inches(0.05), SW, Inches(0.05), color)

def section_divider(sl, number, title, color, desc=""):
    """Full-bleed section divider slide."""
    box(sl, 0, 0, Inches(4.5), SH, RGBColor(0x0A, 0x0E, 0x14))
    box(sl, Inches(4.5), 0, SW - Inches(4.5), SH, color)
    box(sl, Inches(4.45), 0, Inches(0.10), SH, WHITE)
    # big number
    txt(sl, number, Inches(4.8), Inches(1.8), Inches(7.8), Inches(2.5),
        size=130, bold=True, color=RGBColor(0xFF,0xFF,0xFF))
    txt(sl, title, Inches(0.5), Inches(2.6), Inches(3.7), Inches(1.0),
        size=28, bold=True, color=WHITE)
    if desc:
        txt(sl, desc, Inches(0.5), Inches(3.7), Inches(3.7), Inches(1.5),
            size=13, color=MUTED)

def bullet_list(sl, items, x, y, w, ih=Inches(0.55), size=13, dot=ACCENT, tc=WHITE):
    for i, item in enumerate(items):
        yy = y + i * ih
        box(sl, x, yy + ih * 0.45, Inches(0.10), Inches(0.10), dot)
        txt(sl, item, x + Inches(0.22), yy, w - Inches(0.22), ih, size=size, color=tc)

def progress_bar(sl, x, y, w, pct, color=GREEN, h=Inches(0.3)):
    box(sl, x, y, w, h, BORDER)
    if pct > 0:
        box(sl, x, y, int(w * pct / 100), h, color)

def code_box(sl, code, x, y, w, h, bc=BORDER):
    s = sl.shapes.add_shape(1, x, y, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = RGBColor(0x0A, 0x0E, 0x14)
    s.line.color.rgb = bc; s.line.width = Pt(1)
    tf = s.text_frame; tf.word_wrap = False
    r  = tf.paragraphs[0].add_run(); r.text = code
    r.font.size = Pt(9.5); r.font.color.rgb = RGBColor(0xC9, 0xD1, 0xD9)

def table_header(sl, x, y, w, h, cols, col_xs, col_ws):
    box(sl, x, y, w, h, RGBColor(0x1A, 0x22, 0x2E))
    for j, (c, cx, cw) in enumerate(zip(cols, col_xs, col_ws)):
        txt(sl, c, cx, y + Inches(0.06), cw, h - Inches(0.06),
            size=10, bold=True, color=MUTED)

def table_row(sl, x, y, w, h, vals, col_xs, col_ws, colors=None, i=0):
    bg = SURFACE if i % 2 == 0 else BG
    box(sl, x, y, w, h, bg)
    for j, (v, cx, cw) in enumerate(zip(vals, col_xs, col_ws)):
        c = colors[j] if colors else WHITE
        txt(sl, v, cx, y + Inches(0.07), cw, h - Inches(0.07), size=11, color=c)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — COVER
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
box(sl, 0, 0, Inches(8.5), SH, RGBColor(0x0A, 0x0E, 0x14))
box(sl, Inches(8.5), 0, SW - Inches(8.5), SH, RGBColor(0x0F, 0x1D, 0x36))
box(sl, Inches(8.45), 0, Inches(0.08), SH, ACCENT)
txt(sl, "SOFTWARE TESTING & DESIGN  ·  APRIL 2026",
    Inches(0.5), Inches(0.35), Inches(7.7), Inches(0.38),
    size=10, color=MUTED, italic=True)
txt(sl, "Testing", Inches(0.5), Inches(1.2), Inches(7.7), Inches(1.3),
    size=62, bold=True, color=WHITE)
txt(sl, "Calcure", Inches(0.5), Inches(2.3), Inches(7.7), Inches(1.4),
    size=72, bold=True, color=ACCENT)
txt(sl, "Terminal Calendar & Task Manager",
    Inches(0.5), Inches(3.72), Inches(7.5), Inches(0.5),
    size=16, color=MUTED)
box(sl, Inches(0.5), Inches(4.45), Inches(3.5), Inches(0.04), DIM)
txt(sl, "Yash Salunke  ·  Harshal Gajjar",
    Inches(0.5), Inches(4.6), Inches(7.5), Inches(0.42),
    size=14, bold=True, color=WHITE)
txt(sl, "github.com/Yashcoder2802/calcure-testing",
    Inches(0.5), Inches(5.08), Inches(7.5), Inches(0.35),
    size=11, color=ACCENT)
# right stats
stats = [("324","Total Tests",GREEN),("89%","Branch Coverage",ACCENT),
         ("81.6%","Mutation Score",ORANGE),("2","Bugs Found",RED)]
for i,(v,l,c) in enumerate(stats):
    y = Inches(0.5) + i * Inches(1.62)
    box(sl, Inches(8.65), y, Inches(4.5), Inches(1.45), RGBColor(0x14,0x22,0x3A))
    box(sl, Inches(8.65), y, Inches(0.08), Inches(1.45), c)
    txt(sl, v, Inches(8.85), y + Inches(0.1), Inches(3.5), Inches(0.82),
        size=44, bold=True, color=c)
    txt(sl, l, Inches(8.85), y + Inches(0.9), Inches(3.5), Inches(0.38), size=13, color=MUTED)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — AGENDA
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
header(sl, "OVERVIEW", "Agenda", "What we'll cover — in report order")
items = [
    ("1", "Subject Application",   "What Calcure is, why we chose it, code metrics", MUTED),
    ("2.1","Blackbox Testing",     "EP · BA · EG · CT — 117 tests · 2 bugs found",  ACCENT),
    ("2.2","Whitebox Testing",     "Unit + Integration · 107 tests · 89% branch coverage", GREEN),
    ("2.3","Mutation Testing",     "mutmut · 81.6% kill rate · 73 precision tests",  ORANGE),
    ("2.4","CLI Testing",          "Alternate testing · subprocess + PTY · 27 tests", PURPLE),
    ("·",  "Results & Lessons",   "Before/after · key takeaways",                    TEAL),
]
for i,(num,title,desc,color) in enumerate(items):
    x = Inches(0.35) + (i%2) * Inches(6.55)
    y = Inches(1.38) + (i//2) * Inches(1.82)
    card(sl, x, y, Inches(6.2), Inches(1.68))
    box(sl, x, y, Inches(0.08), Inches(1.68), color)
    txt(sl, num,   x+Inches(0.22), y+Inches(0.12), Inches(0.75), Inches(0.55),
        size=26, bold=True, color=color)
    txt(sl, title, x+Inches(1.0),  y+Inches(0.12), Inches(5.0), Inches(0.45),
        size=15, bold=True, color=WHITE)
    txt(sl, desc,  x+Inches(1.0),  y+Inches(0.62), Inches(5.0), Inches(0.82),
        size=11, color=MUTED)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — SUBJECT APPLICATION
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
header(sl, "SECTION 1", "Subject Application — Calcure", "Why we chose it and key metrics", MUTED)

card(sl, Inches(0.35), Inches(1.35), Inches(5.9), Inches(5.78))
txt(sl, "Why We Chose Calcure", Inches(0.55), Inches(1.48), Inches(5.5), Inches(0.38),
    size=13, bold=True, color=ACCENT)
reasons = [
    "Almost no existing tests (~67 lines in 2 files)",
    "Well-organized: separate modules per feature",
    "Great edge cases: leap years, rollovers, dates",
    "Domain everyone understands (calendar/tasks)",
    "Simple to set up — pip install, one command",
]
bullet_list(sl, reasons, Inches(0.55), Inches(1.95), Inches(5.5),
            ih=Inches(0.74), size=13, dot=ACCENT)

card(sl, Inches(6.55), Inches(1.35), Inches(6.45), Inches(5.78))
txt(sl, "Code Metrics", Inches(6.75), Inches(1.48), Inches(6.1), Inches(0.38),
    size=13, bold=True, color=ACCENT)
metrics = [
    ("Total Python LOC",     "~5,784"),
    ("Core logic LOC",       "~5,689"),
    ("Number of modules",    "~12"),
    ("Number of functions",  "~213"),
    ("Pre-existing tests",   "2 files, ~67 lines"),
    ("Language",             "Python 3"),
    ("License",              "MIT"),
]
col_xs = [Inches(6.8), Inches(10.0)]
col_ws = [Inches(3.0), Inches(2.8)]
for i,(k,v) in enumerate(metrics):
    y = Inches(2.0) + i * Inches(0.68)
    bg = CARD2 if i%2==0 else SURFACE
    box(sl, Inches(6.6), y, Inches(6.35), Inches(0.64), bg)
    txt(sl, k, col_xs[0], y+Inches(0.12), col_ws[0], Inches(0.42), size=12, color=MUTED)
    txt(sl, v, col_xs[1], y+Inches(0.12), col_ws[1], Inches(0.42), size=12, bold=True, color=WHITE)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — SECTION DIVIDER 2.1
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
section_divider(sl, "2.1", "Blackbox\nTesting", ACCENT,
    "EP · BA · EG · CT\n117 tests · 2 bugs found\nOwner: Yash Salunke")

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — 2.1 TECHNIQUES OVERVIEW
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
header(sl, "2.1", "Blackbox Testing — Techniques", "Source code not seen — only README & docs used", ACCENT)

techs = [
    ("EP","Equivalence Partitioning", ACCENT,
     "Divide inputs into groups; one test per group.",
     [("Task name: 1–999 chars","Valid — accepted"),
      ("Task name: 0 or 1000+ chars","Invalid — rejected"),
      ("Priority 1–3","Valid — accepted"),
      ("Priority 0 or 4+","Invalid — rejected")]),
    ("BA","Boundary Analysis", GREEN,
     "Test values at the exact edge of each group.",
     [("Name length = 999","Valid ✓"),
      ("Name length = 1000","Invalid ✗"),
      ("Priority = 1 (min)","Valid ✓"),
      ("Priority = 3 (max)","Valid ✓")]),
    ("EG","Error Guessing", RED,
     "Use intuition to guess where bugs hide.",
     [('Name = "   " (spaces)',"Should reject → BUG!"),
      ("CSV year = 'abc'","Should skip → BUG!"),
      ("Delete non-existent ID","Safe, unchanged"),
      ("Toggle status twice","Reverts to NORMAL")]),
    ("CT","Combinatorial Testing", PURPLE,
     "Pairwise: all 2-way input combinations.",
     [("frequency × repetition","8 combos tested"),
      ("status × privacy","4 combos tested"),
      ("firstweekday × month","24 combos tested"),
      ("deadline × status × privacy","2 combos tested")]),
]
for i,(tag,title,color,desc,rows) in enumerate(techs):
    c = i%2; r = i//2
    x = Inches(0.35) + c * Inches(6.55)
    y = Inches(1.35) + r * Inches(2.95)
    card(sl, x, y, Inches(6.2), Inches(2.8))
    pill(sl, tag, x+Inches(0.18), y+Inches(0.14), Inches(0.7), Inches(0.34), color, 12)
    txt(sl, title, x+Inches(1.05), y+Inches(0.14), Inches(4.9), Inches(0.38),
        size=14, bold=True, color=WHITE)
    txt(sl, desc, x+Inches(0.18), y+Inches(0.56), Inches(5.8), Inches(0.38),
        size=10, color=MUTED, italic=True)
    box(sl, x+Inches(0.18), y+Inches(1.02), Inches(5.8), Inches(0.28),
        RGBColor(0x1A,0x22,0x2E))
    txt(sl, "Input", x+Inches(0.28), y+Inches(1.05), Inches(3.0), Inches(0.22),
        size=9, bold=True, color=MUTED)
    txt(sl, "Expected", x+Inches(3.5), y+Inches(1.05), Inches(2.5), Inches(0.22),
        size=9, bold=True, color=MUTED)
    for j,(inp,exp) in enumerate(rows):
        yy = y+Inches(1.3)+j*Inches(0.35)
        bg = CARD2 if j%2==0 else SURFACE
        box(sl, x+Inches(0.18), yy, Inches(5.8), Inches(0.33), bg)
        txt(sl, inp, x+Inches(0.28), yy+Inches(0.04), Inches(3.1), Inches(0.26), size=9, color=WHITE)
        ec = RED if "BUG" in exp else (GREEN if "✓" in exp else MUTED)
        txt(sl, exp, x+Inches(3.5), yy+Inches(0.04), Inches(2.4), Inches(0.26),
            size=9, bold=("BUG" in exp), color=ec)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — 2.1 BLACKBOX RESULTS + BUGS
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
header(sl, "2.1", "Blackbox Results & Bugs Found", "115/117 pass · 2 tests intentionally fail — revealing real faults", ACCENT)

# Left — test class results table
card(sl, Inches(0.35), Inches(1.35), Inches(6.2), Inches(5.78))
txt(sl, "Test Classes", Inches(0.55), Inches(1.48), Inches(5.8), Inches(0.38),
    size=13, bold=True, color=ACCENT)
classes = [
    ("TestTaskManagement",        "24","EP BA EG","⚠ 1 FAIL"),
    ("TestEventManagement",       "11","EP BA EG","✓ Pass"),
    ("TestTimerBehavior",          "8","EP BA",   "✓ Pass"),
    ("TestCollectionBehavior",     "9","EP BA EG","✓ Pass"),
    ("TestFilteringBehavior",      "9","EP EG",   "✓ Pass"),
    ("TestCalendarBehavior",      "15","EP BA",   "✓ Pass"),
    ("TestRepeatedEventsBehavior","10","EP",       "✓ Pass"),
    ("TestDataPersistence",       "11","EP EG",   "⚠ 1 FAIL"),
    ("TestICSImportBehavior",      "3","EP EG",   "✓ Pass"),
    ("TestCombinatorialTesting",  "17","CT",       "✓ Pass"),
    ("TOTAL",                    "117","","115/117"),
]
cx = [Inches(0.45), Inches(2.8), Inches(4.1), Inches(5.25)]
cw = [Inches(2.3),  Inches(0.6), Inches(1.1), Inches(0.95)]
box(sl, Inches(0.4), Inches(1.92), Inches(6.1), Inches(0.3),
    RGBColor(0x1A,0x22,0x2E))
for j,h in enumerate(["Class","Tests","Tags","Result"]):
    txt(sl, h, cx[j], Inches(1.94), cw[j], Inches(0.26), size=9, bold=True, color=MUTED)
for i,(cls,cnt,tags,res) in enumerate(classes):
    y = Inches(2.24)+i*Inches(0.46)
    last = i==len(classes)-1
    bg = RGBColor(0x1A,0x2A,0x1A) if last else (CARD2 if i%2==0 else SURFACE)
    box(sl, Inches(0.4), y, Inches(6.1), Inches(0.44), bg)
    rc = RED if "FAIL" in res else (GREEN if "Pass" in res else WHITE)
    txt(sl, cls,  cx[0], y+Inches(0.07), cw[0], Inches(0.32), size=9,  color=WHITE, bold=last)
    txt(sl, cnt,  cx[1], y+Inches(0.07), cw[1], Inches(0.32), size=10, color=GREEN, bold=True)
    txt(sl, tags, cx[2], y+Inches(0.07), cw[2], Inches(0.32), size=9,  color=MUTED)
    txt(sl, res,  cx[3], y+Inches(0.07), cw[3], Inches(0.32), size=9,  color=rc, bold=last)

# Right — bugs
card(sl, Inches(6.75), Inches(1.35), Inches(6.25), Inches(2.7))
box(sl, Inches(6.75), Inches(1.35), Inches(0.08), Inches(2.7), RED)
txt(sl, "Bug #1 — Whitespace Name Accepted", Inches(7.0), Inches(1.48),
    Inches(5.8), Inches(0.38), size=13, bold=True, color=RED)
txt(sl, 'Guard: len(name) > 0\nlen("   ") == 3 → passes ✗\nFix: len(name.strip()) > 0',
    Inches(7.0), Inches(1.9), Inches(5.8), Inches(0.75), size=12, color=WHITE)
code_box(sl, 'self.tasks.add_item(make_task(name="   "))\nself.assertEqual(len(tasks.items), 0)  # FAILS',
    Inches(7.0), Inches(2.72), Inches(5.8), Inches(0.75), RED)
txt(sl, "Severity: Medium — invisible tasks stored",
    Inches(7.0), Inches(3.55), Inches(5.8), Inches(0.32), size=10, color=MUTED, italic=True)

card(sl, Inches(6.75), Inches(4.2), Inches(6.25), Inches(2.93))
box(sl, Inches(6.75), Inches(4.2), Inches(0.08), Inches(2.93), RED)
txt(sl, "Bug #2 — CSV Crash on Bad Year Field", Inches(7.0), Inches(4.33),
    Inches(5.8), Inches(0.38), size=13, bold=True, color=RED)
txt(sl, 'int(row[1]) raises ValueError\nif year = "not-a-year" in CSV\nFix: wrap in try/except',
    Inches(7.0), Inches(4.76), Inches(5.8), Inches(0.75), size=12, color=WHITE)
code_box(sl, 'loaded = EventLoaderCSV(cf).load()\nself.assertEqual(len(loaded.items), 0)  # FAILS',
    Inches(7.0), Inches(5.58), Inches(5.8), Inches(0.75), RED)
txt(sl, "Severity: High — app crashes on startup",
    Inches(7.0), Inches(6.42), Inches(5.8), Inches(0.32), size=10, color=MUTED, italic=True)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — SECTION DIVIDER 2.2
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
section_divider(sl, "2.2", "Whitebox\nTesting", GREEN,
    "Unit + Integration\n107 tests · 89% branch coverage\nOwner: Yash Salunke")

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — 2.2 UNIT TESTS
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
header(sl, "2.2", "Whitebox — Unit Tests", "86 tests targeting specific branches in source code", GREEN)

classes = [
    ("TestTimerInternals",               "12","data.py L234",    "Even/odd stamp parity, pair sum, format"),
    ("TestCollectionInternals",          "13","data.py L89",     "999/1000 guard, \\[ reject, max(ids)+1"),
    ("TestSubtaskPrefixEncoding",         "7","data.py L312",    "'--' vs '----', insert(n+1), 100-char cap"),
    ("TestCalendarInternals",            "13","calendars.py L78","Leap year ÷4/÷100/÷400, grid padding"),
    ("TestPersianCalendarInternals",      "4","calendars.py L200","Jalali conversion, Persian week numbers"),
    ("TestRepeatedEventsInternals",       "8","data.py L360",    "range(1,repetition), month/year overflow"),
    ("TestCSVLoadingInternals",           "8","loaders.py L145", "Old/new format, dot-prefix, d/w/m/y codes"),
    ("TestAuxiliaryLoaderInternals",      "3","loaders.py L280", "BirthdayLoader early returns"),
    ("TestICSLoaderInternals",            "8","loaders.py L201", "RRULE/EXDATE, missing-field fallbacks"),
    ("TestFilterInternals",               "4","calendars.py L310","Stable sort, year check vs no year"),
    ("TestMoveTaskInternals",             "3","data.py L401",    "pop+insert, post-pop index shift"),
    ("TestPauseAllOtherTimersInternals",  "3","data.py L450",    "is_counting guard, ID exemption"),
]
cx = [Inches(0.4), Inches(2.55), Inches(3.3), Inches(5.1)]
cw = [Inches(2.1),  Inches(0.72), Inches(1.75), Inches(7.9)]
box(sl, Inches(0.35), Inches(1.35), SW-Inches(0.7), Inches(0.32),
    RGBColor(0x1A,0x22,0x2E))
for j,h in enumerate(["Test Class","Tests","Source Location","What it verifies"]):
    txt(sl, h, cx[j], Inches(1.37), cw[j], Inches(0.26), size=9, bold=True, color=MUTED)
for i,(cls,cnt,loc,what) in enumerate(classes):
    y = Inches(1.68)+i*Inches(0.48)
    bg = SURFACE if i%2==0 else BG
    box(sl, Inches(0.35), y, SW-Inches(0.7), Inches(0.45), bg)
    txt(sl, cls,  cx[0], y+Inches(0.07), cw[0], Inches(0.32), size=10, color=PURPLE)
    txt(sl, cnt,  cx[1], y+Inches(0.07), cw[1], Inches(0.32), size=11, bold=True, color=GREEN)
    txt(sl, loc,  cx[2], y+Inches(0.07), cw[2], Inches(0.32), size=9,  color=MUTED)
    txt(sl, what, cx[3], y+Inches(0.07), cw[3], Inches(0.32), size=10, color=WHITE)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — 2.2 INTEGRATION + COVERAGE
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
header(sl, "2.2", "Whitebox — Integration Tests & Coverage", "21 pipeline tests + branch coverage with coverage.py --branch", GREEN)

# Left — integration table
card(sl, Inches(0.35), Inches(1.35), Inches(6.2), Inches(3.6))
txt(sl, "Integration Test Pipelines  (21 tests)", Inches(0.55), Inches(1.48),
    Inches(5.8), Inches(0.38), size=13, bold=True, color=GREEN)
pipelines = [
    ("Events → RepeatedEvents → filter",        "5","Recurring events visible on correct days"),
    ("Tasks → Save → Load → Modify → Save",      "4","Full persistence cycle"),
    ("Events → Save → Load → RepeatedEvents",    "3","Frequency survives CSV round-trip"),
    ("Tasks + Timer full lifecycle",              "3","start/pause/resume/reset"),
    ("Calendar + Filter consistency",             "3","Grid dimensions match filter"),
    ("ICS import → domain objects → filter",     "3","VTODO/VEVENT through real .ics"),
]
px = [Inches(0.45), Inches(4.35), Inches(5.0)]
pw = [Inches(3.8),  Inches(0.55), Inches(1.9)]
box(sl, Inches(0.4), Inches(1.93), Inches(6.1), Inches(0.28),
    RGBColor(0x1A,0x22,0x2E))
for j,h in enumerate(["Pipeline","Tests","Checks"]):
    txt(sl, h, px[j], Inches(1.95), pw[j], Inches(0.24), size=9, bold=True, color=MUTED)
for i,(pip,cnt,chk) in enumerate(pipelines):
    y = Inches(2.22)+i*Inches(0.44)
    bg = CARD2 if i%2==0 else SURFACE
    box(sl, Inches(0.4), y, Inches(6.1), Inches(0.41), bg)
    txt(sl, pip, px[0], y+Inches(0.06), pw[0], Inches(0.30), size=9,  color=WHITE)
    txt(sl, cnt, px[1], y+Inches(0.06), pw[1], Inches(0.30), size=10, bold=True, color=GREEN)
    txt(sl, chk, px[2], y+Inches(0.06), pw[2], Inches(0.30), size=9,  color=MUTED)

# Left bottom — coverage command
card(sl, Inches(0.35), Inches(5.1), Inches(6.2), Inches(2.03))
txt(sl, "Run Coverage", Inches(0.55), Inches(5.22), Inches(5.8), Inches(0.32),
    size=11, bold=True, color=GREEN)
code_box(sl,
    "coverage run --branch -m pytest \\\n"
    "  tests/blackbox/ tests/whitebox/ tests/integration/ -q\n"
    "coverage report -m calcure/data.py calcure/calendars.py ...",
    Inches(0.45), Inches(5.6), Inches(6.0), Inches(1.35))

# Right — coverage bars
card(sl, Inches(6.75), Inches(1.35), Inches(6.25), Inches(5.78))
txt(sl, "Branch Coverage Results", Inches(6.95), Inches(1.48),
    Inches(5.9), Inches(0.38), size=13, bold=True, color=GREEN)
mods = [
    ("calendars.py", 97, GREEN,  "97%"),
    ("data.py",      94, GREEN,  "94%"),
    ("savers.py",    92, ACCENT, "92%"),
    ("loaders.py",   85, ORANGE, "85%"),
    ("__init__.py",  78, ORANGE, "78%"),
]
for i,(mod,pct,color,label) in enumerate(mods):
    y = Inches(2.05)+i*Inches(0.95)
    txt(sl, mod,   Inches(6.95), y,              Inches(2.0), Inches(0.38), size=13, bold=True, color=WHITE)
    txt(sl, label, Inches(11.7), y,              Inches(1.1), Inches(0.38), size=14, bold=True, color=color)
    progress_bar(sl, Inches(6.95), y+Inches(0.42), Inches(5.8), pct, color=color)

box(sl, Inches(6.75), Inches(6.68), Inches(6.25), Inches(0.04), BORDER)
txt(sl, "Core Average:", Inches(6.95), Inches(6.76), Inches(2.5), Inches(0.38),
    size=13, color=MUTED)
txt(sl, "89%", Inches(9.45), Inches(6.72), Inches(2.0), Inches(0.42),
    size=22, bold=True, color=GREEN)
txt(sl, "(Goal was 80%+ ✓)", Inches(11.4), Inches(6.76), Inches(1.5), Inches(0.38),
    size=10, color=MUTED)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — SECTION DIVIDER 2.3
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
section_divider(sl, "2.3", "Mutation\nTesting", ORANGE,
    "mutmut v2.4.4\n81.6% kill rate · 784 mutants\nOwner: Harshal Gajjar")

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — 2.3 MUTATION SCORES + SURVIVORS
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
header(sl, "2.3", "Mutation Testing — Scores & Surviving Mutants",
       "mutmut mutates data.py + calendars.py · target was 80%+", ORANGE)

# Top metrics
for i,(v,l,c) in enumerate([("784","Total Mutants",ACCENT),("640","Killed",GREEN),
                              ("144","Survived",RED),("81.6%","Kill Rate",ORANGE)]):
    x = Inches(0.35+i*3.25)
    card(sl, x, Inches(1.35), Inches(3.0), Inches(1.55))
    box(sl, x, Inches(1.35), Inches(3.0), Inches(0.06), c)
    txt(sl, v, x, Inches(1.52), Inches(3.0), Inches(0.72),
        size=38, bold=True, color=c, align=PP_ALIGN.CENTER)
    txt(sl, l, x, Inches(2.22), Inches(3.0), Inches(0.35),
        size=12, color=MUTED, align=PP_ALIGN.CENTER)

# Left — per-module table
card(sl, Inches(0.35), Inches(3.1), Inches(6.2), Inches(1.85))
txt(sl, "Score by Module", Inches(0.55), Inches(3.22),
    Inches(5.8), Inches(0.35), size=12, bold=True, color=ORANGE)
mod_data = [
    ("calcure/data.py",      "178","518","134","79.4%"),
    ("calcure/calendars.py", " 29","122"," 10","92.4%"),
    ("TOTAL",                "207","640","144","81.6%"),
]
mx = [Inches(0.45), Inches(2.8), Inches(3.7), Inches(4.6), Inches(5.5)]
mw = [Inches(2.3),  Inches(0.85), Inches(0.85), Inches(0.85), Inches(1.0)]
box(sl, Inches(0.4), Inches(3.63), Inches(6.1), Inches(0.28),
    RGBColor(0x1A,0x22,0x2E))
for j,h in enumerate(["Module","Locs","Killed","Survived","Score"]):
    txt(sl, h, mx[j], Inches(3.65), mw[j], Inches(0.24), size=9, bold=True, color=MUTED)
for i,(mod,loc,kil,sur,score) in enumerate(mod_data):
    y = Inches(3.93)+i*Inches(0.44)
    last = i==2
    bg = RGBColor(0x1A,0x2A,0x1A) if last else (CARD2 if i%2==0 else SURFACE)
    box(sl, Inches(0.4), y, Inches(6.1), Inches(0.42), bg)
    txt(sl, mod,   mx[0], y+Inches(0.07), mw[0], Inches(0.3), size=9,  color=WHITE, bold=last)
    txt(sl, loc,   mx[1], y+Inches(0.07), mw[1], Inches(0.3), size=10, color=MUTED)
    txt(sl, kil,   mx[2], y+Inches(0.07), mw[2], Inches(0.3), size=10, color=GREEN, bold=True)
    txt(sl, sur,   mx[3], y+Inches(0.07), mw[3], Inches(0.3), size=10, color=RED,   bold=True)
    txt(sl, score, mx[4], y+Inches(0.07), mw[4], Inches(0.3), size=11, color=ORANGE, bold=last)

# Right — surviving categories
card(sl, Inches(6.75), Inches(3.1), Inches(6.25), Inches(4.03))
txt(sl, "Why Did 144 Mutants Survive?", Inches(6.95), Inches(3.22),
    Inches(5.9), Inches(0.35), size=12, bold=True, color=RED)
surv = [
    ("Off-by-one arithmetic (+1/−1)",     "38","Assertions too loose"),
    ("Comparison flips (>= vs >)",        "31","Not on critical path"),
    ("String literal mutations",          "28","Not asserted in tests"),
    ("Dead / unreachable code",           "22","Cannot be killed"),
    ("Boolean negation",                  "15","Equivalent mutant"),
    ("Other",                             "10","Various"),
]
sx = [Inches(6.85), Inches(10.4), Inches(11.1)]
sw2 = [Inches(3.45), Inches(0.6), Inches(1.8)]
box(sl, Inches(6.8), Inches(3.65), Inches(6.15), Inches(0.28),
    RGBColor(0x1A,0x22,0x2E))
for j,h in enumerate(["Mutant Type","#","Reason"]):
    txt(sl, h, sx[j], Inches(3.67), sw2[j], Inches(0.24), size=9, bold=True, color=MUTED)
for i,(typ,cnt,reason) in enumerate(surv):
    y = Inches(3.95)+i*Inches(0.52)
    bg = CARD2 if i%2==0 else SURFACE
    box(sl, Inches(6.8), y, Inches(6.15), Inches(0.48), bg)
    txt(sl, typ,    sx[0], y+Inches(0.07), sw2[0], Inches(0.34), size=10, color=WHITE)
    txt(sl, cnt,    sx[1], y+Inches(0.07), sw2[1], Inches(0.34), size=11, bold=True, color=RED)
    txt(sl, reason, sx[2], y+Inches(0.07), sw2[2], Inches(0.34), size=9,  color=MUTED)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 12 — 2.3 PRECISION TESTS (73)
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
header(sl, "2.3", "Mutation Testing — 73 Precision Tests",
       "Each test designed to kill exactly one surviving mutant", ORANGE)

card(sl, Inches(0.35), Inches(1.35), Inches(12.63), Inches(0.75))
txt(sl, "Every test is labeled with the exact mutant it kills — e.g. [DAT-L234] means data.py line 234",
    Inches(0.55), Inches(1.48), Inches(12.1), Inches(0.5),
    size=12, color=WHITE)

classes = [
    ("TestDefaultFieldIdentity",      "DAT-L48, DAT-L95",     "3","None→False/True default mutations"),
    ("TestBooleanReturnIdentity",      "DAT-L126 (multiple)",  "6","False-identity in collection methods"),
    ("TestCollectionChangedInit",      "DAT-L130",             "3",".changed initialized to exactly False"),
    ("TestTimerPassedTimeArithmetic",  "DAT-L234",             "3","Day-boundary arithmetic"),
    ("TestNameLengthBoundaryPrecision","DAT-L89",              "4","999/1000 char comparator precision"),
    ("TestStatusTogglePrecision",      "DAT-L173",             "4","Same-status revert logic"),
    ("TestGenerateIdPrecision",        "DAT-L112",             "3","max+1 arithmetic mutations"),
    ("TestSubtaskDashPrecision",       "DAT-L312",             "4","'--' vs '----' comparisons"),
    ("TestWeeklyRecurrenceFormula",    "DAT-L360",             "4","Weekly offset arithmetic"),
    ("TestDailyRecurrenceFormula",     "DAT-L380",             "3","Daily overflow boundary"),
    ("TestFilterEventsYearPrecision",  "CAL-L310",             "3","Year-equality comparators"),
    ("TestBirthdaysFilterPrecision",   "CAL-L320",             "3","Month/day comparators"),
    ("TestMonthlyRecurrenceFormula",   "DAT-L400",             "4","Month-overflow arithmetic"),
    ("TestCalendarLeapYearPrecision",  "CAL-L78",              "6","Leap-year formula comparators"),
    ("TestRepeatedEventsEdgeCases",    "DAT-L350",             "2","repetition≥1 guard, rrule branch"),
    ("TestItemExistsNotFound",         "DAT-L450",             "2","item_exists false-return identity"),
    ("TOTAL",                          "",                    "73",""),
]
cx2 = [Inches(0.4), Inches(2.9), Inches(6.5), Inches(7.4)]
cw2 = [Inches(2.45), Inches(3.55), Inches(0.85), Inches(5.7)]
box(sl, Inches(0.35), Inches(2.17), SW-Inches(0.7), Inches(0.3),
    RGBColor(0x1A,0x22,0x2E))
for j,h in enumerate(["Test Class","Target Mutant Label","Tests","What it kills"]):
    txt(sl, h, cx2[j], Inches(2.19), cw2[j], Inches(0.26), size=9, bold=True, color=MUTED)
for i,(cls,label,cnt,kills) in enumerate(classes):
    y = Inches(2.48)+i*Inches(0.34)
    last = i==len(classes)-1
    bg = RGBColor(0x1A,0x2A,0x1A) if last else (SURFACE if i%2==0 else BG)
    box(sl, Inches(0.35), y, SW-Inches(0.7), Inches(0.32), bg)
    txt(sl, cls,   cx2[0], y+Inches(0.04), cw2[0], Inches(0.26), size=9,  color=PURPLE, bold=last)
    txt(sl, label, cx2[1], y+Inches(0.04), cw2[1], Inches(0.26), size=9,  color=TEAL)
    txt(sl, cnt,   cx2[2], y+Inches(0.04), cw2[2], Inches(0.26), size=10, bold=True, color=ORANGE)
    txt(sl, kills, cx2[3], y+Inches(0.04), cw2[3], Inches(0.26), size=9,  color=WHITE)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 13 — SECTION DIVIDER 2.4
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
section_divider(sl, "2.4", "CLI\nTesting", PURPLE,
    "Alternate Testing\n27 tests · subprocess + PTY\nOwner: Harshal Gajjar")

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 14 — 2.4 CLI TESTING
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
header(sl, "2.4", "Alternate Testing — CLI Testing",
       "Calcure needs a real TTY — two-tier strategy with subprocess and pty module", PURPLE)

# Two tier cards
card(sl, Inches(0.35), Inches(1.35), Inches(6.2), Inches(2.35))
box(sl, Inches(0.35), Inches(1.35), Inches(6.2), Inches(0.06), ACCENT)
txt(sl, "Tier 1 — No TTY  (subprocess)", Inches(0.55), Inches(1.5),
    Inches(5.8), Inches(0.4), size=14, bold=True, color=ACCENT)
txt(sl, "Flags processed BEFORE curses starts.\nPlain subprocess.run() is enough — no terminal needed.",
    Inches(0.55), Inches(1.96), Inches(5.8), Inches(0.55), size=11, color=MUTED)
bullet_list(sl, ["-v  (version)","--folder","--config","Unknown/invalid flags"],
    Inches(0.55), Inches(2.58), Inches(5.8), ih=Inches(0.38), size=12, dot=ACCENT)

card(sl, Inches(6.75), Inches(1.35), Inches(6.25), Inches(2.35))
box(sl, Inches(6.75), Inches(1.35), Inches(6.25), Inches(0.06), PURPLE)
txt(sl, "Tier 2 — PTY  (pty module)", Inches(6.95), Inches(1.5),
    Inches(5.9), Inches(0.4), size=14, bold=True, color=PURPLE)
txt(sl, "Flags processed INSIDE main(stdscr) after curses starts.\nPython's pty module provides a real pseudo-terminal.",
    Inches(6.95), Inches(1.96), Inches(5.9), Inches(0.55), size=11, color=MUTED)
bullet_list(sl, ["--task  (add task)","--event  (add event)","Data integrity checks"],
    Inches(6.95), Inches(2.58), Inches(5.9), ih=Inches(0.38), size=12, dot=PURPLE)

# Test class table
card(sl, Inches(0.35), Inches(3.85), Inches(12.63), Inches(3.28))
txt(sl, "Test Classes  (27 tests total)", Inches(0.55), Inches(3.98),
    Inches(12.0), Inches(0.38), size=13, bold=True, color=PURPLE)
cli_classes = [
    ("TestVersionFlag",        "3","Tier 1","-v outputs version, exits 0, creates no files"),
    ("TestFolderFlag",         "4","Tier 1","--folder creates dir, routes CSVs, handles unwritable"),
    ("TestConfigFlag",         "3","Tier 1","--config creates/reads, handles corrupt config"),
    ("TestTaskFlag",           "4","Tier 2","--task writes CSV, empty name, no event side-effects"),
    ("TestEventFlag",          "5","Tier 2","--event writes CSV, malformed input, invalid dates"),
    ("TestInvalidFlags",       "3","Tier 1","Unknown flags don't crash"),
    ("TestCombinedInvocations","3","Tier 1","No args, --privacy+--folder, -v+--folder"),
    ("TestDataIntegrity",      "2","Tier 2","Bad flag doesn't corrupt data; atomic .bak write"),
]
tcx = [Inches(0.45), Inches(2.85), Inches(3.6), Inches(4.45)]
tcw = [Inches(2.35), Inches(0.7), Inches(0.8), Inches(8.8)]
box(sl, Inches(0.4), Inches(4.42), Inches(12.55), Inches(0.28),
    RGBColor(0x1A,0x22,0x2E))
for j,h in enumerate(["Class","Tests","Tier","Scenario"]):
    txt(sl, h, tcx[j], Inches(4.44), tcw[j], Inches(0.24), size=9, bold=True, color=MUTED)
for i,(cls,cnt,tier,scen) in enumerate(cli_classes):
    y = Inches(4.72)+i*Inches(0.42)
    bg = SURFACE if i%2==0 else BG
    box(sl, Inches(0.4), y, Inches(12.55), Inches(0.40), bg)
    txt(sl, cls,  tcx[0], y+Inches(0.06), tcw[0], Inches(0.3), size=10, color=WHITE)
    txt(sl, cnt,  tcx[1], y+Inches(0.06), tcw[1], Inches(0.3), size=11, bold=True, color=GREEN)
    tc = ACCENT if tier=="Tier 1" else PURPLE
    txt(sl, tier, tcx[2], y+Inches(0.06), tcw[2], Inches(0.3), size=9,  color=tc)
    txt(sl, scen, tcx[3], y+Inches(0.06), tcw[3], Inches(0.3), size=10, color=MUTED)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 15 — RESULTS DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
header(sl, "RESULTS", "Final Results Dashboard", "All numbers across all 4 sections", GREEN)

# 6 big metrics
bigs = [("324","Total Tests",GREEN,"4 suites"),("89%","Branch Coverage",ACCENT,"goal: 80%+"),
        ("81.6%","Mutation Score",ORANGE,"goal: 80%+"),("2","Bugs Found",RED,"real faults"),
        ("5","Test Files",PURPLE,""),("5,784","LOC Tested",TEAL,"Python 3.9+")]
for i,(v,l,c,s) in enumerate(bigs):
    x = Inches(0.35)+(i%3)*Inches(4.35)
    y = Inches(1.4)+(i//3)*Inches(2.2)
    card(sl, x, y, Inches(4.0), Inches(2.0))
    box(sl, x, y, Inches(4.0), Inches(0.06), c)
    txt(sl, v, x, y+Inches(0.18), Inches(4.0), Inches(0.82),
        size=40, bold=True, color=c, align=PP_ALIGN.CENTER)
    txt(sl, l, x, y+Inches(0.98), Inches(4.0), Inches(0.38),
        size=13, color=WHITE, align=PP_ALIGN.CENTER)
    if s:
        txt(sl, s, x, y+Inches(1.38), Inches(4.0), Inches(0.32),
            size=10, color=MUTED, align=PP_ALIGN.CENTER)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 16 — BEFORE vs AFTER
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
header(sl, "RESULTS", "Before vs After", "What we built — aligned to each report section")

rows = [
    ("2.1 Blackbox tests",         "0",   "117",   "+117  (EP+BA+EG+CT)"),
    ("2.2 Whitebox unit tests",    "0",   "86",    "+86   targeting specific branches"),
    ("2.2 Integration tests",      "0",   "21",    "+21   pipeline tests"),
    ("2.3 Mutation-targeted tests","0",   "73",    "+73   precision mutant killers"),
    ("2.4 CLI tests",              "0",   "27",    "+27   Tier1 + Tier2 PTY"),
    ("Branch coverage (core)",     "~0%", "89%",   "Exceeded 80% goal"),
    ("Mutation score",             "0%",  "81.6%", "Exceeded 80% goal"),
    ("Real bugs found",            "0",   "2",     "Both found via EG blackbox"),
]
bx = [Inches(0.35), Inches(4.8), Inches(6.6), Inches(8.6)]
bw = [Inches(4.4),  Inches(1.7), Inches(1.9), Inches(4.6)]
box(sl, Inches(0.35), Inches(1.35), SW-Inches(0.7), Inches(0.42),
    RGBColor(0x1A,0x22,0x2E))
for j,h in enumerate(["Metric","Before","After","Delta"]):
    colors2 = [MUTED,RED,GREEN,ACCENT]
    txt(sl, h, bx[j], Inches(1.38), bw[j], Inches(0.35),
        size=11, bold=True, color=colors2[j])
for i,(metric,before,after,delta) in enumerate(rows):
    y = Inches(1.8)+i*Inches(0.68)
    bg = SURFACE if i%2==0 else BG
    box(sl, Inches(0.35), y, SW-Inches(0.7), Inches(0.64), bg)
    txt(sl, metric, bx[0], y+Inches(0.12), bw[0], Inches(0.42), size=13, color=WHITE)
    txt(sl, before, bx[1], y+Inches(0.08), bw[1], Inches(0.5),
        size=18, bold=True, color=RED, align=PP_ALIGN.CENTER)
    txt(sl, "→", Inches(6.35), y+Inches(0.12), Inches(0.4), Inches(0.38),
        size=16, color=DIM, align=PP_ALIGN.CENTER)
    txt(sl, after,  bx[2], y+Inches(0.08), bw[2], Inches(0.5),
        size=18, bold=True, color=GREEN, align=PP_ALIGN.CENTER)
    txt(sl, delta,  bx[3], y+Inches(0.12), bw[3], Inches(0.42),
        size=11, color=MUTED, italic=True)

# ═════════════════════════════════════════════════════════════════════════════
# SLIDE 17 — Q&A
# ═════════════════════════════════════════════════════════════════════════════
sl = add_slide()
box(sl, 0, 0, SW, Inches(0.08), ACCENT)
box(sl, 0, SH-Inches(0.08), SW, Inches(0.08), ACCENT)
txt(sl, "Q&A", Inches(0), Inches(1.5), SW, Inches(2.5),
    size=110, bold=True, color=RGBColor(0x1A,0x22,0x2E), align=PP_ALIGN.CENTER)
txt(sl, "Q&A", Inches(0.05), Inches(1.45), SW, Inches(2.5),
    size=110, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
txt(sl, "Thank you!", Inches(0), Inches(4.1), SW, Inches(0.6),
    size=24, color=ACCENT, align=PP_ALIGN.CENTER)
txt(sl, "Yash Salunke  ·  Harshal Gajjar",
    Inches(0), Inches(4.75), SW, Inches(0.45),
    size=15, color=MUTED, align=PP_ALIGN.CENTER)
for i,(label,color) in enumerate([("2.1 Blackbox — 117",ACCENT),("2.2 Whitebox — 107",GREEN),
                                    ("2.3 Mutation — 81.6%",ORANGE),("2.4 CLI — 27",PURPLE)]):
    pill(sl, label, Inches(1.5+i*2.6), Inches(5.85), Inches(2.4), Inches(0.46), color, 12)

# ─────────────────────────────────────────────────────────────────────────────
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presentation.pptx")
prs.save(out)
print(f"Saved: {out}  ({len(prs.slides)} slides)")
