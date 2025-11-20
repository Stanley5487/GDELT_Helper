# processing.py
from __future__ import annotations
import os, re, requests
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Iterable, Optional, List, Dict, Any
import pandas as pd

REQUEST_TIMEOUT = 30

GDELT_HEADER_URLS = {
    "Historical (1979–2013)": "https://www.gdeltproject.org/data/lookups/CSV.header.historical.txt",
    "DailyUpdates (2013+)": "https://www.gdeltproject.org/data/lookups/CSV.header.dailyupdates.txt",
}

BUILTIN_COLUMNS = [
    "Year", "SQLDATE", "MonthYear",
    "Actor1CountryCode", "Actor1Type1Code",
    "Actor2CountryCode", "Actor2Type1Code",
    "IsRootEvent",
    "EventCode", "EventBaseCode",
    "QuadClass", "GoldsteinScale", "AvgTone"
]

COMMON_ACTOR_TYPES = ["GOV", "MIL", "COP", "JUD", "SPY", "OPP", "REB", "BUS", "EDU", "HLH", "MED", "ELI", "CVL", "REF", "JRN", "NGO"]
QUICK_ISO3 = ["USA", "CHN", "RUS", "GBR", "FRA", "DEU", "JPN"]


# ---------- 公用工具 ----------
def extract_year_from_filename(fname: str) -> Optional[int]:
    m = re.search(r'(\d{8})', fname)
    if m: return int(m.group(1)[:4])
    m = re.search(r'(\d{6})', fname)
    if m: return int(m.group(1)[:4])
    m = re.search(r'(\d{4})', fname)
    if m:
        y = int(m.group(1))
        if 1979 <= y <= datetime.now(timezone.utc).year:
            return y
    return None

def filename_year_in_range(fname: str, start: int, end: int) -> bool:
    y = extract_year_from_filename(fname)
    return (y is not None) and (start <= y <= end)

def get_headers_union(timeout: int = REQUEST_TIMEOUT) -> List[str]:
    def fetch(url):
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.text.strip().split("\t")
    cols_daily = fetch(GDELT_HEADER_URLS["DailyUpdates (2013+)"])
    cols_hist = fetch(GDELT_HEADER_URLS["Historical (1979–2013)"])
    union, seen = [], set()
    for name in cols_daily + cols_hist:
        if name not in seen:
            union.append(name); seen.add(name)
    return union

def safe_read(path: str, timeout: int = REQUEST_TIMEOUT) -> pd.DataFrame:
    """能自動偵測兩種 header；回傳全字串型別以保安全。"""
    def read_with(columns):
        return pd.read_csv(
            path, sep="\t", header=None, names=columns, dtype=str,
            on_bad_lines="skip", low_memory=False, engine="c"
        )
    try:
        cols = requests.get(GDELT_HEADER_URLS["DailyUpdates (2013+)"], timeout=timeout).text.strip().split("\t")
        return read_with(cols)
    except Exception:
        cols = requests.get(GDELT_HEADER_URLS["Historical (1979–2013)"], timeout=timeout).text.strip().split("\t")
        return read_with(cols)

def reorder_columns_priority(df: pd.DataFrame, user_subset: Optional[Iterable[str]] = None) -> pd.DataFrame:
    priority = [
        "Year", "MonthYear", "SQLDATE",
        "Actor1CountryCode", "Actor1Type1Code",
        "Actor2CountryCode", "Actor2Type1Code",
        "EventCode", "EventBaseCode", "EventRootCode",
        "QuadClass", "GoldsteinScale"
    ]
    if user_subset is None:
        base = list(df.columns)
    else:
        base = [c for c in user_subset if c in df.columns]
    ordered = [c for c in priority if c in base] + [c for c in base if c not in priority]
    return df[ordered]

def _parse_token_list(txt: str) -> set[str]:
    s = (txt or "").strip()
    if not s:
        return set()
    return {t.strip().upper() for t in s.split(",") if t.strip()}


# ---------- 設定資料結構 ----------
@dataclass
class SideFilter:
    country_mode: str = "all"
    countries_csv: str = ""
    type_mode: str = "all"
    type_codes_csv: str = ""

@dataclass
class ProcessorConfig:
    selected_columns: List[str] = field(default_factory=lambda: list(BUILTIN_COLUMNS))
    enable_year_filter: bool = False
    year_start: int = 2005
    year_end: int = datetime.now(timezone.utc).year
    only_cross_country: bool = False
    a1: SideFilter = field(default_factory=SideFilter)
    a2: SideFilter = field(default_factory=SideFilter)


