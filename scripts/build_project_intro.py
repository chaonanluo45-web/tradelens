from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
OUT = ROOT / "docs" / "TradeLens_项目介绍.docx"

NAVY = RGBColor(0x0B, 0x17, 0x2A)
INK = RGBColor(0x1F, 0x2D, 0x3D)
MUTED = RGBColor(0x6B, 0x7A, 0x8F)
TEAL = RGBColor(0x0F, 0x76, 0x6E)
TEAL_BRIGHT = RGBColor(0x2D, 0xD4, 0xBF)
LIME = RGBColor(0xD9, 0xF9, 0x9D)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
PAPER = RGBColor(0xF4, 0xF7, 0xF2)
AMBER = RGBColor(0x9A, 0x67, 0x00)

FONT = "Microsoft YaHei"
MONO = "Consolas"


def set_run_font(run, name=FONT, size=10.5, bold=False, color=INK, italic=False):
    run.font.name = name
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    run.font.color.rgb = color
    rPr = run._element.get_or_add_rPr()
    rPr.rFonts.set(qn("w:eastAsia"), name)
    return run


def add_run(paragraph, text, **kwargs):
    return set_run_font(paragraph.add_run(text), **kwargs)


def para(text="", size=10.5, color=INK, bold=False, name=FONT, align=WD_ALIGN_PARAGRAPH.LEFT,
         before=0, after=4, line=1.5):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line
    if text:
        add_run(p, text, size=size, color=color, bold=bold, name=name)
    return p


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def set_cell_margins(cell, top=0.16, bottom=0.16, left=0.22, right=0.22):
    tcPr = cell._tc.get_or_add_tcPr()
    old = tcPr.find(qn("w:tcMar"))
    if old is not None:
        tcPr.remove(old)
    tcMar = OxmlElement("w:tcMar")
    for side, value in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(int(value * 567)))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_border(cell, **kwargs):
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.find(qn("w:tcBorders"))
    if tcBorders is None:
        tcBorders = OxmlElement("w:tcBorders")
        tcPr.append(tcBorders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        if edge not in kwargs:
            continue
        edge_data = kwargs.get(edge)
        tag = f"w:{edge}"
        element = tcBorders.find(qn(tag))
        if element is None:
            element = OxmlElement(tag)
            tcBorders.append(element)
        if edge_data is None:
            element.set(qn("w:val"), "nil")
        else:
            element.set(qn("w:val"), edge_data.get("val", "single"))
            element.set(qn("w:sz"), str(edge_data.get("sz", 4)))
            element.set(qn("w:space"), "0")
            element.set(qn("w:color"), edge_data.get("color", "DFE7DE"))


def _replace_borders(table, color=None, size=4):
    tblPr = table._tbl.tblPr
    old = tblPr.find(qn("w:tblBorders"))
    if old is not None:
        tblPr.remove(old)
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        if color is None:
            element.set(qn("w:val"), "nil")
        else:
            element.set(qn("w:val"), "single")
            element.set(qn("w:sz"), str(size))
            element.set(qn("w:space"), "0")
            element.set(qn("w:color"), color)
        borders.append(element)
    tblPr.append(borders)


def set_table_borders(table, color="DFE7DE", size=4):
    _replace_borders(table, color=color, size=size)


def no_table_borders(table):
    _replace_borders(table, color=None)


def set_table_width(table, widths):
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = table._tbl.tblPr
    tblW = tblPr.find(qn("w:tblW"))
    if tblW is None:
        tblW = OxmlElement("w:tblW")
        tblPr.append(tblW)
    tblW.set(qn("w:w"), str(int(sum(widths) / 2.54 * 1440)))
    tblW.set(qn("w:type"), "dxa")
    layout = tblPr.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        tblPr.append(layout)
    layout.set(qn("w:type"), "fixed")
    for i, width in enumerate(widths):
        table.columns[i].width = Cm(width)
    for row in table.rows:
        for i, width in enumerate(widths):
            row.cells[i].width = Cm(width)


def new_table(rows, cols, widths, borders=True):
    table = doc.add_table(rows=rows, cols=cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    if borders:
        set_table_borders(table)
    else:
        no_table_borders(table)
    set_table_width(table, widths)
    for row in table.rows:
        trPr = row._tr.get_or_add_trPr()
        cantSplit = OxmlElement("w:cantSplit")
        trPr.append(cantSplit)
        for cell in row.cells:
            set_cell_margins(cell)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    return table


def cell_text(cell, text, size=9.5, color=INK, bold=False, name=FONT,
              align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=1.3):
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line
    add_run(p, text, size=size, color=color, bold=bold, name=name)
    return p


def cell_add(cell, text, size=9.5, color=INK, bold=False, name=FONT,
             align=WD_ALIGN_PARAGRAPH.LEFT, before=0, after=0, line=1.3):
    p = cell.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line
    add_run(p, text, size=size, color=color, bold=bold, name=name)
    return p


def heading(num, title, page_break=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.page_break_before = page_break
    p.paragraph_format.keep_with_next = True
    add_run(p, num, size=10, color=TEAL, bold=True, name=MONO)
    add_run(p, "  /  ", size=10, color=MUTED, name=MONO)
    add_run(p, title, size=19, color=NAVY, bold=True)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "6")
    bottom.set(qn("w:color"), "DCE5DC")
    pBdr.append(bottom)
    pPr.append(pBdr)
    return p


def subhead(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.0
    p.paragraph_format.keep_with_next = True
    add_run(p, text, size=12, color=NAVY, bold=True)
    return p


def callout(title, body=None, fill="EAF4F0", border="0F766E", title_color=TEAL):
    table = new_table(1, 1, [16.6], borders=False)
    cell = table.cell(0, 0)
    shade_cell(cell, fill)
    set_cell_margins(cell, top=0.24, bottom=0.24, left=0.42, right=0.42)
    set_cell_border(cell, left={"sz": 18, "color": border}, top=None, bottom=None, right=None)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2 if body else 0)
    p.paragraph_format.line_spacing = 1.15
    add_run(p, title, size=11.5, color=title_color, bold=True)
    if body:
        p2 = cell.add_paragraph()
        p2.paragraph_format.space_after = Pt(0)
        p2.paragraph_format.line_spacing = 1.5
        add_run(p2, body, size=9.0, color=INK)
    return table


def add_picture(path, width_cm, caption=None):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(str(path), width=Cm(width_cm))
    if caption:
        c = doc.add_paragraph()
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.paragraph_format.space_after = Pt(0)
        add_run(c, caption, size=7.8, color=MUTED)


def add_page_break():
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.add_run().add_break(WD_BREAK.PAGE)


def add_page_field(paragraph):
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), " PAGE ")
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "6B7A8F")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "17")
    rPr.append(color)
    rPr.append(sz)
    r.append(rPr)
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    paragraph._p.append(fld)


