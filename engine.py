"""TradeLens deterministic market-intelligence engine.

The demo is intentionally offline and dependency-free: every market number and
narrative below is a curated *example*, not a live customs/trend feed. The
engine is designed to be replaceable by real data adapters later.
"""

from __future__ import annotations

import math
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


MARKETS: Dict[str, Dict[str, Any]] = {
    "DE": {
        "name": "德国",
        "region": "欧盟",
        "currency": "EUR",
        "symbol": "€",
        "fx": 0.92,
        "growth": 3.8,
        "import_dependency": 72,
        "ecommerce": 84,
        "tariff": 4.7,
        "vat": 19,
        "compliance_level": 82,
        "certs": ["CE（LVD / EMC）", "RoHS", "WEEE 注册", "EPR / 包装法"],
        "certs_en": ["CE (LVD/EMC)", "RoHS", "WEEE registration", "EPR packaging"],
        "labeling": "德文标签：品名、型号、电压、功率、制造商/进口商、CE 标识",
        "channels": [
            ("专业照明/五金分销商", 88, "客单价稳定，重视认证与交期"),
            ("Amazon.de / OTTO", 82, "适合标准品，需处理 EPR 与退货"),
            ("园林工程与承包商", 76, "项目制，账期较长但复购稳定"),
        ],
        "buyer": "中型专业分销商、园林工程采购",
        "payment": "T/T 30% 定金 + 70% 发货前；成熟客户可谈 30–60 天",
        "logistics": "海运 32–38 天；中欧班列 18–22 天",
        "angle": "成熟市场，更新替换与能效改造是主逻辑，认证和回收责任决定能否上架。",
        "tariff_note": "LED 灯具通常按 HS 9405 申报，具体税率以 CN/HTS 编码为准",
        "risks": [
            "CE 技术文件或 EPR 注册不完整，可能导致下架/罚款",
            "德文标签与包装合规是常见验货卡点",
            "海运旺季舱位与欧元汇率波动会压缩毛利",
        ],
    },
    "US": {
        "name": "美国",
        "region": "北美",
        "currency": "USD",
        "symbol": "$",
        "fx": 1.0,
        "growth": 5.1,
        "import_dependency": 68,
        "ecommerce": 90,
        "tariff": 3.9,
        "vat": 0,
        "compliance_level": 74,
        "certs": ["UL / ETL 列名", "FCC（含无线功能时）", "DOE 能效", "Prop 65"],
        "certs_en": ["UL/ETL listing", "FCC", "DOE energy efficiency", "Prop 65"],
        "labeling": "英文标签：型号、输入参数、UL/ETL 标识、原产地、警告语",
        "channels": [
            ("大型连锁与电商", 90, "起量快，但对价格、包装和售后要求高"),
            ("专业分销商", 80, "重视认证、库存周转与本地支持"),
            ("工程/物业采购", 72, "项目制，偏好有本地案例的供应商"),
        ],
        "buyer": "区域分销商、电商卖家、物业/工程采购",
        "payment": "T/T 30% 定金 + 70% 见提单副本；大客户可谈 Net 30",
        "logistics": "海运 28–35 天；美西港口提柜 3–7 天",
        "angle": "规模大、渠道集中，产品责任与能效合规优先，品牌和售后是溢价来源。",
        "tariff_note": "基础 MFN 税率 3.9%；LED 相关产品可能叠加 301 关税，需按 HTS 核对",
        "risks": [
            "UL/ETL 认证周期与费用容易被低估",
            "301 关税及清关编码差异会显著影响到岸成本",
            "电商退货率和产品责任险要求较高",
        ],
    },
    "AE": {
        "name": "阿联酋",
        "region": "海湾",
        "currency": "AED",
        "symbol": "AED ",
        "fx": 3.67,
        "growth": 7.4,
        "import_dependency": 85,
        "ecommerce": 66,
        "tariff": 5.0,
        "vat": 5,
        "compliance_level": 66,
        "certs": ["ESMA / ECAS", "GCC 符合性", "阿拉伯语标签", "能效标签（适用时）"],
        "certs_en": ["ESMA/ECAS", "GCC conformity", "Arabic labeling", "energy label"],
        "labeling": "阿拉伯语/英语双语标签：型号、电压、功率、原产地、进口商",
        "channels": [
            ("迪拜贸易商/进口商", 90, "覆盖海湾多国，适合首站试水"),
            ("工程项目与酒店采购", 78, "看重交期、安装服务与本地案例"),
            ("Noon / Amazon.ae", 64, "增长快，但价格竞争激烈"),
        ],
        "buyer": "迪拜进口商、工程承包商、酒店/地产采购",
        "payment": "T/T 30% 定金 + 70% 发货前；当地代理常见 30–60 天",
        "logistics": "海运 18–25 天；杰贝阿里港清关 3–5 天",
        "angle": "项目驱动、价格敏感度中等，海湾认证与阿拉伯语包装是进场前提。",
        "tariff_note": "一般进口关税 5%，具体以海湾统一关税税则和 HS 编码为准",
        "risks": [
            "ECAS/GCC 认证与阿拉伯语标签缺一不可",
            "工程客户账期和尾款风险需要提前设计",
            "夏季高温对电池/电源类产品提出额外要求",
        ],
    },
    "VN": {
        "name": "越南",
        "region": "东南亚",
        "currency": "VND",
        "symbol": "₫",
        "fx": 25400.0,
        "growth": 9.2,
        "import_dependency": 55,
        "ecommerce": 58,
        "tariff": 10.0,
        "vat": 10,
        "compliance_level": 58,
        "certs": ["能效标签", "QCVN（适用时）", "越南语标签", "Form E 原产地证"],
        "certs_en": ["energy label", "QCVN", "Vietnamese labeling", "Form E"],
        "labeling": "越南语标签：品名、型号、电压、功率、进口商、原产地",
        "channels": [
            ("本地进口商/批发商", 86, "渠道下沉快，价格谈判强"),
            ("五金与建材门店", 74, "适合走量型标准品"),
            ("Shopee / Lazada", 68, "增长快，但客单价偏低"),
        ],
        "buyer": "胡志明/河内进口商、区域批发商",
        "payment": "T/T 30% 定金 + 70% 发货前；首单建议信用证或信保",
        "logistics": "海运 7–12 天；胡志明/海防港清关 3–5 天",
        "angle": "增量市场，渠道下沉快，性价比与交期比品牌更重要。",
        "tariff_note": "MFN 约 10%；中国-东盟自贸协定下凭 Form E 多数可享优惠税率",
        "risks": [
            "Form E 与标签不合规会失去关税优惠或被退运",
            "本地渠道价格战激烈，首单毛利容易被压缩",
            "越南语售后与安装说明缺失会拉高退货",
        ],
    },
    "MX": {
        "name": "墨西哥",
        "region": "拉美",
        "currency": "MXN",
        "symbol": "MX$",
        "fx": 18.2,
        "growth": 6.3,
        "import_dependency": 70,
        "ecommerce": 62,
        "tariff": 10.0,
        "vat": 16,
        "compliance_level": 64,
        "certs": ["NOM 认证", "ANCE（电气安全）", "西班牙语标签", "原产地规则核查"],
        "certs_en": ["NOM certification", "ANCE", "Spanish labeling", "origin verification"],
        "labeling": "西班牙语标签：型号、电压、功率、进口商、原产地、NOM 标识",
        "channels": [
            ("进口商/区域分销", 84, "覆盖美墨边境与首都圈，适合首单"),
            ("连锁建材与物业", 76, "项目制，重视认证与交付"),
            ("Mercado Libre / Amazon.mx", 66, "增长快，物流与退货是门槛"),
        ],
        "buyer": "墨西哥城/蒙特雷进口商、连锁建材采购",
        "payment": "T/T 30% 定金 + 70% 发货前；中信保可降低首单风险",
        "logistics": "海运 28–35 天；曼萨尼约/拉萨罗港清关 5–8 天",
        "angle": "近岸外包带动工程需求，西语本地化与 NOM 认证是关键。",
        "tariff_note": "一般进口关税约 10%；IMMEX 计划下可递延，需按 HS 与原产地规则核对",
        "risks": [
            "NOM 认证与西语标签不完整会卡关",
            "清关代理与查验效率差异大，需预留缓冲",
            "比索汇率波动会影响定价与回款",
        ],
    },
}


