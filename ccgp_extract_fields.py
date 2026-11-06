# -*- coding: utf-8 -*-
import argparse
import csv
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup


DATA_DIR = Path(r"C:\Users\22672\Desktop\统计建模原数据")
SEARCH_URL = "https://search.ccgp.gov.cn/bxsearch"
SOURCE = "中国政府采购网"
CATEGORY = "物业管理服务"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://search.ccgp.gov.cn/bxsearch",
}


@dataclass
class NoticePair:
    index: int
    award_title: str
    award_url: str
    purchase_title: str = ""
    purchase_url: str = ""
    project_id_hint: str = ""
    project_name_hint: str = ""


def log(message: str) -> None:
    print(time.strftime("[%H:%M:%S]"), message, flush=True)


def build_search_url(page_index: int, bid_type: str, kw: str = "物业", project_id: str = "") -> str:
    params = {
        "searchtype": "1",
        "page_index": str(page_index),
        "bidSort": "2",
        "buyerName": "",
        "projectId": project_id,
        "pinMu": "3",
        "bidType": bid_type,
        "dbselect": "bidx",
        "kw": kw,
        "start_time": "2025:04:30",
        "end_time": "2026:04:30",
        "timeType": "6",
        "displayZone": "",
        "zoneId": "",
        "pppStatus": "0",
        "agentName": "",
    }
    return f"{SEARCH_URL}?{urlencode(params)}"


def is_rate_limited(html: str) -> bool:
    return "您的访问过于频繁" in html or "频繁访问" in html[:500]


def fetch(session: requests.Session, url: str, retries: int = 4) -> str:
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, headers=HEADERS, timeout=45)
            response.encoding = response.apparent_encoding or "utf-8"
            html = response.text
            if not is_rate_limited(html):
                return html
            wait = min(240, 45 * attempt)
            log(f"触发频控，等待 {wait} 秒后重试")
            time.sleep(wait)
        except requests.RequestException as exc:
            wait = min(120, 20 * attempt)
            log(f"请求失败，等待 {wait} 秒后重试：{exc}")
            time.sleep(wait)
    raise RuntimeError(f"无法读取网页：{url}")


def visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True).replace("\xa0", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def parse_search_results(html: str, page_index: int) -> list[NoticePair]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[NoticePair] = []
    base = (page_index - 1) * 20
    for i, item in enumerate(soup.select("ul.vT-srch-result-list-bid li"), start=1):
        a = item.find("a", href=True)
        if not a:
            continue
        rows.append(
            NoticePair(
                index=base + i,
                award_title=a.get_text(" ", strip=True).replace(" ", ""),
                award_url=a["href"],
            )
        )
    return rows


def load_manifest(path: Path) -> dict[int, NoticePair]:
    pairs: dict[int, NoticePair] = {}
    if not path.exists():
        return pairs
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status") != "完成":
                continue
            idx = int(row["index"])
            pairs[idx] = NoticePair(
                index=idx,
                award_title=row.get("award_title", ""),
                award_url=row.get("award_url", ""),
                purchase_title=row.get("purchase_title", ""),
                purchase_url=row.get("purchase_url", ""),
                project_id_hint=row.get("project_id", ""),
                project_name_hint=row.get("project_name", ""),
            )
    return pairs


def lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" ：:\t\r\n")


def get_after_label(text: str, labels: list[str], skip: set[str] | None = None, max_lookahead: int = 8) -> str:
    skip = skip or set()
    ls = lines(text)
    for i, line in enumerate(ls):
        for label in labels:
            if label not in line:
                continue
            tail = clean_value(line.split(label, 1)[-1])
            if tail and tail not in skip and not tail.endswith("："):
                return tail
            for nxt in ls[i + 1 : i + 1 + max_lookahead]:
                value = clean_value(nxt)
                if value and value not in skip and not value.endswith("："):
                    return value
    return ""


def extract_publish_date(text: str) -> str:
    match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日\s*\d{1,2}:\d{2}", text)
    if not match:
        match = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if not match:
        return ""
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def clean_project_code(value: str) -> str:
    value = clean_value(value)
    value = re.split(r"[，,；;\s]", value)[0]
    value = value.rstrip("。")
    return value if re.search(r"[A-Za-z0-9]", value) else ""