doc = Document()
doc.core_properties.title = "TradeLens 外贸罗盘 · 项目介绍"
doc.core_properties.subject = "高级组 · 主题 1 金融经贸 · 外贸市场情报智能体"
doc.core_properties.author = "TradeLens 项目组"
doc.core_properties.comments = "知乎黑客松 · 湾区共创季 参赛作品项目介绍"

style = doc.styles["Normal"]
style.font.name = FONT
style.font.size = Pt(10.5)
style.font.color.rgb = INK
style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
style.paragraph_format.line_spacing = 1.5
style.paragraph_format.space_after = Pt(4)

section = doc.sections[0]
section.page_width = Cm(21)
section.page_height = Cm(29.7)
section.left_margin = Cm(2.2)
section.right_margin = Cm(2.2)
section.top_margin = Cm(2.0)
section.bottom_margin = Cm(2.0)
section.header_distance = Cm(1.0)
section.footer_distance = Cm(1.0)

# ------------------------------------------------------------------ cover
banner = doc.add_table(rows=1, cols=2)
banner.alignment = WD_TABLE_ALIGNMENT.CENTER
banner.autofit = False
no_table_borders(banner)
set_table_width(banner, [12.2, 4.4])
row = banner.rows[0]
row.height = Cm(7.3)
row.height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
for cell in row.cells:
    shade_cell(cell, "0B172A")
    set_cell_margins(cell, top=0.55, bottom=0.55, left=0.62, right=0.5)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    set_cell_border(cell, bottom={"sz": 14, "color": "2DD4BF"}, top=None, left=None, right=None)