CATEGORIES: Dict[str, Dict[str, Any]] = {
    "led_outdoor": {
        "name": "LED 户外庭院灯",
        "en": "LED outdoor garden light",
        "short": "户外照明",
        "hs": "9405.42",
        "price_low": 18.0,
        "price_high": 36.0,
        "unit": "件",
        "moq": "500–1,000 件",
        "angle": "户外庭院灯正从单纯照明转向“照明 + 安防 + 氛围”，IP65、CRI 与安装便利性是核心卖点。",
        "keywords": ["LED garden light", "IP65", "3000K", "CRI>80", "die-cast aluminum"],
        "drivers": [
            ("能效替换", "欧洲/北美老旧灯具进入替换周期，LED 渗透率继续提升"),
            ("庭院经济", "户外休闲与景观改造带动庭院照明客单价上行"),
            ("智能联动", "感应、调光、太阳能成为差异化卖点"),
        ],
        "competitors": [
            ("本地/欧洲品牌", 1.55, 2.4, "认证齐全、交期短，占高端工程与商超"),
            ("中国出口品牌", 0.95, 1.45, "性价比和款式迭代快，主攻分销与电商"),
            ("本地组装/贸易商", 1.15, 1.8, "小批量灵活，但研发和一致性较弱"),
        ],
        "cert_extra": ["IP65 防护等级测试报告", "光通量/色温/显色指数报告"],
        "risks": [
            "认证与 EPR 等合规成本容易侵蚀首单利润",
            "外观与光效同质化，容易陷入价格战",
            "海运周期与季节备货错配会造成断货",
        ],
    },
    "portable_power": {
        "name": "便携储能电源",
        "en": "portable power station",
        "short": "便携储能",
        "hs": "8507.60",
        "price_low": 180.0,
        "price_high": 420.0,
        "unit": "台",
        "moq": "100–300 台",
        "angle": "户外露营、应急备电与家庭储能共同拉动需求，安全认证、循环寿命和快充是核心决策点。",
        "keywords": ["portable power station", "LiFePO4", "UPS", "solar input", "pure sine wave"],
        "drivers": [
            ("户外露营", "露营与房车场景持续增长，带动 500–2,000Wh 段位"),
            ("应急备电", "极端天气与电网不稳提升家庭备电需求"),
            ("光伏配套", "阳台光伏与便携太阳能板形成组合销售"),
        ],
        "competitors": [
            ("国际头部品牌", 1.8, 2.8, "品牌与渠道强，价格高，认证齐全"),
            ("中国专业品牌", 0.9, 1.5, "供应链完整，性价比和迭代速度占优"),
            ("白牌/贸易商", 0.65, 1.0, "价格低，但安全与售后风险高"),
        ],
        "cert_extra": ["UN38.3 运输测试", "IEC 62133 / UL 2054 电池安全", "MSDS"],
        "risks": [
            "锂电池运输与仓储合规复杂，空运限制多",
            "产品责任与召回风险高，需预留保险成本",
            "价格战与参数虚标会快速损害品牌",
        ],
    },
    "smart_home": {
        "name": "智能家居传感器",
        "en": "smart home sensor",
        "short": "智能家居",
        "hs": "8531.10",
        "price_low": 8.0,
        "price_high": 26.0,
        "unit": "只",
        "moq": "1,000–3,000 只",
        "angle": "Matter/Thread 生态与隐私本地化正在重塑传感器市场，兼容性、功耗和 App 体验决定复购。",
        "keywords": ["Matter", "Thread", "Zigbee", "PIR sensor", "home automation"],
        "drivers": [
            ("生态统一", "Matter/Thread 降低跨品牌接入门槛"),
            ("安防与节能", "人体存在传感器联动照明和空调"),
            ("适老化", "跌倒/离床等场景带来新增量"),
        ],
        "competitors": [
            ("生态型品牌", 1.6, 2.6, "App 与生态体验好，溢价明显"),
            ("中国方案商", 0.85, 1.4, "模组与整机一体化，迭代快"),
            ("本地安防品牌", 1.1, 1.8, "安装服务强，SKU 较少"),
        ],
        "cert_extra": ["无线射频认证（CE RED / FCC ID）", "隐私与数据合规说明"],
        "risks": [
            "无线认证与频段差异导致 SKU 无法通用",
            "App/云服务停服会直接影响售后与口碑",
            "隐私合规和本地数据存储要求趋严",
        ],
    },
    "pet": {
        "name": "宠物智能用品",
        "en": "smart pet product",
        "short": "宠物智能",
        "hs": "8509.80 / 3926.90",
        "price_low": 15.0,
        "price_high": 55.0,
        "unit": "件",
        "moq": "500–1,500 件",
        "angle": "宠物精细化喂养推动智能饮水机、喂食器和摄像头增长，安全、清洁便利与 App 稳定性是关键。",
        "keywords": ["smart pet feeder", "water fountain", "pet camera", "BPA-free"],
        "drivers": [
            ("精细化养宠", "主人愿意为健康监测和自动喂养付费"),
            ("远程互动", "摄像头与双向语音成为刚需"),
            ("内容种草", "短视频平台放大新品曝光效率"),
        ],
        "competitors": [
            ("国际宠物品牌", 1.5, 2.3, "信任度高，渠道广，价格偏贵"),
            ("中国出海品牌", 0.9, 1.5, "产品迭代快，擅长内容营销"),
            ("本地白牌", 0.65, 1.0, "价格低，质量与售后不稳定"),
        ],
        "cert_extra": ["食品接触材料测试（适用时）", "静音/防水测试报告"],
        "risks": [
            "涉水/涉电产品故障率与退货率偏高",
            "宠物安全事件可能引发严重口碑危机",
            "外观专利与侵权风险需要提前检索",
        ],
    },
    "tools": {
        "name": "锂电工具",
        "en": "cordless power tool",
        "short": "锂电工具",
        "hs": "8467.29",
        "price_low": 25.0,
        "price_high": 80.0,
        "unit": "套",
        "moq": "300–800 套",
        "angle": "无绳化与电池平台化持续替代有线工具，兼容性、扭矩和售后网络是渠道最关心的指标。",
        "keywords": ["cordless tool", "brushless motor", "20V battery", "power tool kit"],
        "drivers": [
            ("无绳替代", "专业与家用场景持续从有绳转向无绳"),
            ("电池平台", "一电多用提升复购与客单价"),
            ("DIY 需求", "家居维护与庭院作业带动入门级套装"),
        ],
        "competitors": [
            ("专业工具品牌", 1.7, 2.6, "渠道与售后强，电池生态锁定"),
            ("中国工具品牌", 0.9, 1.4, "性价比高，产品线扩展快"),
            ("本地贴牌商", 0.7, 1.1, "价格低，依赖代工，品质波动"),
        ],
        "cert_extra": ["电池 UN38.3", "工具安规测试", "噪声/振动测试报告"],
        "risks": [
            "电池平台兼容性与专利风险",
            "售后维修网络不足会拖累渠道信心",
            "海运危险品申报与包装要求严格",
        ],
    },
}