def extract_project_code(text: str, fallback: str = "") -> str:
    ls = lines(text)
    for i, line in enumerate(ls):
        if "采购计划编号" in line:
            continue
        if "项目编号" not in line and "项目号" not in line:
            continue
        tail = clean_project_code(re.sub(r"^.*?(项目编号|项目号)[：:\s]*", "", line))
        if tail:
            return tail
        for nxt in ls[i + 1 : i + 6]:
            if "采购计划编号" in nxt or "项目名称" in nxt:
                continue
            candidate = clean_project_code(nxt)
            if candidate:
                return candidate
    return fallback


def extract_project_name(text: str, fallback: str = "") -> str:
    value = get_after_label(text, ["采购项目名称", "项目名称"], skip={"品目"})
    if value:
        return value
    title = fallback
    return re.sub(r"中标（成交）结果公告|中标结果公告|中标公告|成交公告|结果公告", "", title)


def extract_supplier(text: str) -> str:
    inline = re.search(r"供应商名称[：:\s]*([^\n；;，,]+(?:公司|中心|院|所|厂|集团|有限合伙|合作社))", text)
    if inline:
        return clean_value(inline.group(1))
    skip = {
        "社会信用代码", "供应商地址", "供应商联系电话", "中标金额", "中标（成交）金额",
        "评审总得分", "供应商名称", "地址", "联系电话",
    }
    ls = lines(text)
    for i, line in enumerate(ls):
        if "供应商名称" in line:
            for nxt in ls[i + 1 : i + 24]:
                value = clean_value(nxt)
                if value in skip or "统一社会信用代码" in value:
                    continue
                if any(word in value for word in ["公司", "中心", "院", "所", "厂", "集团", "合作社"]):
                    return value
    return ""


def parse_amount(value: str) -> float | None:
    value = value.replace(",", "")
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(万元|万|元)?", value)
    if not match:
        return None
    number = float(match.group(1))
    unit = match.group(2) or ""
    if "万" in unit:
        number *= 10000
    return round(number, 2)


def extract_amount(text: str, labels: list[str]) -> float | None:
    compact = re.sub(r"\s+", "", text)
    candidates: list[float] = []
    for label in labels:
        pattern = rf"{re.escape(label)}[：:]?([￥¥]?[0-9,]+(?:\.[0-9]+)?(?:万元|万|元)?)"
        match = re.search(pattern, compact)
        if match:
            amount = parse_amount(match.group(1))
            if amount is not None:
                candidates.append(amount)
    ls = lines(text)
    for i, line in enumerate(ls):
        if any(label in line for label in labels):
            window = " ".join(ls[i : i + 4])
            amount = parse_amount(window)
            if amount is not None:
                candidates.append(amount)
    for amount in candidates:
        if amount != 0:
            return amount
    return candidates[0] if candidates else None


def extract_service_period(text: str) -> str:
    labels = ["合同履行期限", "服务期限", "服务时间", "履约期限"]
    header_words = {
        "服务范围", "服务要求", "服务时间", "服务标准", "标的名称", "品目名称",
        "数量", "单价(元)/费率（%）/折扣（折）", "总价(元)", "是否中小企业",
        "中小企业（中型/小型/微型）", "优惠产品简要描述",
    }
    time_words = ["年", "天", "合同", "服务期", "期限", "预计", "签订", "续签", "个月", "详见招标文件", "详见采购文件"]
    ls = lines(text)
    for i, line in enumerate(ls):
        if not any(label in line for label in labels):
            continue
        tail = clean_value(re.sub(r"^.*?(合同履行期限|服务期限|服务时间|履约期限)[：:\s]*", "", line))
        candidates = [tail] + [clean_value(x) for x in ls[i + 1 : i + 14]]
        for value in candidates:
            if not value or value in header_words or value.endswith("："):
                continue
            if "公告期限" in value or "自本公告发布" in value:
                continue
            if any(word in value for word in time_words):
                return value[:180]
    return ""


PROVINCES = [
    "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江", "江苏", "浙江", "安徽",
    "福建", "江西", "山东", "河南", "湖北", "湖南", "广东", "海南", "四川", "贵州", "云南", "陕西",
    "甘肃", "青海", "台湾", "内蒙古", "广西", "西藏", "宁夏", "新疆", "香港", "澳门"
]