left, right = row.cells
p = left.paragraphs[0]
p.paragraph_format.space_after = Pt(4)
p.paragraph_format.line_spacing = 1.0
add_run(p, "PROJECT BRIEF  /  2026", size=7.8, color=TEAL_BRIGHT, bold=True, name=MONO)

p = left.add_paragraph()
p.paragraph_format.space_before = Pt(4)
p.paragraph_format.space_after = Pt(0)
p.paragraph_format.line_spacing = 0.95
add_run(p, "TradeLens", size=34, color=WHITE, bold=True, name="Arial")

p = left.add_paragraph()
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.space_after = Pt(7)
p.paragraph_format.line_spacing = 1.0
add_run(p, "外贸罗盘", size=22, color=LIME, bold=True)

p = left.add_paragraph()
p.paragraph_format.space_after = Pt(6)
p.paragraph_format.line_spacing = 1.2
add_run(p, "把一次询盘，变成一份可执行的市场判断。", size=10.5, color=WHITE)

p = left.add_paragraph()
p.paragraph_format.space_after = Pt(0)
add_run(p, "外贸市场情报智能体   ·   高级组 · 主题 1 金融经贸", size=8, color=RGBColor(0x9F, 0xB6, 0xCC))

p = right.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(0)
p.add_run().add_picture(str(ASSETS / "score_badge.png"), width=Cm(3.55))

# cover label + abstract
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(12)
p.paragraph_format.space_after = Pt(3)
p.paragraph_format.tab_stops.add_tab_stop(Cm(16.6), WD_TAB_ALIGNMENT.RIGHT)
add_run(p, "项目介绍", size=18, color=NAVY, bold=True)
add_run(p, "   PROJECT INTRODUCTION", size=7.5, color=TEAL, bold=True, name=MONO)
add_run(p, "\t2026.11 · 广州", size=8.5, color=MUTED)
pPr = p._p.get_or_add_pPr()
pBdr = OxmlElement("w:pBdr")
bottom = OxmlElement("w:bottom")
bottom.set(qn("w:val"), "single")
bottom.set(qn("w:sz"), "4")
bottom.set(qn("w:space"), "5")
bottom.set(qn("w:color"), "DCE5DC")
pBdr.append(bottom)
pPr.append(pBdr)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(7)
p.paragraph_format.space_after = Pt(7)
p.paragraph_format.line_spacing = 1.6
add_run(p, "TradeLens 外贸罗盘", size=10.5, color=NAVY, bold=True)
add_run(p, "是一款面向中小外贸团队的市场情报智能体。它把产品、市场、目标价与客户询盘，转成可解释的机会判断和下一步动作。", size=10.5, color=INK)

facts = new_table(1, 3, [5.53, 5.53, 5.53], borders=False)
facts.rows[0].height = Cm(1.7)
facts.rows[0].height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST
for i, (num, label) in enumerate((("5", "个目标市场"), ("5", "大外贸品类"), ("0", "外部 API 依赖"))):
    cell = facts.cell(0, i)
    shade_cell(cell, "F1F6F1")
    set_cell_margins(cell, top=0.18, bottom=0.18, left=0.3, right=0.3)
    set_cell_border(cell, left={"sz": 12, "color": "FFFFFF"}, right={"sz": 12, "color": "FFFFFF"})
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    add_run(p, num, size=20, color=TEAL, bold=True, name=MONO)
    add_run(p, "  " + label, size=8.2, color=MUTED)