GOALS = {
    "trial": {"name": "试单验证", "score_adj": 2, "action": "小批量试单"},
    "distributor": {"name": "寻找分销商", "score_adj": 0, "action": "开发区域分销"},
    "brand": {"name": "品牌出海", "score_adj": -2, "action": "品牌化投入"},
}


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def format_local(amount: float, market: Dict[str, Any]) -> str:
    """Format a value already expressed in the market's local currency."""
    if market["currency"] == "VND":
        return f"{round(amount / 1000) * 1000:,.0f} ₫"
    if market["currency"] == "MXN":
        return f"MX${amount:,.0f}"
    if market["currency"] == "AED":
        return f"AED {amount:,.0f}"
    if market["currency"] == "EUR":
        return f"€{amount:,.1f}"
    return f"${amount:,.1f}"


def money(value_usd: float, market: Dict[str, Any]) -> str:
    """Convert a USD-denominated price band and format it locally."""
    return format_local(value_usd * market["fx"], market)


def _price_fit(target: float, low: float, high: float) -> int:
    """How well a target price sits inside the mainstream band."""
    mid = (low + high) / 2
    if low <= target <= high:
        return int(round(clamp(88 - abs(target - mid) / mid * 18)))
    if target < low:
        return int(round(clamp(58 - (low - target) / low * 55, 12, 60)))
    return int(round(clamp(62 - (target - high) / high * 32, 18, 64)))


