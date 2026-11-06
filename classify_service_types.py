import csv
import re
from collections import Counter
from pathlib import Path


DATA_DIR = Path.home() / "Desktop" / "\u7edf\u8ba1\u5efa\u6a21\u539f\u6570\u636e"
INPUT_FILE = DATA_DIR / "government_contract_q1_2025_sample_4500.csv"
OUTPUT_FILE = DATA_DIR / "government_contract_q1_2025_sample_4500_服务类型.csv"


FIELDS_FOR_TEXT = [
    "公告标题",
    "项目名称",
    "采购人名称",
    "代理机构名称",
    "原始供应商名称",
    "采购方式",
    "服务期限",
    "公告正文",
]


def norm_text(value):
    return re.sub(r"\s+", "", value or "")


def extract_main_subject(body):
    body = body or ""
    patterns = [
        r"主要标的名称[:：]\s*([^；;\n\r]+)",
        r"标的名称[:：]\s*([^；;\n\r]+)",
        r"采购品目名称[:：]\s*([^；;\n\r]+)",
        r"采购品目[:：]\s*([^；;\n\r]+)",
    ]
    hits = []
    for pattern in patterns:
        hits.extend(re.findall(pattern, body))
    cleaned = []
    for hit in hits[:8]:
        hit = re.sub(r"采购数量.*$", "", hit)
        hit = re.sub(r"[,，]单价.*$", "", hit)
        hit = norm_text(hit)
        if hit and hit not in cleaned:
            cleaned.append(hit)
    return " ".join(cleaned)


RULES = [
    ("物业管理服务", ["物业管理", "物业服务", "物业费", "后勤物业", "综合物业"]),
    ("保洁服务", ["保洁", "清洁", "卫生保洁", "环境卫生", "垃圾清运", "环卫"]),
    ("安保服务", ["保安", "安保", "安全服务", "安防服务", "门卫", "秩序维护", "巡逻"]),
    ("后勤保障综合服务", ["后勤保障", "后勤服务", "托管服务", "综合保障"]),
    ("餐饮服务", ["餐饮", "食堂", "伙食", "配餐", "供餐", "餐厅运营"]),
    ("食品食材供应/配送", ["食材", "食品", "肉类", "蔬菜", "营养改善", "校园餐", "餐食", "粮油", "农副产品", "屠业", "鲜肉", "配送服务"]),
    ("园林绿化服务/工程", ["园林绿化", "绿化养护", "绿化服务", "绿地养护", "绿化工程", "花卉租摆"]),
    ("车辆维修保养服务", ["车辆维修", "汽车维修", "维修和保养", "定点维修", "保养服务", "车辆保养"]),
    ("车辆加油/能源服务", ["车辆加油", "添加燃料", "汽油", "柴油", "燃油", "加油服务", "充电服务"]),
    ("保险服务", ["车辆保险", "机动车保险", "财产保险", "责任保险", "人寿财产保险", "保险服务"]),
    ("车辆租赁/运输服务", ["车辆租赁", "运输服务", "运输机械租赁", "公务用车租赁", "通勤车", "班车", "校车", "客运服务", "租车服务"]),
    ("车辆采购", ["小型客车", "轿车", "越野车", "救护车", "公务车", "专用车辆", "车辆采购"]),
    ("房屋/场地租赁服务", ["办公楼租赁", "房屋租赁", "场地租赁", "办公场所租赁", "临时办公楼租赁"]),
    ("印刷出版服务", ["印刷", "出版", "宣传册", "画册", "票据打印", "排版", "文印"]),
    ("信息技术服务-软件/系统开发", ["软件开发", "系统开发", "平台建设", "信息系统", "管理系统", "应用系统", "数据库", "政务系统", "数据治理", "数字化", "智能化建设", "软件系统建设", "虚拟仿真", "数字资源"]),
    ("信息技术服务-运维/网络/云服务", ["软件运维", "硬件运维", "系统运维", "网络接入", "网络服务", "云服务", "机房", "信息技术服务", "运行维护", "等保", "安全测评", "视频监控", "光纤租赁", "链路租用", "链路租赁", "政务网"]),
    ("软件产品采购", ["基础软件", "办公软件", "应用软件", "操作系统", "杀毒软件", "数据库软件"]),
    ("咨询评估审计法律服务", ["审计", "资产评估", "评估服务", "法律服务", "法律诉讼", "咨询", "造价咨询", "绩效评价", "可研", "方案编制", "规划编制", "选址论证", "用地报批", "设计服务", "监理", "招标代理"]),
    ("鉴定检测测绘服务", ["司法鉴定", "毒物司法鉴定", "车辆司法鉴定", "检测服务", "测绘", "地质勘测", "勘测服务", "安全检测", "路况检测"]),
    ("会议培训考试服务", ["会议定点", "会议服务", "培训服务", "考试服务", "考务", "会务"]),
    ("文化宣传展陈服务", ["文化馆", "校园文化", "展陈", "陈列馆", "文化补短", "宣传服务", "广告服务", "标识标牌"]),
    ("工程施工/修缮装修", ["房屋修缮", "建筑物修缮", "构筑物修缮", "装修", "装饰", "改造工程", "建设工程", "施工", "维修工程", "路面工程", "街巷亮化", "工程类", "建筑工程", "EPC总承包"]),
    ("医疗设备采购", ["医疗设备", "医用", "CT", "球管", "生理参数", "监护仪", "诊断设备", "医疗器械", "彩色多普勒", "超声诊断", "激光治疗机", "医疗电子票据"]),
    ("医疗卫生服务", ["医疗保健", "卫生服务", "健康服务", "照护专区"]),
    ("仪器仪表/科研设备采购", ["仪器仪表", "雷达", "风廓线雷达", "科研设备", "教学设备", "实训", "实验系统", "沉积系统", "电子技术", "智能交通"]),
    ("厨房设备采购", ["厨房设备", "厨具", "餐厨设备"]),
    ("农资农产品采购", ["复合肥", "农药", "农资", "农残", "速测试剂", "科学施肥", "耕地恢复"]),
    ("服装被装采购", ["服装", "被装", "肩章", "制服", "警服"]),
    ("消防/应急装备采购", ["消防", "灭火", "救援", "应急", "防护服", "防护靴", "救生衣", "抢险"]),
    ("LED/显示音视频设备采购", ["LED", "显示屏", "触控一体机", "投影仪", "音视频", "视频矩阵", "液晶显示器", "显示器"]),
    ("计算机/信息化设备采购", ["台式计算机", "便携式计算机", "笔记本电脑", "服务器", "交换机", "路由器", "终端", "一体机电脑", "计算机"]),
    ("办公设备采购", ["打印机", "复印机", "扫描仪", "多功能一体机", "碎纸机", "传真机", "票据打印机"]),
    ("空调/电器设备采购", ["空调", "电器", "冰箱", "电视", "洗衣机", "冷暖挂机", "柜机", "风扇", "电风扇"]),
    ("家具用具采购", ["办公桌", "办公椅", "文件柜", "保密柜", "沙发", "茶水柜", "会议桌", "会议椅", "家具", "木质架类", "更衣柜"]),
    ("办公耗材采购", ["复印纸", "A4纸", "打印纸", "办公耗材", "硒鼓", "墨盒", "办公用品"]),
    ("图书/文体用品采购", ["图书", "教材", "文体", "体育器材", "健身器材", "乐器"]),
    ("日用物资采购", ["手电筒", "日用品", "生活用品", "物资采购"]),
]


