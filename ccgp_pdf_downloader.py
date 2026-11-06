import argparse
import csv
import random
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup


SEARCH_URL = "https://search.ccgp.gov.cn/bxsearch"
DEFAULT_OUTPUT = Path(r"C:\Users\22672\Desktop\统计建模原数据")
CHROME_CANDIDATES = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://search.ccgp.gov.cn/bxsearch",
    "Upgrade-Insecure-Requests": "1",
}


@dataclass
class Notice:
    title: str
    url: str
    summary: str = ""
    index: int = 0


def log(message: str) -> None:
    print(time.strftime("[%H:%M:%S]"), message, flush=True)


def sanitize_filename(name: str, limit: int = 130) -> str:
    name = re.sub(r"[\\/:*?\"<>|]", "_", name)
    name = re.sub(r"\s+", "", name)
    name = name.strip("._ ")
    return (name[:limit] or "未命名")


def find_chrome() -> Path:
    for path in CHROME_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("没有找到 Chrome 或 Edge 可执行文件。")


def soup_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    return soup.title.get_text(strip=True) if soup.title else ""


def is_rate_limited(html: str) -> bool:
    title = soup_title(html)
    return title.startswith("频繁访问") or "您的访问过于频繁" in html


def fetch(session: requests.Session, url: str, retries: int = 4, timeout: int = 45) -> str:
    for attempt in range(1, retries + 1):
        try:
            response = session.get(url, headers=HEADERS, timeout=timeout)
            response.encoding = response.apparent_encoding or "utf-8"
            html = response.text
            if not is_rate_limited(html):
                return html
            wait = min(300, 45 * attempt)
            log(f"触发频控，等待 {wait} 秒后重试：{url}")
            time.sleep(wait)
        except requests.RequestException as exc:
            wait = min(120, 20 * attempt)
            log(f"请求失败，等待 {wait} 秒后重试：{exc}")
            time.sleep(wait)
    raise RuntimeError(f"多次请求失败或被频控：{url}")


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


def parse_search_results(html: str) -> list[Notice]:
    soup = BeautifulSoup(html, "html.parser")
    results: list[Notice] = []
    for item in soup.select("ul.vT-srch-result-list-bid li"):
        a = item.find("a", href=True)
        if not a:
            continue
        title = a.get_text(" ", strip=True).replace(" ", "")
        summary = item.get_text(" ", strip=True)
        results.append(Notice(title=title, url=a["href"], summary=summary))
    return results


def get_page_results(session: requests.Session, page_index: int, delay: float) -> list[Notice]:
    url = build_search_url(page_index=page_index, bid_type="7", kw="物业")
    log(f"读取中标公告搜索页：第 {page_index} 页")
    html = fetch(session, url)
    time.sleep(delay + random.uniform(0, 2))
    notices = parse_search_results(html)
    base = (page_index - 1) * 20
    for i, notice in enumerate(notices, start=1):
        notice.index = base + i
    return notices


def visible_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text("\n", strip=True).replace("\xa0", " ")