def _verdict(score: int) -> Tuple[str, str, str]:
    if score >= 80:
        return "优先进入", "high", "市场信号与价格带匹配度较高，可进入实质谈判。"
    if score >= 68:
        return "建议试单", "medium", "先以 1–2 个 SKU 和小批量订单验证渠道与合规成本。"
    if score >= 58:
        return "谨慎验证", "low", "存在明显不确定性，建议先做样品和小范围询盘测试。"
    return "暂缓", "low", "当前条件下投入产出比不足，建议更换市场或价格定位。"


def _signals(market: Dict[str, Any], category: Dict[str, Any]) -> List[Dict[str, str]]:
    drivers = category["drivers"]
    return [
        {
            "label": "市场增速（示例）",
            "value": f"+{market['growth']:.1f}%",
            "detail": drivers[0][1],
        },
        {
            "label": "进口依赖度",
            "value": f"{market['import_dependency']}/100",
            "detail": "本地供给难以覆盖中低端 SKU，进口与分销仍是主要供给方式。",
        },
        {
            "label": "电商渗透率",
            "value": f"{market['ecommerce']}%",
            "detail": f"{market['channels'][1][0]}适合标准品起量，但需同步准备退货与本地售后。",
        },
        {
            "label": "采购节奏",
            "value": "Q1 / Q3",
            "detail": "春季备货与秋季工程交付是主要节点，建议提前 90 天锁定舱位与认证。",
        },
    ]


def _competitor_rows(market: Dict[str, Any], category: Dict[str, Any]) -> List[Dict[str, str]]:
    rows = []
    for name, low_mul, high_mul, note in category["competitors"]:
        rows.append(
            {
                "name": name,
                "price": f"{money(category['price_low'] * low_mul, market)} – {money(category['price_high'] * high_mul, market)}",
                "note": note,
            }
        )
    return rows


def _compliance_rows(market: Dict[str, Any], category: Dict[str, Any]) -> List[Dict[str, str]]:
    certs = list(market["certs"]) + list(category.get("cert_extra", []))
    return [
        {"item": "进口关税", "value": f"{market['tariff']:.1f}%", "note": market["tariff_note"]},
        {
            "item": "增值税 / 消费税",
            "value": f"{market['vat']}%" if market["vat"] else "按州销售税",
            "note": "报价时需明确含税/未税口径，避免到岸成本误判",
        },
        {"item": "强制 / 核心认证", "value": "、".join(certs[:3]), "note": "以产品功能、HS 编码和目的国法规最终确认"},
        {"item": "标签与包装", "value": market["labeling"], "note": "建议出货前做一次标签合规审核"},
        {"item": "原产地与单证", "value": "CO / Form E / 原产地声明", "note": "核对自贸协定资格，单证不一致可能失去关税优惠"},
    ]