CITY_TO_PROVINCE = {
    "苏州": "江苏", "太仓": "江苏", "张家港": "江苏", "无锡": "江苏", "南京": "江苏", "泰州": "江苏",
    "宿迁": "江苏", "南通": "江苏", "深圳": "广东", "银川": "宁夏", "阜阳": "安徽", "重庆": "重庆",
}


def infer_region(text: str, title: str) -> tuple[str, str]:
    admin = get_after_label(text, ["行政区域"], max_lookahead=3)
    source = f"{title}\n{text}"
    province = ""
    city = ""
    for prov in PROVINCES:
        if prov in admin or f"{prov}省" in source or f"{prov}市" in source or f"{prov}自治区" in source:
            province = prov
            break
    for city_key, prov in CITY_TO_PROVINCE.items():
        if city_key in source:
            city = f"{city_key}市"
            province = province or prov
            break
    if not city and admin:
        city = admin if admin.endswith("市") else ""
    return province, city


def extract_method(purchase_title: str, purchase_text: str) -> str:
    source = f"{purchase_title}\n{purchase_text}"
    if "公开招标" in source:
        return "公开招标"
    if "磋商" in source:
        return "竞争性磋商"
    if "谈判" in source:
        return "竞争性谈判"
    for method in ["询价", "单一来源", "邀请招标"]:
        if method in source:
            return method
    return ""


def simplify_for_search(title: str, project_name: str) -> str:
    value = project_name or title
    value = re.sub(r"中标（成交）结果公告|中标结果公告|中标公告|成交公告|结果公告|的|关于", "", value)
    return value[:60] or "物业"


def find_purchase_notice(session: requests.Session, project_code: str, project_name: str, award_title: str, delay: int) -> NoticePair | None:
    searches: list[tuple[str, str]] = []
    if project_code:
        searches.append(("物业", project_code))
        searches.append((project_code, ""))
    searches.append((simplify_for_search(award_title, project_name), ""))
    seen: set[str] = set()
    for kw, pid in searches:
        key = f"{kw}|{pid}"
        if key in seen:
            continue
        seen.add(key)
        log(f"搜索采购公告：kw={kw or '-'} projectId={pid or '-'}")
        html = fetch(session, build_search_url(1, "1", kw=kw, project_id=pid))
        time.sleep(delay + random.uniform(0, 2))
        results = parse_search_results(html, 1)
        if results:
            return results[0]
    return None


def amount_to_cell(value: float | None) -> str:
    return "" if value is None else f"{value:.2f}"


def make_row(session: requests.Session, pair: NoticePair, delay: int) -> dict[str, str]:
    award_html = fetch(session, pair.award_url)
    award_text = visible_text(award_html)
    project_code = extract_project_code(award_text, pair.project_id_hint)
    project_name = extract_project_name(award_text, pair.project_name_hint or pair.award_title)

    purchase_url = pair.purchase_url
    purchase_title = pair.purchase_title
    purchase_text = ""
    if not purchase_url:
        purchase = find_purchase_notice(session, project_code, project_name, pair.award_title, delay)
        if purchase:
            purchase_url = purchase.award_url
            purchase_title = purchase.award_title
    if purchase_url:
        purchase_text = visible_text(fetch(session, purchase_url))

    title = BeautifulSoup(award_html, "html.parser").title.get_text(strip=True)
    publish_date = extract_publish_date(award_text)
    province, city = infer_region(award_text, title)
    buyer_name = get_after_label(award_text, ["采购单位"], skip={"采购单位"})
    agency_name = get_after_label(award_text, ["代理机构名称"], skip={"代理机构名称"})
    supplier_name = extract_supplier(award_text)
    winning_amount = extract_amount(award_text, ["总中标金额", "中标（成交）金额", "中标金额", "成交金额", "投标总报价"])
    budget_amount = extract_amount(purchase_text, ["预算金额", "采购预算", "项目预算", "最高限价"])
    price_ratio = None
    discount_rate = None
    if winning_amount is not None and budget_amount not in (None, 0):
        price_ratio = winning_amount / budget_amount
        discount_rate = 1 - price_ratio

    return {
        "id": str(pair.index),
        "title": title or pair.award_title,
        "url": pair.award_url,
        "publish_date": publish_date,
        "province": province,
        "city": city,
        "project_code": project_code,
        "project_name": project_name,
        "buyer_name": buyer_name,
        "agency_name": agency_name,
        "supplier_name": supplier_name,
        "budget_amount": amount_to_cell(budget_amount),
        "winning_amount": amount_to_cell(winning_amount),
        "price_ratio": "" if price_ratio is None else f"{price_ratio:.6f}",
        "discount_rate": "" if discount_rate is None else f"{discount_rate:.6f}",
        "procurement_method": extract_method(purchase_title, purchase_text) or extract_method(pair.award_title, award_text),
        "service_period": extract_service_period(purchase_text) or extract_service_period(award_text),
        "category": CATEGORY,
        "announcement_text": award_text,
        "source": SOURCE,
    }