def extract_project_id(text: str, summary: str = "") -> str:
    source = f"{text}\n{summary}"
    lines = [line.strip() for line in source.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        if "采购计划编号" in line:
            continue
        if "项目编号" in line:
            tail = re.sub(r"^.*?项目编号[：:\s]*", "", line).strip()
            if looks_like_project_id(tail) and "项目名称" not in tail:
                return clean_project_id(tail)
            for next_line in lines[i + 1 : i + 6]:
                if "项目名称" in next_line or "采购计划编号" in next_line:
                    continue
                if looks_like_project_id(next_line):
                    return clean_project_id(next_line)
    patterns = [
        r"项目编号[：:\s]*([A-Za-z0-9][A-Za-z0-9()（）\-/_.]+)",
        r"项目号[：:\s]*([A-Za-z0-9][A-Za-z0-9()（）\-/_.]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, source)
        if match:
            return clean_project_id(match.group(1))
    return ""


def clean_project_id(value: str) -> str:
    value = value.strip()
    value = re.split(r"[，,；;\s]", value)[0]
    value = value.rstrip("。")
    return value


def looks_like_project_id(value: str) -> bool:
    value = clean_project_id(value)
    if not value or value in {"：", ":", "编号", "项目编号"}:
        return False
    return bool(re.search(r"[A-Za-z0-9]", value))


def extract_project_name(text: str, fallback_title: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for i, line in enumerate(lines):
        if "项目名称" in line:
            tail = re.sub(r"^.*?项目名称[：:\s]*", "", line).strip()
            if tail and not tail.startswith("品目"):
                return tail
            for next_line in lines[i + 1 : i + 4]:
                if next_line not in {"三、中标（成交）信息", "品目"}:
                    return next_line
    return fallback_title


def print_pdf(chrome: Path, url: str, pdf_path: Path) -> bool:
    if pdf_path.exists() and pdf_path.stat().st_size > 20_000:
        log(f"已存在，跳过打印：{pdf_path.name}")
        return True
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = pdf_path.with_suffix(".tmp.pdf")
    if tmp_path.exists():
        tmp_path.unlink()
    cmd = [
        str(chrome),
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-extensions",
        f"--print-to-pdf={tmp_path}",
        url,
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    for _ in range(30):
        if tmp_path.exists() and tmp_path.stat().st_size > 10_000:
            tmp_path.replace(pdf_path)
            return True
        time.sleep(1)
    if tmp_path.exists():
        tmp_path.replace(pdf_path)
    return pdf_path.exists() and pdf_path.stat().st_size > 10_000


def simplify_title_for_search(title: str, project_name: str) -> str:
    text = project_name or title
    text = re.sub(r"中标（成交）结果公告|中标\\(成交\\)结果公告|中标结果公告|中标公告|成交公告|结果公告", "", text)
    text = re.sub(r"关于|的", "", text)
    return text.strip()[:60] or "物业"


def find_purchase_notice(
    session: requests.Session,
    project_id: str,
    project_name: str,
    title: str,
    delay: float,
) -> Notice | None:
    searches: list[tuple[str, str]] = []
    if project_id:
        searches.append(("物业", project_id))
        searches.append((project_id, ""))
    keyword = simplify_title_for_search(title, project_name)
    searches.append((keyword, ""))

    seen: set[str] = set()
    for kw, pid in searches:
        key = f"{kw}|{pid}"
        if key in seen:
            continue
        seen.add(key)
        url = build_search_url(page_index=1, bid_type="1", kw=kw, project_id=pid)
        log(f"搜索采购公告：kw={kw or '-'} projectId={pid or '-'}")
        html = fetch(session, url)
        time.sleep(delay + random.uniform(0, 2))
        results = parse_search_results(html)
        if results:
            return results[0]
    return None


def append_manifest(path: Path, row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    fields = [
        "index",
        "project_id",
        "project_name",
        "award_title",
        "award_url",
        "award_pdf",
        "purchase_title",
        "purchase_url",
        "purchase_pdf",
        "status",
    ]
    with path.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def process_notice(
    session: requests.Session,
    chrome: Path,
    notice: Notice,
    output_dir: Path,
    manifest: Path,
    search_delay: float,
    visit_delay: float,
) -> None:
    log(f"处理第 {notice.index} 条：{notice.title}")
    award_html = fetch(session, notice.url)
    text = visible_text(award_html)
    project_id = extract_project_id(text, notice.summary)
    project_name = extract_project_name(text, notice.title)
    name_prefix = sanitize_filename(project_name or notice.title)
    if project_id:
        name_prefix = sanitize_filename(f"{project_id}_{name_prefix}")

    award_pdf = output_dir / f"{name_prefix}_中标公告.pdf"
    award_ok = print_pdf(chrome, notice.url, award_pdf)
    time.sleep(visit_delay + random.uniform(0, 1.5))

    purchase_title = ""
    purchase_url = ""
    purchase_pdf = ""
    status = "中标公告已保存" if award_ok else "中标公告打印失败"

    purchase = find_purchase_notice(session, project_id, project_name, notice.title, search_delay)
    if purchase:
        purchase_title = purchase.title
        purchase_url = purchase.url
        purchase_pdf_path = output_dir / f"{name_prefix}_采购公告.pdf"
        purchase_ok = print_pdf(chrome, purchase.url, purchase_pdf_path)
        purchase_pdf = str(purchase_pdf_path) if purchase_ok else ""
        status = "完成" if award_ok and purchase_ok else "采购公告打印失败"
    else:
        status = f"{status}; 未找到采购公告"

    append_manifest(
        manifest,
        {
            "index": str(notice.index),
            "project_id": project_id,
            "project_name": project_name,
            "award_title": notice.title,
            "award_url": notice.url,
            "award_pdf": str(award_pdf) if award_ok else "",
            "purchase_title": purchase_title,
            "purchase_url": purchase_url,
            "purchase_pdf": purchase_pdf,
            "status": status,
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="下载中国政府采购网物业中标公告及对应采购公告 PDF")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="PDF 保存目录")
    parser.add_argument("--start-index", type=int, default=5, help="从搜索结果总序号开始处理，默认跳过前四条")
    parser.add_argument("--max-items", type=int, default=10, help="本次最多处理多少条")
    parser.add_argument("--page-start", type=int, default=1, help="开始页码")
    parser.add_argument("--page-end", type=int, default=115, help="结束页码")
    parser.add_argument("--search-delay", type=float, default=18.0, help="搜索请求之间的等待秒数")
    parser.add_argument("--visit-delay", type=float, default=4.0, help="公告页打印后的等待秒数")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output)
    manifest = output_dir / "下载清单.csv"
    chrome = find_chrome()
    log(f"使用浏览器：{chrome}")
    log(f"输出目录：{output_dir}")

    session = requests.Session()
    processed = 0
    for page in range(args.page_start, args.page_end + 1):
        notices = get_page_results(session, page, args.search_delay)
        if not notices:
            log(f"第 {page} 页没有解析到结果，跳过。")
            continue
        for notice in notices:
            if notice.index < args.start_index:
                continue
            if processed >= args.max_items:
                log("达到本次处理数量上限。")
                return 0
            try:
                process_notice(
                    session,
                    chrome,
                    notice,
                    output_dir,
                    manifest,
                    args.search_delay,
                    args.visit_delay,
                )
                processed += 1
            except Exception as exc:
                log(f"第 {notice.index} 条处理失败：{exc}")
                append_manifest(
                    manifest,
                    {
                        "index": str(notice.index),
                        "project_id": "",
                        "project_name": "",
                        "award_title": notice.title,
                        "award_url": notice.url,
                        "award_pdf": "",
                        "purchase_title": "",
                        "purchase_url": "",
                        "purchase_pdf": "",
                        "status": f"失败：{exc}",
                    },
                )
    log(f"本次完成 {processed} 条。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