def _actions(market: Dict[str, Any], category: Dict[str, Any], goal: str) -> List[Dict[str, str]]:
    goal_name = GOALS.get(goal, GOALS["trial"])["name"]
    return [
        {
            "window": "0–30 天",
            "title": "锁定 2 个 SKU 与合规包",
            "detail": f"完成 {market['certs'][0]} 与 {category['cert_extra'][0]} 的资料核对，确认目标价 {goal_name} 下的毛利底线。",
        },
        {
            "window": "30–60 天",
            "title": "触达 10 家目标渠道",
            "detail": f"优先联系{market['channels'][0][0]}，用英文/本地语言一页纸报价 + 认证清单换取样品机会。",
        },
        {
            "window": "60–90 天",
            "title": "用一个小单验证到岸成本",
            "detail": f"按 {category['moq']} 的起订量试单，复盘关税、物流、退货与真实复购，不急于扩 SKU。",
        },
        {
            "window": "90 天+",
            "title": "决定是否本地化投入",
            "detail": f"若询盘转化率达标，再评估 {market['region']} 本地仓、品牌注册或独家分销。",
        },
    ]


def analyze_market(
    category_key: str = "led_outdoor",
    market_key: str = "DE",
    target_price: Optional[float] = None,
    goal: str = "trial",
) -> Dict[str, Any]:
    if category_key not in CATEGORIES:
        raise ValueError("未知产品品类")
    if market_key not in MARKETS:
        raise ValueError("未知目标市场")

    market = MARKETS[market_key]
    category = CATEGORIES[category_key]
    low_usd, high_usd = category["price_low"], category["price_high"]
    low = low_usd * market["fx"]
    high = high_usd * market["fx"]
    if target_price is None or target_price <= 0:
        target_price = round((low + high) / 2, 2)
    target_price = float(target_price)

    demand = clamp(45 + market["growth"] * 5 + market["import_dependency"] * 0.30)
    price_fit = _price_fit(target_price, low, high)
    compliance_friendly = clamp(100 - market["compliance_level"])
    channel = clamp(40 + market["ecommerce"] * 0.55)
    competition = 65.0
    raw_score = (
        demand * 0.35
        + price_fit * 0.25
        + channel * 0.15
        + competition * 0.15
        + compliance_friendly * 0.10
        + GOALS.get(goal, GOALS["trial"])["score_adj"]
    )
    score = int(round(clamp(raw_score, 35, 92)))
    verdict, level, verdict_note = _verdict(score)

    price_position = "低于主流带"
    if target_price > high:
        price_position = "高于主流带"
    elif target_price >= low:
        price_position = "位于主流带"

    summary = (
        f"{market['name']} · {category['name']}：{market['angle']}"
        f"{category['angle']} 当前目标价 {format_local(target_price, market)} {price_position}，"
        f"综合机会分 {score}，行动建议为“{verdict}”。"
    )

    metrics = [
        {"label": "市场增速", "value": f"+{market['growth']:.1f}%", "hint": "示例年增速"},
        {"label": "进口依赖", "value": f"{market['import_dependency']}/100", "hint": "越高越依赖进口"},
        {"label": "主流价格带", "value": f"{format_local(low, market)}–{format_local(high, market)}", "hint": f"目标价 {format_local(target_price, market)}"},
        {"label": "合规难度", "value": "高" if market["compliance_level"] >= 75 else ("中" if market["compliance_level"] >= 62 else "中低"), "hint": f"{len(market['certs'])} 项核心要求"},
    ]

    radar = [
        {"label": "需求热度", "value": int(round(demand))},
        {"label": "价格匹配", "value": int(round(price_fit))},
        {"label": "合规友好", "value": int(round(compliance_friendly))},
        {"label": "渠道成熟", "value": int(round(channel))},
        {"label": "竞争空间", "value": int(round(competition))},
    ]

    risks = []
    for i, risk in enumerate((category["risks"] + market["risks"])[:4]):
        risks.append(
            {
                "level": "高" if i == 0 else ("中" if i < 3 else "低"),
                "title": risk,
                "detail": "建议在报价前完成一次专项核查，并写入试单复盘清单。",
            }
        )

    trace = [
        {"step": "01", "name": "解析任务", "detail": f"{category['name']} × {market['name']} × {GOALS.get(goal, GOALS['trial'])['name']}"},
        {"step": "02", "name": "检索市场卡", "detail": f"读取 {market['region']} 关税、认证、渠道与买家画像"},
        {"step": "03", "name": "匹配价格带", "detail": f"目标价对照 {format_local(low, market)}–{format_local(high, market)} 主流带"},
        {"step": "04", "name": "计算机会分", "detail": "需求 35% · 价格 25% · 渠道 15% · 竞争 15% · 合规 10%"},
        {"step": "05", "name": "生成行动清单", "detail": "输出 90 天试单路径与 4 项风险提示"},
    ]

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "data_note": "演示数据：基于公开行业经验整理的示例值，非实时海关/趋势数据；关税与认证请以官方口径复核。",
        "category": {"key": category_key, **category},
        "market": {
            "key": market_key,
            "name": market["name"],
            "region": market["region"],
            "currency": market["currency"],
            "symbol": market["symbol"],
            "buyer": market["buyer"],
            "payment": market["payment"],
            "logistics": market["logistics"],
            "language": {
                "DE": "德语 / 英语",
                "US": "英语（西语渠道补充）",
                "AE": "阿拉伯语 / 英语",
                "VN": "越南语 / 英语",
                "MX": "西班牙语 / 英语",
            }[market_key],
        },
        "input": {"target_price": target_price, "goal": goal, "goal_name": GOALS.get(goal, GOALS["trial"])["name"]},
        "score": score,
        "level": level,
        "verdict": verdict,
        "verdict_note": verdict_note,
        "summary": summary,
        "metrics": metrics,
        "radar": radar,
        "score_breakdown": [
            {"label": "需求", "weight": "35%", "value": int(round(demand))},
            {"label": "价格", "weight": "25%", "value": price_fit},
            {"label": "渠道", "weight": "15%", "value": int(round(channel))},
            {"label": "竞争", "weight": "15%", "value": int(round(competition))},
            {"label": "合规", "weight": "10%", "value": int(round(compliance_friendly))},
        ],
        "signals": _signals(market, category),
        "compliance": _compliance_rows(market, category),
        "competitors": _competitor_rows(market, category),
        "channels": [{"name": n, "fit": fit, "note": note} for n, fit, note in market["channels"]],
        "risks": risks,
        "actions": _actions(market, category, goal),
        "trace": trace,
        "price_band": {"low": low, "high": high, "target": target_price, "position": price_position},
    }