def gather_pairs(session: requests.Session, data_dir: Path, start_index: int, max_items: int, delay: int) -> list[NoticePair]:
    pairs = load_manifest(data_dir / "下载清单.csv")
    needed_end = start_index + max_items - 1
    page_start = (start_index - 1) // 20 + 1
    page_end = (needed_end - 1) // 20 + 1
    for page in range(page_start, page_end + 1):
        html = fetch(session, build_search_url(page, "7", kw="物业"))
        time.sleep(delay + random.uniform(0, 2))
        for pair in parse_search_results(html, page):
            pairs.setdefault(pair.index, pair)
    return [pairs[i] for i in range(start_index, needed_end + 1) if i in pairs]


FIELDS = [
    "id", "title", "url", "publish_date", "province", "city", "project_code", "project_name",
    "buyer_name", "agency_name", "supplier_name", "budget_amount", "winning_amount",
    "price_ratio", "discount_rate", "procurement_method", "service_period", "category",
    "announcement_text", "source",
]


def read_existing_rows(output: Path, overwrite: bool) -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    if output.exists() and not overwrite:
        with output.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("id"):
                    merged[row["id"]] = row
    return merged


def write_rows(output: Path, merged: dict[str, dict[str, str]]) -> Path:
    sorted_rows = [merged[key] for key in sorted(merged, key=lambda value: int(value))]
    target = output
    try:
        with target.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(sorted_rows)
    except PermissionError:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        target = output.with_name(f"{output.stem}_备用_{stamp}{output.suffix}")
        with target.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(sorted_rows)
        log(f"原 CSV 可能被 Excel/WPS 占用，已写入备用文件：{target}")
    return target


def append_failure(data_dir: Path, pair: NoticePair, error: Exception) -> None:
    path = data_dir / "字段抽取失败日志.csv"
    exists = path.exists()
    with path.open("a", encoding="utf-8-sig", newline="") as f:
        fields = ["time", "id", "title", "url", "error"]
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "id": pair.index,
                "title": pair.award_title,
                "url": pair.award_url,
                "error": repr(error),
            }
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="从中国政府采购网公告正文抽取建模字段为 CSV")
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    parser.add_argument("--output", default=str(DATA_DIR / "政府采购物业样本字段.csv"))
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--max-items", type=int, default=7)
    parser.add_argument("--delay", type=int, default=18)
    parser.add_argument("--overwrite", action="store_true", help="覆盖输出文件；默认按 id 增量合并")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    session = requests.Session()
    pairs = gather_pairs(session, data_dir, args.start_index, args.max_items, args.delay)
    log(f"准备抽取 {len(pairs)} 条样本")
    output = Path(args.output)
    merged = read_existing_rows(output, args.overwrite)
    target = output
    for pair in pairs:
        log(f"抽取第 {pair.index} 条：{pair.award_title}")
        try:
            row = make_row(session, pair, args.delay)
            merged[row["id"]] = row
            target = write_rows(output, merged)
            log(f"已保存第 {pair.index} 条，当前累计 {len(merged)} 条")
        except Exception as exc:
            log(f"第 {pair.index} 条失败，已记录并继续：{exc}")
            append_failure(data_dir, pair, exc)
        time.sleep(3 + random.uniform(0, 1.5))
    log(f"已生成：{target}，当前累计 {len(merged)} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