# ---------- 主流程 ----------
def process_directory(
    raw_dir: str,
    out_path: str,
    cfg: ProcessorConfig,
    stop_flag: Optional[Callable[[], bool]] = None,
    progress_cb: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    讀取 raw_dir 下所有 .csv（tab 分隔、無標頭），依 cfg 篩選後合併輸出到 out_path。
    stop_flag(): 回傳 True 代表要求中止。
    progress_cb(msg): 用來回報日誌。
    回傳: {'files_total':int, 'files_used':int, 'rows_out':int, 'errors':int}
    """
    def log(msg: str):
        if progress_cb:
            progress_cb(msg)

    if not raw_dir or not os.path.isdir(raw_dir):
        raise FileNotFoundError("無此資料夾或路徑（原始資料夾）。")
    out_dir = os.path.dirname(out_path) or "."
    if not os.path.isdir(out_dir):
        raise FileNotFoundError("無此資料夾或路徑（輸出資料夾）。")

    try:
        files = [f for f in sorted(os.listdir(raw_dir)) if f.lower().endswith(".csv")]
    except FileNotFoundError:
        raise FileNotFoundError("讀取目錄失敗：無此資料夾或權限不足。")

    if not files:
        log("找不到檔案。請先進行下載或確認檔案路徑！")
        return {'files_total': 0, 'files_used': 0, 'rows_out': 0, 'errors': 0}

    files_total = len(files)
    errors = 0
    used = 0
    all_dfs: List[pd.DataFrame] = []

    # 年份快篩（依檔名）
    if cfg.enable_year_filter:
        files_prefiltered = [f for f in files if filename_year_in_range(f, cfg.year_start, cfg.year_end)]
        skipped = len(files) - len(files_prefiltered)
        files = files_prefiltered
        log(f"年份篩選：保留 {len(files)} 檔，略過 {skipped} 檔。")
        if not files:
            log("篩選後沒有符合年份的檔案。")
            return {'files_total': files_total, 'files_used': 0, 'rows_out': 0, 'errors': 0}

    want_cols = list(cfg.selected_columns) if cfg.selected_columns else None

    for idx, fname in enumerate(files, 1):
        if stop_flag and stop_flag():
            log("處理已中止。")
            break

        path = os.path.join(raw_dir, fname)
        try:
            df = safe_read(path)

            # 年份兜底（讀入後再濾）
            if cfg.enable_year_filter and not filename_year_in_range(fname, cfg.year_start, cfg.year_end):
                if 'Year' in df.columns:
                    yr = pd.to_numeric(df['Year'], errors='coerce')
                    df = df[(yr >= cfg.year_start) & (yr <= cfg.year_end)]
                elif 'SQLDATE' in df.columns:
                    yr = pd.to_numeric(df['SQLDATE'].astype(str).str[:4], errors='coerce')
                    df = df[(yr >= cfg.year_start) & (yr <= cfg.year_end)]
                else:
                    log(f"ℹ️ {fname} 無 Year/SQLDATE，無法做年份篩選。")

            # 國家過濾
            a1 = df.get('Actor1CountryCode')
            a2 = df.get('Actor2CountryCode')
            mask_country = pd.Series(True, index=df.index)

            if a1 is not None:
                if cfg.a1.country_mode == "custom":
                    a1_set = _parse_token_list(cfg.a1.countries_csv)
                    if a1_set:
                        mask_country &= a1.isin(a1_set)
                    else:
                        log(f"{fname} A1 自訂義國家為空，未套用 A1 國家過濾。")
                else:
                    mask_country &= a1.notna() & a1.ne('')
            else:
                log(f"{fname} 缺 Actor1CountryCode，略過 A1 國家過濾。")

            if a2 is not None:
                if cfg.a2.country_mode == "custom":
                    a2_set = _parse_token_list(cfg.a2.countries_csv)
                    if a2_set:
                        mask_country &= a2.isin(a2_set)
                    else:
                        log(f"{fname} A2 自訂義國家為空，未套用 A2 國家過濾。")
                else:
                    mask_country &= a2.notna() & a2.ne('')
            else:
                log(f"{fname} 缺 Actor2CountryCode，略過 A2 國家過濾。")

            if cfg.only_cross_country and (a1 is not None) and (a2 is not None):
                mask_country &= a1.notna() & a1.ne('') & a2.notna() & a2.ne('') & a1.ne(a2)

            df = df[mask_country]

            # 行為者類型過濾
            a1t = df.get('Actor1Type1Code')
            a2t = df.get('Actor2Type1Code')
            mask_types = pd.Series(True, index=df.index)

            if a1t is not None:
                if cfg.a1.type_mode == "labeled":
                    mask_types &= a1t.notna() & a1t.ne('')
                elif cfg.a1.type_mode == "custom":
                    codes = _parse_token_list(cfg.a1.type_codes_csv)
                    if codes:
                        mask_types &= a1t.isin(codes)
                    else:
                        log(f"{fname} A1 自訂義類型為空，未套用 A1 類型過濾。")
            else:
                log(f"{fname} 缺 Actor1Type1Code 欄，略過 A1 類型過濾。")

            if a2t is not None:
                if cfg.a2.type_mode == "labeled":
                    mask_types &= a2t.notna() & a2t.ne('')
                elif cfg.a2.type_mode == "custom":
                    codes = _parse_token_list(cfg.a2.type_codes_csv)
                    if codes:
                        mask_types &= a2t.isin(codes)
                    else:
                        log(f"{fname} A2 自訂義類型為空，未套用 A2 類型過濾。")
            else:
                log(f"{fname} 缺 Actor2Type1Code 欄，略過 A2 類型過濾。")

            df = df[mask_types]

            # 欄位子集 + 排序
            if want_cols:
                use_cols = [c for c in want_cols if c in df.columns]
                if not use_cols:
                    log(f"{fname} 無符合所選欄位，略過。")
                    continue
                df = reorder_columns_priority(df, user_subset=use_cols)
            else:
                df = reorder_columns_priority(df, user_subset=None)

            if not df.empty:
                all_dfs.append(df)
                used += 1
                log(f"{fname} 合併 {len(df):,} 筆（{idx}/{len(files)}）")
            else:
                log(f"{fname} 無符合資料。")

        except Exception as e:
            errors += 1
            log(f"錯誤 {fname}：{e}")

    if not all_dfs:
        log("沒有符合條件的資料可匯出。")
        return {'files_total': files_total, 'files_used': used, 'rows_out': 0, 'errors': errors}

    out = pd.concat(all_dfs, ignore_index=True)
    out.to_csv(out_path, index=False, sep='\t')
    log(f"完成！共匯出 {len(out):,} 筆至：{out_path}")

    return {'files_total': files_total, 'files_used': used, 'rows_out': int(len(out)), 'errors': errors}