shot = new_table(1, 1, [16.6], borders=True)
cell = shot.cell(0, 0)
set_cell_margins(cell, top=0.1, bottom=0.1, left=0.1, right=0.1)
p = cell.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(0)
p.add_run().add_picture(str(ASSETS / "cover_app.png"), width=Cm(16.1))
cap = doc.add_paragraph()
cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
cap.paragraph_format.space_before = Pt(3)
cap.paragraph_format.space_after = Pt(0)
add_run(cap, "市场简报工作台 · 德国 LED 户外庭院灯示例", size=7.6, color=MUTED)

# ------------------------------------------------------------------ body
body = doc.add_section(WD_SECTION.NEW_PAGE)
body.page_width = Cm(21)
body.page_height = Cm(29.7)
body.left_margin = Cm(2.2)
body.right_margin = Cm(2.2)
body.top_margin = Cm(2.0)
body.bottom_margin = Cm(2.0)
body.header_distance = Cm(1.0)
body.footer_distance = Cm(1.0)
body.header.is_linked_to_previous = False
body.footer.is_linked_to_previous = False
sectPr = body._sectPr
pgNumType = OxmlElement("w:pgNumType")
pgNumType.set(qn("w:start"), "1")
sectPr.append(pgNumType)

header = body.header
header.is_linked_to_previous = False
hp = header.paragraphs[0]
hp.paragraph_format.space_after = Pt(3)
hp.paragraph_format.tab_stops.add_tab_stop(Cm(16.6), WD_TAB_ALIGNMENT.RIGHT)
add_run(hp, "TradeLens 外贸罗盘  ·  项目介绍", size=8, color=MUTED, bold=True)
add_run(hp, "\t高级组 · 主题 1 金融经贸", size=8, color=MUTED)
pPr = hp._p.get_or_add_pPr()
pBdr = OxmlElement("w:pBdr")
bottom = OxmlElement("w:bottom")
bottom.set(qn("w:val"), "single")
bottom.set(qn("w:sz"), "4")
bottom.set(qn("w:space"), "4")
bottom.set(qn("w:color"), "DDE5DC")
pBdr.append(bottom)
pPr.append(pBdr)

footer = body.footer
fp = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
fp.paragraph_format.space_before = Pt(0)
add_run(fp, "— ", size=8.5, color=MUTED)
add_page_field(fp)
add_run(fp, " —", size=8.5, color=MUTED)

# page 1 body: overview
heading("01", "项目概览")
para(
    "TradeLens 外贸罗盘把一次新市场判断拆成一条可解释的流水线：输入产品、市场、目标价和本次目标，"
    "系统检索结构化市场卡，计算机会分，输出需求信号、准入合规、竞争渠道、风险提示和 90 天行动清单；"
    "同时可把客户询盘拆成可跟进字段，识别低价、急单和信息缺口，生成英文回复草稿。",
    size=10.5, line=1.7, after=8,
)
callout(
    "“先判断值不值得做，再决定怎么回复。”",
    "市场判断和询盘回复不是两个孤立的聊天任务，而是同一条外贸决策链。TradeLens 把这条链路产品化，"
    "让每个结论都能回到具体字段、具体权重和具体动作。",
)

subhead("目标用户")
users = new_table(1, 3, [5.53, 5.53, 5.53], borders=True)
for i, (title, body_text) in enumerate((
    ("中小外贸企业", "业务员、外贸经理与老板，需要快速判断一个新市场值不值得投入。"),
    ("外贸 SOHO", "一个人承担选品、找客户、报价和跟单，需要可复用的判断框架。"),
    ("渠道与品牌方", "寻找新品类、新市场或新供应商，需要把零散信息变成可比较的结论。"),
)):
    cell = users.cell(0, i)
    shade_cell(cell, "FAFBF8")
    set_cell_margins(cell, top=0.28, bottom=0.28, left=0.3, right=0.3)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(3)
    add_run(p, title, size=10, color=NAVY, bold=True)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    p2.paragraph_format.line_spacing = 1.45
    add_run(p2, body_text, size=8.8, color=MUTED)

