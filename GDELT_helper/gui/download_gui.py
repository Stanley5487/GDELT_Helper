
import os
import threading
import queue
from datetime import datetime, timezone

from tkinter import (
    Frame, Label, Button, Listbox, Scrollbar, Text, StringVar, BooleanVar,
    LEFT, RIGHT, BOTH, X, Y, END, EXTENDED, DISABLED, NORMAL, filedialog
)
from tkinter import ttk

from GDELT_helper.gui.utils import new_section
from GDELT_helper.download.core import (
    enumerate_targets_for_year,
    count_total_targets,
    detect_latest_available_year,
    download_one,
)
from GDELT_helper.config import NotificationConfig
from GDELT_helper.notify import Notifier


class GDELTDownloaderGUI:
    def __init__(self, parent, notify_cfg=None):
        self.parent = parent
        self.frame = Frame(parent)
        self.frame.pack(fill=BOTH, expand=True)

        self.save_dir = StringVar(value="")
        self.downloading = BooleanVar(value=False)
        self.stop_event = threading.Event()

        self.year_min = 1979
        self.year_max = datetime.now(timezone.utc).year

        self._build_top_bar()
        self._build_year_selector()
        self._build_progress()
        self._build_log()

        self.notify_cfg = notify_cfg if notify_cfg is not None else NotificationConfig()
        self.notifier = Notifier(self.notify_cfg)

        self.msg_queue = queue.Queue()
        self._drain_queue()

    def destroy(self):
        self.frame.destroy()

    # ---------------- UI blocks ----------------

    def _build_top_bar(self):
        box= new_section(self.frame, "儲存路徑與偵測")
        Label(box, text="儲存資料夾：").pack(side=LEFT)
        self.dir_label = Label(box, textvariable=self.save_dir, relief="groove", anchor="w")
        self.dir_label.pack(side=LEFT, fill=X, expand=True, padx=6)
        Button(box, text="選擇資料夾", command=self._choose_dir).pack(side=LEFT, padx=6)
        Button(box, text="偵測最新年份", command=self._detect_and_update_years).pack(side=LEFT, padx=6)

    def _build_year_selector(self):
        box = new_section(self.frame, "選擇年份（可複選）")
        left = Frame(box); left.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = Scrollbar(left); scrollbar.pack(side=RIGHT, fill=Y)
        self.year_list = Listbox(left, selectmode=EXTENDED, exportselection=False, height=14)
        self.year_list.pack(side=LEFT, fill=BOTH, expand=True)
        self.year_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.year_list.yview)
        self._refresh_year_list()

        btns = Frame(box); btns.pack(side=RIGHT, padx=6)
        Button(btns, text="全選", command=self._select_all).pack(fill=X, pady=3)
        Button(btns, text="清除", command=self._clear_sel).pack(fill=X, pady=3)
        self.btn_download = Button(btns, text="下載", command=self._start_download)
        self.btn_download.pack(fill=X, pady=(3, 1))
        self.btn_stop = Button(btns, text="中止下載", command=self._stop_download, state=DISABLED)
        self.btn_stop.pack(fill=X, pady=(1, 3))

    def _build_progress(self):
        box= new_section(self.frame, "整體進度")
        self.progress = ttk.Progressbar(box, mode="determinate", maximum=100)
        self.progress.pack(fill=X, padx=2, pady=(0, 4))
        self.progress_text = StringVar(value="尚未開始")
        Label(box, textvariable=self.progress_text).pack(anchor="w")

    def _build_log(self):
        box= new_section(self.frame, "下載紀錄")
        inner = Frame(box); inner.pack(fill=BOTH, expand=True)
        scrollbar = Scrollbar(inner); scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text = Text(inner, height=16)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self.save_dir.get(), title="選擇儲存資料夾")
        if d:
            self.save_dir.set(d)

    def _refresh_year_list(self):
        self.year_list.delete(0, END)
        for y in range(self.year_min, self.year_max + 1):
            self.year_list.insert(END, str(y))

    def _select_all(self):
        self.year_list.selection_set(0, END)

    def _clear_sel(self):
        self.year_list.selection_clear(0, END)

    def _detect_and_update_years(self):
        self._log("偵測最新可用年份中…")

        def run():
            latest = detect_latest_available_year()
            self.msg_queue.put(("log", f"偵測完成：{latest}"))
            self.msg_queue.put(("years", latest))
        threading.Thread(target=run, daemon=True).start()


    def _log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(END, f"[{ts}] {msg}\n")
        self.log_text.see(END)

    def _queue_log(self, msg):
        self.msg_queue.put(("log", msg))

    def _queue_progress(self, completed, total):
        self.msg_queue.put(("progress", (completed, total)))

    def _drain_queue(self):
        try:
            while True:
                typ, payload = self.msg_queue.get_nowait()
                if typ == "log":
                    self._log(payload)
                elif typ == "progress":
                    comp, total = payload
                    pct = (comp / total * 100) if total > 0 else 0
                    self.progress["value"] = pct
                    self.progress_text.set(f"{comp} / {total} 檔（{pct:.1f}%）")
                elif typ == "years":
                    latest = int(payload)
                    if latest > self.year_max:
                        self.year_max = latest
                        self._refresh_year_list()
                        self._log(f"年份已更新為 {self.year_min}–{self.year_max}")
        except queue.Empty:
            pass
        finally:
            self.frame.after(120, self._drain_queue)

    # ---------------- download flow ----------------

    def _start_download(self):
        if self.downloading.get():
            return
        sel = [self.year_list.get(i) for i in self.year_list.curselection()]
        if not sel:
            self._log("請先選擇至少一個年份！")
            return
        out_dir = self.save_dir.get()
        if not out_dir:
            self._log("請先選擇儲存資料夾！")
            return
        os.makedirs(out_dir, exist_ok=True)

        total = count_total_targets(sel)
        if total == 0:
            self._log("沒有可下載的目標。")
            return

        # UI 反饋
        self._log("開始下載，請稍後！")
        self.btn_download.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        self.progress["maximum"] = 100
        self.progress["value"] = 0
        self.progress_text.set("準備中…")
        self.downloading.set(True)
        self.stop_event.clear()

        t = threading.Thread(target=self._worker_download, args=(sel, out_dir, total), daemon=True)
        t.start()

    def _stop_download(self):
        if self.downloading.get():
            self.stop_event.set()
            self._log("正在中止下載…")

    def _worker_download(self, years, out_dir, total):
        completed = 0

        def perfile_cb(delta):
            nonlocal completed
            completed += delta
            self._queue_progress(completed, total)

        self._queue_log(f"開始下載。儲存位置：{out_dir}")
        try:
            for y in years:
                if self.stop_event.is_set():
                    break
                self._queue_log(f"年份 {y}：搜尋檔案中")
                targets = enumerate_targets_for_year(int(y))
                if not targets:
                    self._queue_log(f"年份 {y} 無目標，略過。")
                    continue
                for base in targets:
                    if self.stop_event.is_set():
                        break
                    self._queue_log(f"嘗試：{base}")
                    try:
                        download_one(base, out_dir, self._queue_log, self.stop_event, perfile_cb=perfile_cb)
                    except Exception as e:
                        self._queue_log(f"下載錯誤（{base}）：{e!r}")
        except Exception as e:
            self._queue_log(f"致命錯誤：{e!r}")
            try:
                if getattr(self.notify_cfg, "enabled", False) and getattr(self.notify_cfg, "on_error", False):
                    self.notifier.notify(
                        "GDELT下載：致命錯誤",
                        f"儲存位置：{out_dir}\n已完成：{completed} / {total}\n錯誤：{e!r}\n時間：{datetime.now():%Y-%m-%d %H:%M:%S}"
                    )
            except Exception as ne:
                self._queue_log(f"通知失敗：{ne!r}")
        finally:
            self.downloading.set(False)
            self.btn_download.config(state=NORMAL)
            self.btn_stop.config(state=DISABLED)

            if self.stop_event.is_set():
                self._queue_log("下載已中止。")
            else:
                self._queue_log("所有選取年份處理完成。")
                try:
                    enabled = getattr(self.notify_cfg, "enabled", False)
                    on_finish = getattr(self.notify_cfg, "on_finish", False)
                    to_addrs = getattr(self.notify_cfg, "to_addrs", "").strip()
                    if enabled and on_finish and to_addrs:
                        self._queue_log("通知：嘗試寄出『下載完成』郵件…")
                        self.notifier.notify(
                            "GDELT下載：完成",
                            (f"儲存位置：{out_dir}\n"
                             f"總目標：{total}\n"
                             f"完成數：{completed}\n"
                             f"完成時間：{datetime.now():%Y-%m-%d %H:%M:%S}")
                        )
                        self._queue_log("通知：『下載完成』郵件已送出")
                    else:
                        self._queue_log("通知：條件未滿足（未啟用或未勾完成、或收件人為空），不寄信。")
                except Exception as ne:
                    self._queue_log(f"通知失敗：{ne!r}")