# ---------------------------------------------------------------------------
# Inquiry parsing
# ---------------------------------------------------------------------------

_MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

_CITY_TO_MARKET = {
    "hamburg": "DE", "berlin": "DE", "munich": "DE", "münchen": "DE", "frankfurt": "DE",
    "germany": "DE", "deutschland": "DE",
    "new york": "US", "los angeles": "US", "chicago": "US", "houston": "US",
    "usa": "US", "united states": "US", "u.s.": "US",
    "dubai": "AE", "abu dhabi": "AE", "sharjah": "AE", "uae": "AE",
    "ho chi minh": "VN", "hanoi": "VN", "haiphong": "VN", "vietnam": "VN",
    "mexico city": "MX", "monterrey": "MX", "guadalajara": "MX", "mexico": "MX",
}

_PRODUCT_HINTS = {
    "led_outdoor": ["led", "garden light", "flood light", "庭院灯", "投光灯", "户外灯", "street light"],
    "portable_power": ["power station", "portable power", "储能", "户外电源", "generator", "battery pack"],
    "smart_home": ["sensor", "zigbee", "matter", "smart home", "传感器", "智能家居"],
    "pet": ["pet", "feeder", "fountain", "宠物", "喂食器", "饮水机"],
    "tools": ["drill", "tool", "saw", "工具", "电钻", "锂电"],
}


def _parse_money(text: str) -> Tuple[Optional[float], Optional[str]]:
    patterns = [
        r"(?:target|best|offer|price|报价|目标价)[^\d€$]{0,24}(eur|usd|aed|vnd|mxn|€|\$)?\s*([\d][\d,]*(?:\.\d+)?)",
        r"(eur|usd|aed|vnd|mxn|€|\$)\s*([\d][\d,]*(?:\.\d+)?)",
        r"([\d][\d,]*(?:\.\d+)?)\s*(eur|usd|aed|vnd|mxn|€|\$)",
    ]
    for index, pattern in enumerate(patterns):
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        if index == 0:
            currency, amount = match.groups()
        elif index == 1:
            currency, amount = match.groups()
        else:
            amount, currency = match.groups()
        symbol_map = {"€": "EUR", "$": "USD"}
        normalized_currency = symbol_map.get(currency or "", (currency or "").upper()) or None
        try:
            return float(amount.replace(",", "")), normalized_currency
        except ValueError:
            continue
    return None, None


