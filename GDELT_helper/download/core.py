#　下載功能
from __future__ import annotations
import os
import zipfile
import requests
import threading
import calendar
from datetime import datetime, timedelta, timezone


BASE_URL = "http://data.gdeltproject.org/events/"
REQUEST_TIMEOUT = 30

def unzip_and_cleanup(file_path, out_dir, log):
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(out_dir)
        os.remove(file_path)
        log(f"解壓完成並刪除壓縮檔：{os.path.basename(file_path)}")
    except zipfile.BadZipFile:
        log(f"解壓縮失敗：{os.path.basename(file_path)}")


def is_extracted(out_dir, base_filename):
    try:
        for f in os.listdir(out_dir):
            if f.startswith(str(base_filename)) and f.lower().endswith(".csv"):
                return True
    except FileNotFoundError:
        return False
    return False


def server_has(base_filename):
    for suffix in (".export.CSV.zip", ".zip"):
        url = BASE_URL + base_filename + suffix
        try:
            r = requests.head(url, allow_redirects=True, timeout=REQUEST_TIMEOUT)
            if r.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
    return False


def download_one(base_filename, out_dir, log, stop_event: threading.Event, perfile_cb=None, timeout=REQUEST_TIMEOUT):
    if stop_event.is_set():
        return
    candidates = [f"{base_filename}.export.CSV.zip", f"{base_filename}.zip"]
    if is_extracted(out_dir, base_filename):
        log(f"已有此檔案，跳過：{base_filename}")
        if perfile_cb: perfile_cb(1)
        return
    os.makedirs(out_dir, exist_ok=True)
    for filename in candidates:
        if stop_event.is_set():
            return
        url = BASE_URL + filename
        zip_path = os.path.join(out_dir, filename)
        if os.path.exists(zip_path):
            log(f"已有壓縮檔：{filename} 解壓縮中")
            unzip_and_cleanup(zip_path, out_dir, log)
            if perfile_cb: perfile_cb(1)
            return
        try:
            with requests.get(url, stream=True, timeout=timeout) as r:
                if r.status_code != 200:
                    continue
                downloaded = 0
                chunk_size = 1024 * 256
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=chunk_size):
                        if stop_event.is_set():
                            log(f"已中止下載：{filename}")
                            try:
                                f.close()
                                os.remove(zip_path)
                            except Exception:
                                pass
                            return
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                mb = downloaded / 1024 / 1024
                log(f"成功下載：{filename}（{mb:.2f} MB）")
                unzip_and_cleanup(zip_path, out_dir, log)
                if perfile_cb: perfile_cb(1)
                return
        except requests.exceptions.RequestException as e:
            log(f"下載失敗（{filename}）：{e}")
    log(f"未找到可用檔案：{base_filename}")


def enumerate_targets_for_year(year: int):
    targets = []
    if 1979 <= year <= 2005:
        targets.append(f"{year}")
    elif 2006 <= year <= 2012:
        for m in range(1, 13):
            targets.append(f"{year}{m:02d}")
    elif year == 2013:
        for m in range(1, 4):
            targets.append(f"2013{m:02d}")
        for m in range(4, 13):
            _, days = calendar.monthrange(2013, m)
            for d in range(1, days + 1):
                targets.append(f"2013{m:02d}{d:02d}")
    elif year >= 2014:
        for m in range(1, 13):
            _, days = calendar.monthrange(year, m)
            for d in range(1, days + 1):
                targets.append(f"{year}{m:02d}{d:02d}")
    return targets


def count_total_targets(years):
    return sum(len(enumerate_targets_for_year(int(y))) for y in years)


def detect_latest_available_year(max_back_days=540):
    today = datetime.now(timezone.utc).date()
    for i in range(max_back_days + 1):
        dt = today - timedelta(days=i)
        base = dt.strftime("%Y%m%d")
        if server_has(base):
            return dt.year
    return today.year