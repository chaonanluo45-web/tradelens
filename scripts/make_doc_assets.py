from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

FONT_BD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_RG = "C:/Windows/Fonts/msyh.ttc"
FONT_NUM = "C:/Windows/Fonts/arialbd.ttf"

NAVY = "#0B172A"
TEAL = "#0F766E"
TEAL_BRIGHT = "#2DD4BF"
LIME = "#D9F99D"
MUTED = "#6B7A8F"
LINE = "#DFE7DE"
PAPER = "#F7F9F5"


def font(path, size):
    return ImageFont.truetype(path, size)


# ---------------------------------------------------------------- cover image
src = Image.open(ROOT / "screenshots" / "poster_app_wide.png").convert("RGB")
# 2160x1440 -> 2:1 crop, keeping the hero and composer.
cover = src.crop((0, 0, 2160, 1080))
cover.save(OUT / "cover_app.png", optimize=True)


# ---------------------------------------------------------------- score badge
size = 720
img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)
box = (54, 54, size - 54, size - 54)
draw.arc(box, start=0, end=360, fill=(35, 63, 88, 255), width=26)
draw.arc(box, start=-90, end=190.8, fill=TEAL_BRIGHT, width=26)
# rounded-looking endpoints
for angle in (-90, 190.8):
    import math
    cx = size / 2 + (size / 2 - 54) * math.cos(math.radians(angle))
    cy = size / 2 + (size / 2 - 54) * math.sin(math.radians(angle))
    draw.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), fill=TEAL_BRIGHT)

draw.text((size / 2, 235), "机会评分", font=font(FONT_RG, 30), fill="#A8BED2", anchor="mm")
draw.text((size / 2, 355), "78", font=font(FONT_NUM, 190), fill="#FFFFFF", anchor="mm")
draw.text((size / 2, 475), "/ 100", font=font(FONT_NUM, 30), fill="#8AA3BA", anchor="mm")
draw.text((size / 2, 548), "建议试单", font=font(FONT_BD, 38), fill=LIME, anchor="mm")
img.save(OUT / "score_badge.png")


# ---------------------------------------------------------------- architecture
W, H = 1600, 540
img = Image.new("RGB", (W, H), PAPER)
draw = ImageDraw.Draw(img)
draw.text((52, 30), "五步智能体流水线", font=font(FONT_BD, 34), fill=NAVY)
draw.text((W - 52, 42), "EXPLAINABLE BY DESIGN", font=font(FONT_NUM, 15), fill=TEAL, anchor="ra")

steps = [
    ("01", "解析任务", "产品 × 市场 × 价格"),
    ("02", "检索市场卡", "关税 / 认证 / 渠道"),
    ("03", "五维评分", "需求 · 价格 · 合规"),
    ("04", "生成行动", "90 天试单路径"),
    ("05", "询盘解析", "实体抽取 + 回复"),
]
box_w, box_h, gap = 268, 154, 34
start_x = (W - (box_w * 5 + gap * 4)) // 2
y = 116
for i, (num, title, sub) in enumerate(steps):
    x = start_x + i * (box_w + gap)
    draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=14, fill="#FFFFFF", outline=LINE, width=2)
    draw.rounded_rectangle((x, y, x + box_w, y + 7), radius=3, fill=TEAL_BRIGHT)
    draw.text((x + 20, y + 24), num, font=font(FONT_NUM, 17), fill=TEAL)
    draw.text((x + 20, y + 56), title, font=font(FONT_BD, 29), fill=NAVY)
    draw.text((x + 20, y + 103), sub, font=font(FONT_RG, 18), fill=MUTED)
    if i < 4:
        ax = x + box_w + 7
        draw.line((ax, y + box_h / 2, ax + gap - 14, y + box_h / 2), fill=TEAL, width=2)
        draw.polygon([
            (ax + gap - 12, y + box_h / 2),
            (ax + gap - 22, y + box_h / 2 - 6),
            (ax + gap - 22, y + box_h / 2 + 6),
        ], fill=TEAL)

# bottom band
draw.rounded_rectangle((52, 315, W - 52, 438), radius=12, fill="#EAF3EE")
draw.text((78, 341), "浏览器", font=font(FONT_BD, 22), fill=NAVY)
draw.text((78, 377), "原生 HTML / CSS / JavaScript", font=font(FONT_RG, 17), fill=MUTED)
draw.text((520, 351), "JSON API", font=font(FONT_BD, 20), fill=TEAL)
draw.text((520, 384), "analyze / inquiry", font=font(FONT_NUM, 15), fill=MUTED)
draw.text((900, 341), "Python 标准库引擎", font=font(FONT_BD, 22), fill=NAVY)
draw.text((900, 377), "市场卡 · 评分公式 · 风险规则 · 回复模板", font=font(FONT_RG, 17), fill=MUTED)
draw.text((W - 78, 366), "0 外部依赖", font=font(FONT_BD, 24), fill=TEAL, anchor="ra")
draw.text((W - 78, 398), "断网可演示", font=font(FONT_RG, 15), fill=MUTED, anchor="ra")

draw.text((52, 476), "输入在浏览器完成，事实与规则留在服务端；评分与风险均可回到具体字段复核。", font=font(FONT_RG, 18), fill="#5E6F7F")

img.save(OUT / "architecture.png", optimize=True)

print("saved", OUT / "cover_app.png", OUT / "score_badge.png", OUT / "architecture.png")