def _parse_quantity(text: str) -> Optional[int]:
    patterns = [
        r"([\d][\d,]*)\s*(?:pcs|pieces|units|sets|台|件|只|套)",
        r"(?:quantity|qty|数量)[^\d]{0,12}([\d][\d,]*)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return int(m.group(1).replace(",", ""))
            except ValueError:
                pass
    return None


def _parse_deadline(text: str) -> Optional[str]:
    today = date.today()

    # Relative wording: "within 3 weeks", "in 10 days", "3周内".
    relative = re.search(r"(?:within|in|after)\s*(\d{1,3})\s*(day|week|month)s?", text, re.IGNORECASE)
    if not relative:
        relative = re.search(r"(\d{1,3})\s*(天|周|个月)内", text)
    if relative:
        amount = int(relative.group(1))
        unit = relative.group(2).lower()
        if unit in ("day", "天"):
            days = amount
        elif unit in ("week", "周"):
            days = amount * 7
        else:
            days = amount * 30
        return (today + timedelta(days=days)).isoformat()

    # ISO / Chinese numeric date with explicit year.
    match = re.search(r"(20\d{2})[-/年.](\d{1,2})[-/月.](\d{1,2})", text)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3))).isoformat()
        except ValueError:
            return None

    year: Optional[int] = None
    month: Optional[int] = None
    day: Optional[int] = None

    # 15 Jan / 15 January 2027
    match = re.search(r"\b(\d{1,2})\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?(?:\s*,?\s*(20\d{2}))?", text, re.IGNORECASE)
    if match:
        day = int(match.group(1))
        month = _MONTHS[match.group(2).lower()]
        year = int(match.group(3)) if match.group(3) else None

    # Jan 15 / January 15, 2027
    if month is None:
        match = re.search(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s*(\d{1,2})(?:\s*,?\s*(20\d{2}))?", text, re.IGNORECASE)
        if match:
            month = _MONTHS[match.group(1).lower()]
            day = int(match.group(2))
            year = int(match.group(3)) if match.group(3) else None

    # 1月15日 / 1月15号
    if month is None:
        match = re.search(r"(\d{1,2})月(\d{1,2})[日号]", text)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))

    if month is None or day is None:
        return None

    candidate_year = year or today.year
    try:
        candidate = date(candidate_year, month, day)
    except ValueError:
        return None
    if year is None and candidate < today:
        try:
            candidate = date(candidate_year + 1, month, day)
        except ValueError:
            return None
    return candidate.isoformat()


def _parse_market(text: str) -> Optional[str]:
    lower = text.lower()
    for city, market in _CITY_TO_MARKET.items():
        if city in lower:
            return market
    if "德国" in text:
        return "DE"
    if "美国" in text:
        return "US"
    if "阿联酋" in text or "迪拜" in text:
        return "AE"
    if "越南" in text:
        return "VN"
    if "墨西哥" in text:
        return "MX"
    return None


def _parse_category(text: str) -> Optional[str]:
    lower = text.lower()
    for key, hints in _PRODUCT_HINTS.items():
        if any(h in lower for h in hints):
            return key
    return None