PRIORITY_OVERRIDES = [
    ("信息技术服务-软件/系统开发", ["物业维修资金系统", "物业专项维修资金", "物业资金系统"]),
    ("保洁服务", ["物业保洁", "保洁物业"]),
    ("安保服务", ["物业安保", "安保物业"]),
]


def classify(row):
    body = row.get("公告正文", "") or ""
    subject = extract_main_subject(body)
    title_project = norm_text((row.get("公告标题", "") or "") + " " + (row.get("项目名称", "") or ""))
    combined = " ".join(norm_text(row.get(field, "")) for field in FIELDS_FOR_TEXT)
    haystack = f"{subject} {title_project} {combined}"

    for label, keywords in PRIORITY_OVERRIDES:
        if any(keyword in haystack for keyword in keywords):
            return label

    scores = Counter()
    for label, keywords in RULES:
        for keyword in keywords:
            if keyword in subject:
                scores[label] += 5
            if keyword in title_project:
                scores[label] += 3
            if keyword in combined:
                scores[label] += 1

    if scores:
        # Choose the highest score; RULES order breaks ties through insertion order.
        return scores.most_common(1)[0][0]

    # Fallbacks based on broad procurement wording.
    if any(word in haystack for word in ["服务", "外包", "运营", "维护"]):
        return "其他服务"
    if any(word in haystack for word in ["设备", "采购", "货物", "产品"]):
        return "其他货物采购"
    if any(word in haystack for word in ["工程", "施工", "修缮"]):
        return "工程施工/修缮装修"
    return "其他/无法判定"


def main():
    with INPUT_FILE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    output_fields = list(fieldnames)
    if "服务类型" not in output_fields:
        output_fields.append("服务类型")

    for row in rows:
        label = classify(row)
        row["服务类型"] = label
        if "服务类别" in row:
            row["服务类别"] = label

    with OUTPUT_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=output_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(row["服务类型"] for row in rows)
    print(f"input={INPUT_FILE}")
    print(f"output={OUTPUT_FILE}")
    print(f"rows={len(rows)}")
    print("top_categories:")
    for label, count in counts.most_common(30):
        print(f"{label}\t{count}")


if __name__ == "__main__":
    main()
