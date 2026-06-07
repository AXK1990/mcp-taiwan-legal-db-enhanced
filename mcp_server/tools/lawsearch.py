"""司法院法令判解系統查詢工具（legal.judicial.gov.tw/FINT）

流程：
  1. GET default.aspx → 取得 ASP.NET VIEWSTATE
  2. POST default.aspx 帶 txtKW → 回傳含 iframe 的 HTML，
     左側清單有各分類 ty 代碼與筆數
  3. GET qryresultlst.aspx?ty={ty}&q={hash} → 結果清單
  4. GET data.aspx?ty={ty}&id={id} → 單筆全文
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING

import httpx
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from mcp_server.cache.db import CacheDB
    from mcp_server.tools.waf_bypass import JudicialWAFBypass

logger = logging.getLogger(__name__)

_BASE        = "https://legal.judicial.gov.tw/FINT"
_SEARCH_URL  = f"{_BASE}/default.aspx"
_RESULT_URL  = f"{_BASE}/qryresultlst.aspx"
_DATA_URL    = f"{_BASE}/data.aspx"

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# ty 代碼 ↔ 中文名稱
TY_NAMES: dict[str, str] = {
    "JCC": "憲法法庭裁判",
    "CD":  "大法官解釋",
    "T":   "大法官不受理決議",
    "C":   "司法解釋",
    "J2":  "大法庭專區",
    "J1":  "停止適用之判例",
    "J":   "精選裁判",
    "D":   "決議",
    "Q":   "法律問題",
    "E":   "行政函釋",
}
TY_CODES = {v: k for k, v in TY_NAMES.items()}   # 中文 → 代碼

# 進階查詢 - 文件類型對應表（基於實際測試）
# 格式：{"顯示名稱": {"name": "表單參數名", "value": "表單參數值"}}
DOC_TYPE_ADVANCED = {
    "民事決議":   {"name": "dtype", "value": "A"},
    "刑事決議":   {"name": "dtype", "value": "B"},
    "家事決議":   {"name": "dtype", "value": "UA"},
    "行政決議":   {"name": "dtype", "value": "C"},
    # 未來可擴充：大法官解釋、精選裁判等
}

_ADVANCED_URL = f"{_BASE}/Default_AD.aspx"  # 進階查詢頁面


class LawSearchClient:
    """司法院法令判解系統查詢用戶端"""

    def __init__(self, cache: "CacheDB", waf: "JudicialWAFBypass"):
        self._cache = cache
        self._waf   = waf
        self._base_headers = {
            "User-Agent":      _USER_AGENT,
            "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
            "Referer":         _SEARCH_URL,
        }

    async def close(self) -> None:
        pass  # httpx.AsyncClient 每次查詢自行建立/關閉

    # ------------------------------------------------------------------
    # 公開介面
    # ------------------------------------------------------------------

    async def search(
        self,
        keyword: str,
        doc_type: str = "",
        max_results: int = 20,
        offset: int = 0,
    ) -> dict:
        """搜尋法令判解資料庫

        Args:
            keyword:     關鍵字（法院名稱、裁判案號、案由、全文檢索字詞）
            doc_type:    資料類型，可填中文名稱或 ty 代碼；空白 = 全部類型合併回傳
            max_results: 最多回傳筆數（上限 200）
            offset:      跳過前幾筆（分頁用，每頁 20 筆）

        Returns:
            {success, keyword, doc_type, categories, total_count, results, cached, timestamp}
            categories：各分類名稱與筆數清單
        """
        if not keyword.strip():
            return {"success": False, "error": "請提供搜尋關鍵字"}

        max_results = min(max_results, 200)
        offset = max(offset, 0)

        cache_key = {"src": "lawsearch", "keyword": keyword, "doc_type": doc_type, "offset": offset, "max": max_results}
        cached = await self._cache.get_search(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        from mcp_server.tools.waf_bypass import get_with_waf_retry

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
                headers=self._base_headers,
                cookies=self._waf.get_cookies(),
            ) as client:

                # ── Step 1：GET 取 VIEWSTATE ──────────────────────────
                r1 = await get_with_waf_retry(client, _SEARCH_URL, self._waf)
                r1.raise_for_status()

                soup1  = BeautifulSoup(r1.text, "html.parser")
                vs     = soup1.find("input", {"name": "__VIEWSTATE"})
                ev     = soup1.find("input", {"name": "__EVENTVALIDATION"})
                vg     = soup1.find("input", {"name": "__VIEWSTATEGENERATOR"})

                if not vs:
                    return {
                        "success": False,
                        "error": "無法取得 ASP.NET 表單 token（網站結構可能已變動）",
                        "timestamp": datetime.now().isoformat(),
                    }

                form_data = {
                    "__VIEWSTATE":          vs["value"],
                    "__EVENTVALIDATION":    ev["value"] if ev else "",
                    "__VIEWSTATEGENERATOR": vg["value"] if vg else "",
                    "__VIEWSTATEENCRYPTED": "",
                    "txtKW":                keyword,
                    "ctl00$cp_content$btnSimpleQry": "送出查詢",
                }

                # ── Step 2：POST 送出查詢 ─────────────────────────────
                r2 = await get_with_waf_retry(
                    client, _SEARCH_URL, self._waf,
                    method="POST", data=form_data,
                )
                r2.raise_for_status()

                soup2 = BeautifulSoup(r2.text, "html.parser")

                # 解析左側分類清單（各 ty 的筆數）
                categories = self._parse_categories(soup2)

                # 取得預設 iframe 的 ty 與 q
                iframe = soup2.find("iframe", id="iframe-data")
                if not iframe or not iframe.get("src"):
                    return {
                        "success": True,
                        "keyword": keyword,
                        "doc_type": doc_type or "全部",
                        "categories": categories,
                        "total_count": 0,
                        "results": [],
                        "cached": False,
                        "timestamp": datetime.now().isoformat(),
                    }

                iframe_src  = iframe["src"]
                q_match     = re.search(r"q=([0-9a-f]+)", iframe_src)
                q_hash      = q_match.group(1) if q_match else ""

                # 決定要查哪些 ty
                if doc_type:
                    # 支援中文名稱或直接傳代碼
                    ty_code = TY_CODES.get(doc_type) or (doc_type if doc_type in TY_NAMES else None)
                    if not ty_code:
                        return {
                            "success": False,
                            "error": f"不認識的資料類型：{doc_type}，"
                                     f"可用值：{', '.join(TY_NAMES.values())}",
                        }
                    ty_list = [ty_code]
                else:
                    # 依分類筆數排序，只查有結果的類型
                    ty_list = [
                        cat["ty"] for cat in categories
                        if cat["count"] > 0
                    ]

                # ── Step 3：GET 各 ty 的結果清單 ─────────────────────
                all_results: list[dict] = []
                total_count = 0

                for ty in ty_list:
                    if len(all_results) >= max_results:
                        break
                    remaining = max_results - len(all_results)
                    items, subtotal = await self._fetch_result_list(
                        client, ty, q_hash, remaining, offset=offset,
                    )
                    total_count += subtotal
                    all_results.extend(items)

                data = {
                    "success":     True,
                    "keyword":     keyword,
                    "doc_type":    doc_type or "全部",
                    "categories":  categories,
                    "total_count": total_count,
                    "results":     all_results[:max_results],
                    "cached":      False,
                    "timestamp":   datetime.now().isoformat(),
                }

                if all_results:
                    await self._cache.set_search(cache_key, data)

                return data

        except Exception as exc:
            logger.error("法令判解搜尋失敗: %s", exc)
            return {
                "success":   False,
                "error":     str(exc),
                "timestamp": datetime.now().isoformat(),
            }

    async def search_advanced(
        self,
        keyword: str = "",
        date_from: str = "",
        date_to: str = "",
        doc_types: list[str] | None = None,
        max_results: int = 20,
        offset: int = 0,
    ) -> dict:
        """進階查詢法令判解資料庫（支援日期範圍和精確類型篩選）

        Args:
            keyword:     關鍵字（選填）
            date_from:   起始日期，格式：民國年/月/日（如 "77/1/1"）
            date_to:     結束日期，格式：民國年/月/日（如 "77/12/31"）
            doc_types:   文件類型列表（如 ["民事決議", "刑事決議"]），None = 全部類型
            max_results: 最多回傳筆數（上限 200）
            offset:      跳過前幾筆（分頁用）

        Returns:
            {success, query, categories, total_count, results, cached, timestamp}
        """
        max_results = min(max_results, 200)
        offset = max(offset, 0)

        # 解析日期
        year_from = month_from = day_from = ""
        year_to = month_to = day_to = ""

        if date_from:
            parts = date_from.split("/")
            if len(parts) == 3:
                year_from, month_from, day_from = parts

        if date_to:
            parts = date_to.split("/")
            if len(parts) == 3:
                year_to, month_to, day_to = parts

        # 建立快取鍵
        cache_key = {
            "src": "lawsearch_advanced",
            "keyword": keyword,
            "date_from": date_from,
            "date_to": date_to,
            "doc_types": ",".join(doc_types) if doc_types else "all",
            "offset": offset,
            "max": max_results,
        }
        cached = await self._cache.get_search(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        from mcp_server.tools.waf_bypass import get_with_waf_retry

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
                headers=self._base_headers,
                cookies=self._waf.get_cookies(),
            ) as client:

                # ── Step 1：GET 取 VIEWSTATE ──────────────────────────
                r1 = await get_with_waf_retry(client, _ADVANCED_URL, self._waf)
                r1.raise_for_status()

                soup1 = BeautifulSoup(r1.text, "html.parser")
                vs = soup1.find("input", {"name": "__VIEWSTATE"})
                ev = soup1.find("input", {"name": "__EVENTVALIDATION"})
                vg = soup1.find("input", {"name": "__VIEWSTATEGENERATOR"})

                if not vs:
                    return {
                        "success": False,
                        "error": "無法取得 ASP.NET 表單 token（網站結構可能已變動）",
                        "timestamp": datetime.now().isoformat(),
                    }

                # ── Step 2：建立表單參數 ─────────────────────────────
                form_data = {
                    "__VIEWSTATE": vs["value"],
                    "__EVENTVALIDATION": ev["value"] if ev else "",
                    "__VIEWSTATEGENERATOR": vg["value"] if vg else "",
                    "__VIEWSTATEENCRYPTED": "",
                    "txtKW": keyword,
                    "txtKT": "",
                    "txtYear": "",
                    "sltWords": "常用字別",
                    "txtCase": "",
                    "txtNo": "",
                    "txtY1": year_from,
                    "txtM1": month_from,
                    "txtD1": day_from,
                    "txtY2": year_to,
                    "txtM2": month_to,
                    "txtD2": day_to,
                    "sdate": "",
                    "edate": "",
                    "ctl00$cp_content$btnQry": "送出查詢",
                }

                # 分析並驗證 doc_types 參數
                filter_by_ty = []  # 用 ty 代碼篩選（後篩選）

                if doc_types:
                    for doc_type in doc_types:
                        # 檢查是否為 TY_NAMES 中的類型（如「決議」）
                        if doc_type in TY_CODES:
                            ty_code = TY_CODES[doc_type]
                            filter_by_ty.append(ty_code)
                        # 檢查是否為 DOC_TYPE_ADVANCED 中的細分類型（如「民事決議」）
                        elif doc_type in DOC_TYPE_ADVANCED:
                            mapping = DOC_TYPE_ADVANCED[doc_type]
                            param_name = mapping["name"]
                            param_value = mapping["value"]

                            # 如果該參數名已存在，檢查是否需要多值
                            if param_name in form_data:
                                # 已存在的處理：這裡需要特殊處理
                                # httpx 的 data 參數支援 list 表示多值
                                if not isinstance(form_data[param_name], list):
                                    form_data[param_name] = [form_data[param_name]]
                                form_data[param_name].append(param_value)
                            else:
                                form_data[param_name] = param_value
                        else:
                            # 無效的類型，報錯
                            valid_general = list(TY_NAMES.values())
                            valid_specific = list(DOC_TYPE_ADVANCED.keys())
                            return {
                                "success": False,
                                "error": f"不支援的文件類型：{doc_type}。\n"
                                         f"有效的概括類型：{', '.join(valid_general)}\n"
                                         f"有效的細分類型：{', '.join(valid_specific)}",
                                "timestamp": datetime.now().isoformat(),
                            }

                # ── Step 3：POST 送出查詢 ─────────────────────────────
                r2 = await get_with_waf_retry(
                    client, _ADVANCED_URL, self._waf,
                    method="POST", data=form_data,
                )
                r2.raise_for_status()

                soup2 = BeautifulSoup(r2.text, "html.parser")

                # 解析左側分類清單（各 ty 的筆數）
                categories = self._parse_categories(soup2)

                # 取得預設 iframe 的 ty 與 q
                iframe = soup2.find("iframe", id="iframe-data")
                if not iframe or not iframe.get("src"):
                    return {
                        "success": True,
                        "query": {
                            "keyword": keyword,
                            "date_from": date_from,
                            "date_to": date_to,
                            "doc_types": doc_types or "全部",
                        },
                        "categories": categories,
                        "total_count": 0,
                        "results": [],
                        "cached": False,
                        "timestamp": datetime.now().isoformat(),
                    }

                iframe_src = iframe["src"]
                q_match = re.search(r"q=([0-9a-f]+)", iframe_src)
                q_hash = q_match.group(1) if q_match else ""

                # 決定要查哪些 ty
                if filter_by_ty:
                    # 如果指定了概括類型（如「決議」），只查詢對應的 ty
                    ty_list = [ty for ty in filter_by_ty if any(cat["ty"] == ty and cat["count"] > 0 for cat in categories)]
                else:
                    # 否則依分類筆數排序，查所有有結果的類型
                    ty_list = [
                        cat["ty"] for cat in categories
                        if cat["count"] > 0
                    ]

                # ── Step 4：GET 各 ty 的結果清單 ─────────────────────
                all_results: list[dict] = []
                total_count = 0

                for ty in ty_list:
                    if len(all_results) >= max_results:
                        break
                    remaining = max_results - len(all_results)
                    items, subtotal = await self._fetch_result_list(
                        client, ty, q_hash, remaining, offset=offset,
                    )
                    total_count += subtotal
                    all_results.extend(items)

                data = {
                    "success": True,
                    "query": {
                        "keyword": keyword,
                        "date_from": date_from,
                        "date_to": date_to,
                        "doc_types": doc_types or "全部",
                    },
                    "categories": categories,
                    "total_count": total_count,
                    "results": all_results[:max_results],
                    "cached": False,
                    "timestamp": datetime.now().isoformat(),
                }

                if all_results:
                    await self._cache.set_search(cache_key, data)

                return data

        except Exception as exc:
            logger.error("進階法令判解搜尋失敗: %s", exc)
            return {
                "success": False,
                "error": str(exc),
                "timestamp": datetime.now().isoformat(),
            }

    async def get_document(self, ty: str, doc_id: str) -> dict:
        """取得單筆全文

        Args:
            ty:     資料類型代碼（如 CD、JCC、D、Q…）
            doc_id: 文件 ID（如 D,812 或 JCC,115,審裁,665）

        Returns:
            {success, ty, id, title, full_text, url, cached, timestamp}
        """
        if not ty or not doc_id:
            return {"success": False, "error": "請同時提供 ty 和 doc_id"}

        cache_key = {"src": "lawsearch_doc", "ty": ty, "id": doc_id}
        cached = await self._cache.get_search(cache_key)
        if cached:
            cached["cached"] = True
            return cached

        from mcp_server.tools.waf_bypass import get_with_waf_retry
        from urllib.parse import quote

        url = f"{_DATA_URL}?ty={ty}&id={quote(doc_id, safe=',')}"

        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                follow_redirects=True,
                headers=self._base_headers,
                cookies=self._waf.get_cookies(),
            ) as client:
                r = await get_with_waf_retry(client, url, self._waf)
                r.raise_for_status()

            result = self._parse_document(r.text, ty, doc_id, url)
            if result.get("success"):
                await self._cache.set_search(cache_key, result)
            return result

        except Exception as exc:
            logger.error("法令判解取得全文失敗: %s", exc)
            return {"success": False, "error": str(exc), "url": url}

    # ------------------------------------------------------------------
    # 內部：取得結果清單
    # ------------------------------------------------------------------

    async def _fetch_result_list(
        self,
        client: httpx.AsyncClient,
        ty: str,
        q_hash: str,
        max_items: int,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """GET qryresultlst.aspx?ty={ty}&q={hash}&page=N 並解析結果，支援分頁

        每頁固定 20 筆，page 從 1 開始。
        offset 是要跳過的筆數（例如 offset=20 從第2頁開始）。
        """
        from mcp_server.tools.waf_bypass import get_with_waf_retry

        PAGE_SIZE = 20
        start_page = (offset // PAGE_SIZE) + 1
        skip_in_page = offset % PAGE_SIZE

        all_items: list[dict] = []
        total = 0
        page = start_page
        MAX_PAGES = 50

        while len(all_items) < max_items and page <= MAX_PAGES:
            url = f"{_RESULT_URL}?ty={ty}&q={q_hash}&sort=DS&page={page}&ot=in"
            try:
                r = await get_with_waf_retry(client, url, self._waf)
                if r.status_code != 200:
                    logger.warning("法令判解結果清單 HTTP %d: ty=%s page=%d",
                                   r.status_code, ty, page)
                    break
            except Exception as exc:
                logger.warning("法令判解結果清單失敗: ty=%s page=%d %s", ty, page, exc)
                break

            items, subtotal = self._parse_result_list(r.text, ty, PAGE_SIZE)

            if total == 0 and subtotal > 0:
                total = subtotal

            if not items:
                break

            # 第一頁要跳過 skip_in_page 筆
            if page == start_page and skip_in_page > 0:
                items = items[skip_in_page:]

            all_items.extend(items)

            if len(items) < PAGE_SIZE:
                # 最後一頁
                break

            page += 1

        return all_items[:max_items], total

    # ------------------------------------------------------------------
    # HTML 解析
    # ------------------------------------------------------------------

    def _parse_categories(self, soup: BeautifulSoup) -> list[dict]:
        """解析左側分類清單

        HTML 結構：
        <ul>
          <li class="active">
            <a href="qryresultlst.aspx?ty=JCC&q=..." data-code="JCC" target="iframe-data">
              憲法法庭裁判<span class="badge">76</span>
            </a>
          </li>
          ...
        </ul>
        """
        categories = []
        panel = soup.find("div", id="result-count")
        if not panel:
            return categories

        for li in panel.find_all("li"):
            a = li.find("a")
            if not a:
                continue
            badge = a.find("span", class_="badge")
            count_str = badge.get_text(strip=True).replace(",", "") if badge else "0"
            try:
                count = int(count_str)
            except ValueError:
                count = 0

            name = a.get_text(strip=True)
            if badge:
                name = name.replace(badge.get_text(strip=True), "").strip()

            ty_code = a.get("data-code", "")
            if not ty_code:
                # 從 href 抓 ty 參數
                href = a.get("href", "")
                m = re.search(r"ty=([^&]+)", href)
                ty_code = m.group(1) if m else ""

            categories.append({
                "ty":    ty_code,
                "name":  name,
                "count": count,
            })

        return categories

    def _parse_result_list(
        self, html: str, ty: str, max_items: int
    ) -> tuple[list[dict], int]:
        """解析 qryresultlst.aspx 的結果清單 HTML

        實際結構（已確認）：
        <table class="int-table">
          <tr>
            <td>1.</td>
            <td></td>
            <td>
              <div class="row">
                <div class="col-th">會議次別：</div>
                <div class="col-td"><a href="data.aspx?id=...">標題</a></div>
              </div>
              <div class="row">
                <div class="col-th">會議日期：</div>
                <div class="col-td">民國 100 年 11 月 16 日</div>
              </div>
              <div class="row">
                <div class="col-th">問題要旨：</div>
                <div class="col-td text-pre">摘要文字</div>
              </div>
            </td>
          </tr>
          ...
        </table>

        分頁：共 N 筆，現在第 P/T 頁，「下一頁」連結在 <a> 含「下一頁」文字
        """
        soup = BeautifulSoup(html, "html.parser")
        results: list[dict] = []

        # 找 <table class="int-table">
        table = soup.find("table", class_="int-table")
        if not table:
            table = soup.find("table")

        if table:
            for row in table.find_all("tr"):
                item = self._parse_int_table_row(row, ty)
                if item:
                    results.append(item)
                if len(results) >= max_items:
                    break

        # fallback：直接找所有 data.aspx 連結
        if not results:
            for a in soup.find_all("a", href=re.compile(r"data\.aspx")):
                item = self._parse_link(a, ty)
                if item:
                    results.append(item)
                if len(results) >= max_items:
                    break

        # 估算總筆數：找「共 N 筆」
        total = len(results)
        total_el = soup.find(string=re.compile(r"共\s*\d[\d,]*\s*筆"))
        if total_el:
            m = re.search(r"(\d[\d,]*)", total_el)
            if m:
                total = int(m.group(1).replace(",", ""))

        return results, total

    def _parse_int_table_row(self, row, ty: str) -> dict | None:
        """從 int-table 的 <tr> 解析一筆結果

        每個 <tr> 的第3個 <td> 包含多個 <div class="row">，
        每個 row 有 col-th（欄位名）和 col-td（內容）。
        連結在第一個 col-td 的 <a>。
        """
        cells = row.find_all("td", recursive=False)
        if len(cells) < 3:
            return None

        content_cell = cells[2]  # 第3個 td 是內容
        rows_divs = content_cell.find_all("div", class_="row")
        if not rows_divs:
            return None

        title  = ""
        href   = ""
        date   = ""
        summary = ""

        for div_row in rows_divs:
            th = div_row.find("div", class_="col-th")
            td = div_row.find("div", class_=re.compile(r"\bcol-td\b"))
            if not th or not td:
                continue

            key = th.get_text(strip=True).rstrip("：: ")
            val = td.get_text(strip=True)

            # 標題連結（第一個 row 的 col-td 含 <a>）
            if not title:
                a = td.find("a", href=re.compile(r"data\.aspx"))
                if a:
                    title = a.get_text(strip=True)
                    href  = a.get("href", "")

            # 日期欄位
            if key in ("會議日期", "發文日期", "裁判日期", "解釋日期"):
                date = val

            # 摘要欄位（問題要旨 / 案由摘要 / 裁判要旨 / 解釋爭點）
            if key in ("問題要旨", "案由摘要", "裁判要旨", "解釋爭點", "決議要旨"):
                summary = val[:800]

        if not title or not href:
            return None

        if not href.startswith("http"):
            href = f"{_BASE}/{href.lstrip('/')}"

        doc_id = self._extract_id(href)

        return {
            "doc_type": TY_NAMES.get(ty, ty),
            "title":    title,
            "date":     date,
            "summary":  summary,
            "ty":       ty,
            "id":       doc_id,
            "url":      href,
        }

    def _parse_table_row(self, row, ty: str) -> dict | None:
        """舊版 table row 解析（保留作 fallback）"""
        cells = row.find_all("td")
        if len(cells) < 2:
            return None
        link = row.find("a", href=re.compile(r"data\.aspx"))
        if not link:
            return None
        title = link.get_text(strip=True)
        href  = link.get("href", "")
        if not href.startswith("http"):
            href = f"{_BASE}/{href.lstrip('/')}"
        doc_id = self._extract_id(href)
        row_text = row.get_text(" ", strip=True)
        date_m = re.search(
            r"民國\s*\d{2,3}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", row_text
        )
        date = date_m.group(0) if date_m else ""
        return {
            "doc_type": TY_NAMES.get(ty, ty),
            "title":    title,
            "date":     date,
            "summary":  "",
            "ty":       ty,
            "id":       doc_id,
            "url":      href,
        }

    def _parse_container(self, container, ty: str) -> dict | None:
        """從 div/li 容器解析一筆結果"""
        link = container.find("a", href=re.compile(r"data\.aspx"))
        if not link:
            return None
        return self._parse_link(link, ty, container)

    def _parse_link(self, link, ty: str, context=None) -> dict | None:
        """從 <a> 連結解析一筆結果"""
        title = link.get_text(strip=True)
        if not title:
            return None

        href = link.get("href", "")
        if not href.startswith("http"):
            href = f"{_BASE}/{href.lstrip('/')}"

        doc_id  = self._extract_id(href)
        date    = ""
        summary = ""

        # 從周圍文字取日期與摘要
        parent = context or link.parent
        if parent:
            text = parent.get_text(" ", strip=True)
            # 只取「民國 XXX 年 XX 月 XX 日」格式
            date_m = re.search(
                r"民國\s*\d{2,3}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日", text
            )
            if date_m:
                date = date_m.group(0)
            # 案由摘要
            summary_m = re.search(r"案由摘要[：:]\s*(.+?)(?=\s{2,}|$)", text)
            if summary_m:
                summary = summary_m.group(1).strip()[:300]

        return {
            "doc_type": TY_NAMES.get(ty, ty),
            "title":    title,
            "date":     date,
            "summary":  summary,
            "ty":       ty,
            "id":       doc_id,
            "url":      href,
        }

    def _extract_id(self, url: str) -> str:
        """從 URL 中取出 id 參數"""
        from urllib.parse import urlparse, parse_qs, unquote
        qs = parse_qs(urlparse(url).query)
        raw = qs.get("id", [""])[0]
        return unquote(raw)

    def _parse_document(self, html: str, ty: str, doc_id: str, url: str) -> dict:
        """解析全文頁面

        法令判解系統全文頁結構（data.aspx）：
        <div class="int-table">
          <div class="row">
            <div class="col-th">發文單位：</div>
            <div class="col-td">司法院</div>
          </div>
          <div class="row">
            <div class="col-th">解釋字號：</div>
            <div class="col-td itemtitle">釋字第 808 號【刑罰併處...】</div>
          </div>
          ...
          <div class="col-all text-pre">理 由 書：...</div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")

        # ── 標題（從 <title> 標籤）──────────────────────────
        title_el = soup.find("title")
        title = title_el.get_text(strip=True) if title_el else ""

        # ── 主要資料表格 ─────────────────────────────────────
        int_table = soup.find("div", class_="int-table")
        fields: dict[str, str] = {}
        full_text_parts: list[str] = []

        if int_table:
            # 解析每個 row：col-th = 欄位名稱，col-td = 內容
            for row in int_table.find_all("div", class_="row"):
                th = row.find("div", class_="col-th")
                td = row.find("div", class_=re.compile(r"\bcol-td\b"))
                if th and td:
                    key = th.get_text(strip=True).rstrip("：: ")
                    val = td.get_text("\n", strip=True)
                    fields[key] = val
                    full_text_parts.append(f"{key}：\n{val}")

            # 理由書全文（col-all text-pre）
            full_section = int_table.find("div", class_=re.compile(r"\bcol-all\b"))
            if full_section:
                reasoning = full_section.get_text("\n", strip=True)
                full_text_parts.append(reasoning)

        full_text = "\n\n".join(full_text_parts)
        full_text = re.sub(r"\n{3,}", "\n\n", full_text).strip()

        # 若 int-table 解析失敗，fallback 到去掉 nav/header/footer 後的全頁文字
        if not full_text:
            for tag in soup(["script", "style", "nav", "header", "footer",
                             "noscript"]):
                tag.decompose()
            main = (
                soup.find("div", id="center")
                or soup.find("div", class_="main")
                or soup.body
            )
            full_text = (main or soup).get_text("\n", strip=True)
            full_text = re.sub(r"\n{3,}", "\n\n", full_text).strip()

        return {
            "success":    True,
            "ty":         ty,
            "id":         doc_id,
            "doc_type":   TY_NAMES.get(ty, ty),
            "title":      title,
            "fields":     fields,        # 結構化欄位（字號、日期、爭點、解釋文…）
            "full_text":  full_text[:50000],
            "url":        url,
            "cached":     False,
            "timestamp":  datetime.now().isoformat(),
        }