def parse_inquiry(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if len(text) < 20:
        raise ValueError("询盘内容过短，至少输入 20 个字符")

    normalized = re.sub(r"\s+", " ", text)
    market_key = _parse_market(normalized) or "DE"
    category_key = _parse_category(normalized) or "led_outdoor"
    market = MARKETS[market_key]
    category = CATEGORIES[category_key]
    quantity = _parse_quantity(normalized)
    price, currency = _parse_money(normalized)
    deadline = _parse_deadline(normalized)
    certs = []
    for cert in ["CE", "RoHS", "REACH", "UL", "ETL", "FCC", "NOM", "ESMA", "GCC", "UN38.3", "IP65", "IP67"]:
        if re.search(rf"\b{re.escape(cert)}\b", normalized, re.IGNORECASE):
            certs.append(cert)
    incoterm = None
    m = re.search(r"\b(EXW|FOB|CIF|CFR|DDP|DAP)\b", normalized, re.IGNORECASE)
    if m:
        incoterm = m.group(1).upper()

    low = category["price_low"] * market["fx"]
    high = category["price_high"] * market["fx"]
    target = price if price else (low + high) / 2
    if currency and currency not in ("", market["currency"]) and price:
        # Convert common currencies to the market currency for comparison.
        fx_to_usd = {"EUR": 1.09, "USD": 1.0, "AED": 0.272, "VND": 0.000039, "MXN": 0.055}.get(currency, 1.0)
        target = price * fx_to_usd * market["fx"]

    lead_score = 60
    flags: List[Dict[str, str]] = []

    if quantity:
        if quantity >= 5000:
            lead_score += 18
            flags.append({"level": "good", "title": "数量明确且具备规模", "detail": f"{quantity:,} 件可作为重点询盘跟进。"})
        elif quantity >= 1000:
            lead_score += 12
            flags.append({"level": "good", "title": "数量达到试单门槛", "detail": f"{quantity:,} 件适合安排样品与阶梯报价。"})
        else:
            lead_score += 3
            flags.append({"level": "info", "title": "首单数量偏小", "detail": "建议确认是否可拼柜，或设置合理的小单附加费。"})
    else:
        flags.append({"level": "warn", "title": "未识别到采购数量", "detail": "回复时先确认数量，否则无法给出有效阶梯价。"})

    if price:
        if target < low:
            lead_score -= 6
            flags.append(
                {
                    "level": "warn",
                    "title": "目标价低于主流带",
                    "detail": f"客户目标价约 {format_local(target, market)}，低于参考带 {format_local(low, market)}–{format_local(high, market)}；可提供简化配置或调整规格。",
                }
            )
        elif target > high:
            lead_score += 4
            flags.append(
                {
                    "level": "good",
                    "title": "目标价高于主流带",
                    "detail": f"客户目标价约 {format_local(target, market)}，高于参考带；可用认证、交期和定制服务支撑溢价。",
                }
            )
        else:
            lead_score += 10
            flags.append(
                {
                    "level": "good",
                    "title": "目标价位于可谈区间",
                    "detail": f"目标价约 {format_local(target, market)}，落在 {format_local(low, market)}–{format_local(high, market)} 主流带内。",
                }
            )
    else:
        flags.append({"level": "info", "title": "未识别到目标价", "detail": "先问清预算区间，再决定是否进入打样。"})

    if deadline:
        days = (date.fromisoformat(deadline) - date.today()).days
        if days < 0:
            flags.append({"level": "warn", "title": "交期已过期", "detail": f"客户希望 {deadline} 前交付，需重新确认时间。"})
        elif days <= 30:
            lead_score -= 5
            flags.append({"level": "warn", "title": "交期偏紧", "detail": f"距离期望交付仅 {days} 天，需确认现货/空运方案。"})
        else:
            flags.append({"level": "good", "title": "交期可规划", "detail": f"距离期望交付约 {days} 天，可安排常规生产与海运。"})
    else:
        flags.append({"level": "info", "title": "未识别到交付时间", "detail": "回复中应主动给出标准交期并询问项目节点。"})

    missing = [c for c in market["certs"][:2] if c.split("（")[0] not in certs]
    if missing:
        flags.append({"level": "info", "title": "认证信息待补", "detail": f"客户未明确 {', '.join(missing)}；报价时附上证书清单可提升专业度。"})
    else:
        lead_score += 4

    if not incoterm:
        flags.append({"level": "info", "title": "贸易条款未明确", "detail": "回复中先按 FOB 报价，并说明可选的 CIF/DDP 方案。"})

    lead_score = int(clamp(lead_score, 30, 96))
    lead_level = "A" if lead_score >= 80 else ("B" if lead_score >= 65 else "C")
    recommended = "优先回复 + 24 小时内报价" if lead_score >= 80 else ("正常跟进 + 补充关键信息" if lead_score >= 65 else "先筛选，避免投入过多打样成本")

    product_display = category["name"]
    product_en = category.get("en", category["name"])
    reply_price = target if target >= low else (low + high) / 2
    reply = f"""Subject: Re: Inquiry for {product_en} — preliminary offer

Dear Purchasing Team,

Thank you for your inquiry. We can support the {product_en} project and are pleased to share a preliminary offer:

- Product: {product_en} ({', '.join(category['keywords'][:3])})
- Quantity: {f"{quantity:,} pcs" if quantity else "to be confirmed"}
- Reference unit price: {format_local(reply_price, market)} / pc {incoterm or "FOB Shenzhen"}
- Lead time: 30–35 days after deposit (to be confirmed against final specification)
- Payment: 30% T/T deposit, 70% before shipment
- Certification: {', '.join(market['certs_en'][:3])}

{"We note your target price. To meet it, we can propose a simplified configuration or a mixed-container plan without compromising safety certification. " if price and target < low else "We are happy to discuss volume-based pricing and sample arrangements. "}Could you please confirm the final specification, destination port and required certification scope? We will then send a formal quotation and sample plan within 2 working days.

Best regards,
[Your name]
[Company]
[Phone / WhatsApp]
"""
    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "data_note": "解析结果为规则引擎演示，关键数字请在报价前人工复核。",
        "lead_score": lead_score,
        "lead_level": lead_level,
        "recommended": recommended,
        "market": market["name"],
        "market_key": market_key,
        "category": category["name"],
        "category_key": category_key,
        "extracted": [
            {"label": "产品", "value": product_display},
            {"label": "数量", "value": f"{quantity:,} 件" if quantity else "未识别"},
            {"label": "目标价", "value": format_local(target, market) if price else "未识别"},
            {"label": "目的地", "value": market["name"]},
            {"label": "期望交付", "value": deadline or "未识别"},
            {"label": "贸易条款", "value": incoterm or "未识别"},
            {"label": "认证要求", "value": "、".join(certs) if certs else "未识别"},
        ],
        "benchmark": {
            "low": format_local(low, market),
            "high": format_local(high, market),
            "target": format_local(target, market) if price else None,
            "position": "低于主流带" if price and target < low else ("高于主流带" if price and target > high else "位于主流带"),
        },
        "flags": flags,
        "reply": reply,
        "next_steps": [
            "24 小时内回复，先确认规格、数量、目的地和认证范围",
            "附上 2–3 张实拍图、认证清单和一页纸报价",
            "若目标价偏低，提供“简化配置/混合柜/阶梯价”三个选项",
        ],
    }


def list_options() -> Dict[str, Any]:
    return {
        "categories": [{"key": k, "name": v["name"], "short": v["short"]} for k, v in CATEGORIES.items()],
        "markets": [
            {"key": k, "name": v["name"], "currency": v["currency"], "symbol": v["symbol"]}
            for k, v in MARKETS.items()
        ],
        "goals": [{"key": k, "name": v["name"]} for k, v in GOALS.items()],
        "disclaimer": "演示数据为离线示例，不构成实时贸易或投资建议。",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(analyze_market("led_outdoor", "DE", 22, "trial"), ensure_ascii=False, indent=2)[:2000])