subhead("四个真实痛点")
pains = new_table(2, 2, [8.3, 8.3], borders=True)
pain_items = [
    ("01", "信息碎片化", "海关、认证、电商、竞品和聊天记录分散在不同地方，做一次判断要反复切换。"),
    ("02", "判断靠经验", "“市场很大、机会不错”常常只是感觉，缺少可复用的评分框架，难以向团队解释为什么。"),
    ("03", "合规容易漏项", "CE、EPR、WEEE、标签和原产地单证，任何一项缺失都可能影响上架或清关。"),
    ("04", "回复靠手工", "低价、急单、认证缺口混在一封邮件里，容易漏掉真正影响成交的条件。"),
]
for idx, (num, title, body_text) in enumerate(pain_items):
    cell = pains.cell(idx // 2, idx % 2)
    shade_cell(cell, "FAFBF8")
    set_cell_margins(cell, top=0.26, bottom=0.26, left=0.3, right=0.3)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    add_run(p, num + "  ", size=7.5, color=TEAL, bold=True, name=MONO)
    add_run(p, title, size=9.8, color=NAVY, bold=True)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    p2.paragraph_format.line_spacing = 1.45
    add_run(p2, body_text, size=8.8, color=MUTED)

subhead("为什么是现在")
para(
    "大模型降低了文本生成的成本，但外贸决策的瓶颈并不是“写不出”，而是“数字是否可信、合规是否漏项、下一步做什么”。"
    "TradeLens 选择把事实、规则和生成分开：市场卡约束事实，评分公式负责判断，模板负责表达。"
    "这让系统在断网、没有 API Key 的现场也能稳定演示，也让评委可以追问每一个分数的来源。",
    size=10, line=1.65, after=0,
)

# page 2 body: product
heading("02", "产品方案", page_break=True)
para(
    "产品从一个具体任务开始：业务员拿到一个新品或一封询盘，需要在有限时间内判断“这个市场值不值得试、这封询盘要不要跟”。"
    "TradeLens 把这个动作拆成四步，并把结果沉淀成可复用的市场卡。",
    size=10.2, line=1.65, after=8,
)

subhead("四步完成一次市场判断")
steps = new_table(5, 3, [2.0, 6.2, 8.4], borders=True)
headers = ("步骤", "做什么", "得到什么")
for i, h in enumerate(headers):
    cell = steps.cell(0, i)
    shade_cell(cell, "0B172A")
    cell_text(cell, h, size=8.5, color=WHITE, bold=True)
step_rows = [
    ("01", "选择产品、市场、目标价与本次目标", "30 秒内建立分析上下文，避免从空白页开始"),
    ("02", "检索市场卡，匹配价格带与合规要求", "机会分、主流价格带、合规难度"),
    ("03", "按五维权重计算，生成风险与行动", "一份可执行的 90 天试单路径"),
    ("04", "把客户询盘拆成字段，标记冲突点", "优先级、风险提示、英文回复草稿"),
]
for r, (num, action, output) in enumerate(step_rows, start=1):
    for c, value in enumerate((num, action, output)):
        cell = steps.cell(r, c)
        if r % 2 == 0:
            shade_cell(cell, "FAFBF8")
        cell_text(
            cell, value,
            size=8.8 if c else 10,
            color=TEAL if c == 0 else (NAVY if c == 1 else MUTED),
            bold=(c == 0),
            name=MONO if c == 0 else FONT,
        )

subhead("四个核心模块")
mods = new_table(2, 2, [8.3, 8.3], borders=True)
mod_items = [
    ("01 / BRIEF", "市场简报", "5 个市场 × 5 个品类，输出需求信号、合规清单、竞争分层、渠道适配度与行动路径。"),
    ("02 / SCORE", "机会评分", "需求 35% · 价格 25% · 渠道 15% · 竞争 15% · 合规 10%，分数直接对应下一步动作。"),
    ("03 / COMPLIANCE", "准入合规", "关税、增值税、认证、标签、原产地单证，全部拆成可核对的字段。"),
    ("04 / INQUIRY", "询盘解析", "抽取数量、目标价、交期、贸易条款与认证，标记低价、急单和信息缺口。"),
]
for idx, (kicker, title, body_text) in enumerate(mod_items):
    cell = mods.cell(idx // 2, idx % 2)
    shade_cell(cell, "FAFBF8")
    set_cell_margins(cell, top=0.28, bottom=0.28, left=0.32, right=0.32)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    add_run(p, kicker, size=7.2, color=TEAL, bold=True, name=MONO)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(3)
    add_run(p2, title, size=11, color=NAVY, bold=True)
    p3 = cell.add_paragraph()
    p3.paragraph_format.space_after = Pt(0)
    p3.paragraph_format.line_spacing = 1.5
    add_run(p3, body_text, size=8.8, color=MUTED)

subhead("一份简报包含什么")
outputs = new_table(2, 3, [5.53, 5.53, 5.53], borders=True)
output_items = [
    ("结论", "机会分、建议动作、置信边界"),
    ("数据", "增速、进口依赖、主流价格带"),
    ("合规", "关税、VAT、认证、标签、单证"),
    ("竞争", "竞争分层、参考价格、渠道适配"),
    ("风险", "认证、价格、物流、回款风险"),
    ("行动", "0–30 / 30–60 / 60–90 天路径"),
]
for idx, (title, body_text) in enumerate(output_items):
    cell = outputs.cell(idx // 3, idx % 3)
    shade_cell(cell, "F1F6F1")
    set_cell_margins(cell, top=0.22, bottom=0.22, left=0.28, right=0.28)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    add_run(p, title, size=9.2, color=TEAL, bold=True)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    p2.paragraph_format.line_spacing = 1.4
    add_run(p2, body_text, size=8.8, color=INK)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(8)
p.paragraph_format.space_after = Pt(0)
add_run(p, "从“市场很大”到“下周做什么”，一份简报完成闭环。", size=10.5, color=TEAL, bold=True)

# page 3 body: case
heading("03", "演示案例", page_break=True)
para(
    "以“德国 × LED 户外庭院灯 × 目标价 €24.8 × 试单验证”为例。系统在不到一秒内完成检索、评分和行动生成，"
    "并把结论、依据和风险拆开呈现，方便业务员复核。",
    size=10.2, line=1.65, after=8,
)

case = new_table(1, 4, [4.15, 4.15, 4.15, 4.15], borders=True)
case_vals = (("产品", "LED 户外庭院灯"), ("市场", "德国 · EUR"), ("目标价", "€24.8"), ("本次目标", "试单验证"))
for i, (label, value) in enumerate(case_vals):
    cell = case.cell(0, i)
    shade_cell(cell, "0B172A")
    set_cell_margins(cell, top=0.24, bottom=0.24, left=0.3, right=0.3)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    add_run(p, label, size=7.8, color=RGBColor(0xA8, 0xBE, 0xD2))
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    add_run(p2, value, size=10.5, color=WHITE, bold=True)

metrics = new_table(1, 3, [5.53, 5.53, 5.53], borders=True)
metric_vals = (("78 / 100", "机会评分 · 建议试单"), ("€16.6–€33.1", "主流价格带 · 目标价居中"), ("高", "合规难度 · CE / EPR 前置"))
for i, (value, label) in enumerate(metric_vals):
    cell = metrics.cell(0, i)
    shade_cell(cell, "F1F6F1")
    set_cell_margins(cell, top=0.24, bottom=0.24, left=0.3, right=0.3)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    add_run(p, value, size=16 if i == 0 else 13, color=TEAL, bold=True, name=MONO if i == 0 else FONT)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    add_run(p2, label, size=7.8, color=MUTED)

subhead("系统判断")
para(
    "德国是成熟市场，更新替换与能效改造是主逻辑，认证和回收责任决定能否上架。目标价位于主流带内，"
    "但 CE、WEEE、EPR 和德文标签是硬门槛，因此结论不是“直接冲”，而是“建议试单”：先用 1–2 个 SKU 和小批量订单验证渠道、"
    "合规成本与真实复购，再决定是否扩大投入。",
    size=10, line=1.65, after=6,
)

breakdown = new_table(2, 5, [3.32, 3.32, 3.32, 3.32, 3.32], borders=True)
break_head = ("需求 35%", "价格 25%", "渠道 15%", "竞争 15%", "合规 10%")
break_vals = ("86", "88", "86", "65", "18")
for i, h in enumerate(break_head):
    cell = breakdown.cell(0, i)
    shade_cell(cell, "0B172A")
    cell_text(cell, h, size=7.8, color=WHITE, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell2 = breakdown.cell(1, i)
    cell_text(cell2, break_vals[i], size=14, color=TEAL, bold=True, name=MONO, align=WD_ALIGN_PARAGRAPH.CENTER)

add_picture(ROOT / "screenshots" / "inquiry.png", 14.0)

# page 4 body: technology
heading("04", "技术架构", page_break=True)
para(
    "比赛版优先保证稳定、可解释、可演示。前端是原生 HTML / CSS / JavaScript，服务端只使用 Python 标准库，"
    "不需要数据库、API Key、npm 或 pip 安装；现场断网也能完成完整流程。",
    size=10.2, line=1.65, after=6,
)
add_picture(ASSETS / "architecture.png", 14.2, "浏览器只负责输入与呈现；事实、评分与风险规则留在服务端，可逐项复核。")

subhead("关键设计")
design = new_table(2, 2, [8.3, 8.3], borders=True)
design_items = [
    ("01 / STRUCTURE", "结构化市场卡", "把关税、认证、渠道、买家、物流拆成字段，先约束事实，再生成文本，降低幻觉。"),
    ("02 / SCORE", "确定性评分", "五维权重固定、结果可复现；分数不是结论，而是触发下一步动作的开关。"),
    ("03 / PARSE", "规则解析询盘", "数量、价格、交期是强字段，规则比自由生成更稳定，也更容易写测试。"),
    ("04 / OFFLINE", "零依赖运行", "单进程 HTTP 服务，无外部服务依赖；现场演示不受网络和额度影响。"),
]
for idx, (kicker, title, body_text) in enumerate(design_items):
    cell = design.cell(idx // 2, idx % 2)
    shade_cell(cell, "FAFBF8")
    set_cell_margins(cell, top=0.15, bottom=0.15, left=0.3, right=0.3)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    add_run(p, kicker, size=7.2, color=TEAL, bold=True, name=MONO)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(3)
    add_run(p2, title, size=10.5, color=NAVY, bold=True)
    p3 = cell.add_paragraph()
    p3.paragraph_format.space_after = Pt(0)
    p3.paragraph_format.line_spacing = 1.45
    add_run(p3, body_text, size=8.8, color=MUTED)

subhead("质量与稳定性")
quality = new_table(1, 3, [5.53, 5.53, 5.53], borders=True)
quality_vals = (("25", "组品类 × 市场组合"), ("13", "项引擎 / API 测试"), ("0", "外部依赖 / 密钥"))
for i, (value, label) in enumerate(quality_vals):
    cell = quality.cell(0, i)
    shade_cell(cell, "F1F6F1")
    set_cell_margins(cell, top=0.22, bottom=0.22, left=0.3, right=0.3)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(1)
    add_run(p, value, size=18, color=TEAL, bold=True, name=MONO)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    add_run(p2, label, size=7.8, color=MUTED)

para(
    "测试覆盖 25 组组合、价格带、多币种、询盘抽取、风险标记与 API 边界。",
    size=8.8, line=1.45, after=3,
)
callout(
    "数据边界：这是比赛 Demo，不是实时贸易数据库。",
    "市场增速、进口依赖、价格带为示例值；关税、认证、标签和原产地规则会随 HS 编码与目的国法规变化，正式报价前必须复核。",
    fill="FFF8E8", border="D99A23", title_color=AMBER,
)

# page 5 body: value and roadmap
heading("05", "价值与路线", page_break=True)
para(
    "TradeLens 的价值不在于多写一段文案，而在于把外贸决策从“凭感觉”变成“有依据、有下一步”。"
    "对业务员，它是一张可复用的判断底稿；对团队，它是一套统一的检查清单；对赛事，它是一个可解释 AI 的落地样本。",
    size=10.2, line=1.65, after=8,
)

subhead("对应评分维度")
score_table = new_table(4, 4, [3.2, 1.7, 6.2, 5.5], borders=True)
score_head = ("评分维度", "权重", "我们的回答", "证据 / 现场可见")
for i, h in enumerate(score_head):
    cell = score_table.cell(0, i)
    shade_cell(cell, "0B172A")
    cell_text(cell, h, size=8.2, color=WHITE, bold=True)
score_rows = [
    ("技术实现 Tech", "40%", "可运行的双引擎 Web 应用：市场简报 + 询盘解析，API 与前端解耦。", "25 组组合、13 项测试、0 外部依赖、断网可演示。"),
    ("创意与价值 Idea", "30%", "把市场判断和询盘跟进串成一条决策链，而不是单点聊天。", "五维机会分、低价 / 急单风险标记、90 天行动。"),
    ("用户体验 UX", "30%", "三次点击完成简报，图表化呈现，支持打印 / PDF。", "雷达图、价格带、响应式布局、移动端抽屉。"),
]
for r, row_data in enumerate(score_rows, start=1):
    for c, value in enumerate(row_data):
        cell = score_table.cell(r, c)
        if r % 2 == 0:
            shade_cell(cell, "FAFBF8")
        cell_text(
            cell, value,
            size=8.7,
            color=NAVY if c == 0 else (TEAL if c == 1 else MUTED),
            bold=(c == 0),
            align=WD_ALIGN_PARAGRAPH.CENTER if c == 1 else WD_ALIGN_PARAGRAPH.LEFT,
        )

subhead("项目价值")
values = new_table(1, 3, [5.53, 5.53, 5.53], borders=True)
value_items = [
    ("对业务员", "把散落的调研动作压缩成一次输入，先得到一份能拿去讨论的初判。"),
    ("对团队", "统一市场卡、评分口径和合规清单，减少“每个人一套说法”。"),
    ("对赛事", "展示一个可解释、可测试、可离线运行的 AI 落地样本。"),
]
for i, (title, body_text) in enumerate(value_items):
    cell = values.cell(0, i)
    shade_cell(cell, "F1F6F1")
    set_cell_margins(cell, top=0.24, bottom=0.24, left=0.3, right=0.3)
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    add_run(p, title, size=9.5, color=TEAL, bold=True)
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(0)
    p2.paragraph_format.line_spacing = 1.45
    add_run(p2, body_text, size=8.8, color=INK)

subhead("下一步")
roadmap = new_table(4, 2, [3.0, 13.6], borders=True)
roadmap_rows = [
    ("数据层", "接入海关编码 / 关税 API、Google Trends、展会采购商数据、汇率与运价。"),
    ("模型层", "用 LLM 做多语言润色、买家画像总结和邮件个性化，但保留事实校验与评分层。"),
    ("产品层", "增加项目空间、历史版本、团队协作和到岸成本测算。"),
    ("部署层", "部署到国内云服务，增加访问控制、速率限制和监控，提供公开体验链接。"),
]
for r, (label, text) in enumerate(roadmap_rows):
    c0, c1 = roadmap.cell(r, 0), roadmap.cell(r, 1)
    shade_cell(c0, "FAFBF8")
    cell_text(c0, label, size=8.8, color=TEAL, bold=True)
    cell_text(c1, text, size=8.8, color=MUTED)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(14)
p.paragraph_format.space_after = Pt(0)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_run(p, "TradeLens 不替外贸人做决定，它让每个决定都有依据、有下一步。", size=12, color=NAVY, bold=True)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(6)
p.paragraph_format.space_after = Pt(0)
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_run(p, "TradeLens 外贸罗盘  ·  高级组 · 主题 1 金融经贸", size=8, color=MUTED)

OUT.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUT)
print("saved", OUT)
