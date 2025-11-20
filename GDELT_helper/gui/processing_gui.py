# gui_data_processor.py
from __future__ import annotations
import os, threading, queue
from datetime import datetime, timezone
from tkinter import *
from tkinter import filedialog
from GDELT_helper.gui.utils import  new_section, ScrollFrame

# 資料處理
from GDELT_helper.processing.core import (
    GDELT_HEADER_URLS, BUILTIN_COLUMNS, COMMON_ACTOR_TYPES, QUICK_ISO3,
    get_headers_union, process_directory, ProcessorConfig, SideFilter
)

REQUEST_TIMEOUT = 30

# -------------------------- GUI --------------------------
class DataProcessorGUI:
    def __init__(self, parent, notify_cfg=None):
        self.parent = parent
        self.stop_event = threading.Event()

        # 捲動容器
        self.scroll = ScrollFrame(parent)
        self.scroll.pack(fill=BOTH, expand=True)
        self.frame = self.scroll.body

        # 路徑
        self.raw_dir = StringVar(value="")
        self.out_dir = StringVar(value="")
        self.out_name = StringVar(value="gdelt_filtered_data.csv")

        # 欄位
        self.all_columns = []
        self.selected_columns = list(BUILTIN_COLUMNS)

        # 國家
        self.a1_country_mode = StringVar(value="all")
        self.a2_country_mode = StringVar(value="all")
        self.actor1_countries = StringVar(value="")
        self.actor2_countries = StringVar(value="")
        self.only_cross_country = BooleanVar(value=False)

        # 年份
        this_year = datetime.now(timezone.utc).year
        self.enable_year_filter = BooleanVar(value=False)
        self.year_start = StringVar(value="2005")
        self.year_end = StringVar(value=str(this_year))

        # 類型
        self.a1_type_mode = StringVar(value="all")
        self.a2_type_mode = StringVar(value="all")
        self.a1_type_codes = StringVar(value="")
        self.a2_type_codes = StringVar(value="")

        # UI
        self._build_paths()
        self._build_column_picker()
        self._build_country_filters()
        self._build_year_filters()
        self._build_actor_type_filters()
        self._build_actions()
        self._build_log()

        self.notify_cfg = notify_cfg  # 可為 None；保留你原本的通知流程
        # self.notifier = Notifier(self.notify_cfg) if self.notify_cfg else None

        self.msg_queue = queue.Queue()
        self._drain_queue()

        # 啟動抓欄位（改用 processing 內的邏輯）
        threading.Thread(target=self._load_headers_union, daemon=True).start()

    def destroy(self):
        self.scroll.destroy()

    # ---- UI blocks ----
    def _build_paths(self):
        box= new_section(self.frame, "資料來源與輸出")
        Label(box, text="原始資料夾：").grid(row=0, column=0, sticky="w")
        Entry(box, textvariable=self.raw_dir, width=60).grid(row=0, column=1, padx=6, sticky="we")
        Button(box, text="選擇…", command=self._choose_raw).grid(row=0, column=2)
        Label(box, text="輸出資料夾：").grid(row=1, column=0, sticky="w")
        Entry(box, textvariable=self.out_dir, width=60).grid(row=1, column=1, padx=6, sticky="we")
        Button(box, text="選擇…", command=self._choose_out).grid(row=1, column=2)
        Label(box, text="輸出檔名：").grid(row=2, column=0, sticky="w")
        Entry(box, textvariable=self.out_name, width=40).grid(row=2, column=1, padx=6, sticky="w")

    def _build_column_picker(self):
        box= new_section(self.frame, "欄位選擇")
        left = Frame(box); left.grid(row=0, column=0, sticky="nsew")
        box.grid_columnconfigure(0, weight=1)
        box.grid_rowconfigure(0, weight=1)
        Label(left, text="可用欄位（多選）：").pack(anchor="w")
        inner = Frame(left); inner.pack(fill=BOTH, expand=True)
        scrollbar = Scrollbar(inner); scrollbar.pack(side=RIGHT, fill=Y)
        self.col_list = Listbox(inner, selectmode=EXTENDED, exportselection=False, height=12)
        self.col_list.pack(side=LEFT, fill=BOTH, expand=True)
        self.col_list.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.col_list.yview)
        btns = Frame(box); btns.grid(row=0, column=1, padx=8, sticky="ns")
        Button(btns, text="全選", command=lambda: self.col_list.selection_set(0, END)).pack(fill=X, pady=2)
        Button(btns, text="取消", command=lambda: self.col_list.selection_clear(0, END)).pack(fill=X, pady=2)
        Button(btns, text="套用", command=self._cols_apply).pack(fill=X, pady=8)
        Label(btns, text="提示：初始已勾常用欄位(可再調整)", justify=LEFT).pack(anchor="w")

    def _build_country_filters(self):
        box= new_section(self.frame, "國家（ISO3）")
        # A1
        Label(box, text="行為者1（發起國）").grid(row=0, column=0, sticky="w")
        Radiobutton(box, text="全部國家", variable=self.a1_country_mode, value="all",
                    command=lambda: self._toggle_country_row(1)).grid(row=0, column=1, sticky="w")
        Radiobutton(box, text="自訂義國家", variable=self.a1_country_mode, value="custom",
                    command=lambda: self._toggle_country_row(1)).grid(row=0, column=2, sticky="w")
        self.a1_country_row = Frame(box); self.a1_country_row.grid(row=1, column=0, columnspan=5, sticky="w", pady=(2,8))
        Label(self.a1_country_row, text="A1 國家（逗號分隔）：").pack(side=LEFT)
        self.a1_entry = Entry(self.a1_country_row, textvariable=self.actor1_countries, width=44); self.a1_entry.pack(side=LEFT, padx=(4,8))
        a1_btns = Frame(self.a1_country_row); a1_btns.pack(side=LEFT)
        for code in QUICK_ISO3:
            Button(a1_btns, text=code, command=lambda c=code: self._append_token(self.actor1_countries, c)).pack(side=LEFT, padx=1)

        # A2
        Label(box, text="行為者2（目標國）").grid(row=2, column=0, sticky="w")
        Radiobutton(box, text="全部國家", variable=self.a2_country_mode, value="all",
                    command=lambda: self._toggle_country_row(2)).grid(row=2, column=1, sticky="w")
        Radiobutton(box, text="自訂義國家", variable=self.a2_country_mode, value="custom",
                    command=lambda: self._toggle_country_row(2)).grid(row=2, column=2, sticky="w")
        self.a2_country_row = Frame(box); self.a2_country_row.grid(row=3, column=0, columnspan=5, sticky="w", pady=(2,4))
        Label(self.a2_country_row, text="A2 國家（逗號分隔）：").pack(side=LEFT)
        self.a2_entry = Entry(self.a2_country_row, textvariable=self.actor2_countries, width=44); self.a2_entry.pack(side=LEFT, padx=(4,8))
        a2_btns = Frame(self.a2_country_row); a2_btns.pack(side=LEFT)
        for code in QUICK_ISO3:
            Button(a2_btns, text=code, command=lambda c=code: self._append_token(self.actor2_countries, c)).pack(side=LEFT, padx=1)

        self.chk_cross = Checkbutton(box, text="只保留A1和A2是相異國家（A1≠A2）", variable=self.only_cross_country)
        self.chk_cross.grid(row=4, column=0, columnspan=3, sticky="w", pady=(6,0))

        # 預設隱藏自訂列
        self._toggle_country_row(1, init=True)
        self._toggle_country_row(2, init=True)

    def _build_year_filters(self):
        box = new_section(self.frame, "年份篩選")
        Checkbutton(box, text="啟用年份篩選", variable=self.enable_year_filter).grid(row=0, column=0, sticky="w")
        Label(box, text="起始年").grid(row=0, column=1, sticky="e")
        Entry(box, textvariable=self.year_start, width=8).grid(row=0, column=2, sticky="w")
        Label(box, text="結束年").grid(row=0, column=3, sticky="e")
        Entry(box, textvariable=self.year_end, width=8).grid(row=0, column=4, sticky="w")

    def _build_actor_type_filters(self):
        box = new_section(self.frame, "行為者類型（CAMEO ActorType Codes）")
        # A1
        Label(box, text="行為者1（發起）").grid(row=0, column=0, sticky="w")
        for i, (label, val) in enumerate([("所有資料（含未標籤）", "all"), ("只有有類型標籤", "labeled"), ("自訂義", "custom")], start=1):
            Radiobutton(box, text=label, variable=self.a1_type_mode, value=val,
                        command=lambda: self._toggle_type_row(1)).grid(row=0, column=i, sticky="w")
        self.a1_custom_row = Frame(box); self.a1_custom_row.grid(row=1, column=0, columnspan=4, sticky="w", pady=(2,8))
        Label(self.a1_custom_row, text="A1 類型碼（逗號分隔）：").pack(side=LEFT)
        self.a1_entry_type = Entry(self.a1_custom_row, textvariable=self.a1_type_codes, width=44); self.a1_entry_type.pack(side=LEFT, padx=(4,8))
        a1_btns = Frame(self.a1_custom_row); a1_btns.pack(side=LEFT)
        for code in COMMON_ACTOR_TYPES:
            Button(a1_btns, text=code, command=lambda c=code: self._append_token(self.a1_type_codes, c)).pack(side=LEFT, padx=1)
        # A2
        Label(box, text="行為者2（目標）").grid(row=2, column=0, sticky="w")
        for i, (label, val) in enumerate([("所有資料（含未標籤）", "all"), ("只有有類型標籤", "labeled"), ("自訂義", "custom")], start=1):
            Radiobutton(box, text=label, variable=self.a2_type_mode, value=val,
                        command=lambda: self._toggle_type_row(2)).grid(row=2, column=i, sticky="w")
        self.a2_custom_row = Frame(box); self.a2_custom_row.grid(row=3, column=0, columnspan=4, sticky="w", pady=(2,4))
        Label(self.a2_custom_row, text="A2 類型碼（逗號分隔）：").pack(side=LEFT)
        self.a2_entry_type = Entry(self.a2_custom_row, textvariable=self.a2_type_codes, width=44); self.a2_entry_type.pack(side=LEFT, padx=(4,8))
        a2_btns = Frame(self.a2_custom_row); a2_btns.pack(side=LEFT)
        for code in COMMON_ACTOR_TYPES:
            Button(a2_btns, text=code, command=lambda c=code: self._append_token(self.a2_type_codes, c)).pack(side=LEFT, padx=1)

        self._toggle_type_row(1, init=True)
        self._toggle_type_row(2, init=True)

    def _build_actions(self):
        box = new_section(self.frame, "開始處理")
        self.btn_process = Button(box, text="開始合併與篩選", command=self._start_process); self.btn_process.pack(side=LEFT)
        self.btn_stop = Button(box, text="中止處理", command=self._stop_process, state=DISABLED); self.btn_stop.pack(side=LEFT, padx=8)

    def _build_log(self):
        box = new_section(self.frame, "處理日誌")
        inner = Frame(box); inner.pack(fill=BOTH, expand=True)
        scrollbar = Scrollbar(inner); scrollbar.pack(side=RIGHT, fill=Y)
        self.log_text = Text(inner, height=18)
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

    # ---- UI helpers ----
    def _append_token(self, var: StringVar, token: str):
        cur = var.get().strip()
        parts = [p.strip().upper() for p in cur.split(",") if p.strip()] if cur else []
        if token not in parts:
            parts.append(token)
            var.set(",".join(parts))

    def _toggle_country_row(self, side: int, init: bool=False):
        if side == 1:
            if self.a1_country_mode.get() == "custom":
                self.a1_country_row.grid()
                self.a1_entry.config(state=NORMAL)
            else:
                self.a1_country_row.grid_remove()
                if not init: self.actor1_countries.set("")
        else:
            if self.a2_country_mode.get() == "custom":
                self.a2_country_row.grid()
                self.a2_entry.config(state=NORMAL)
            else:
                self.a2_country_row.grid_remove()
                if not init: self.actor2_countries.set("")

    def _toggle_type_row(self, side: int, init: bool=False):
        if side == 1:
            if self.a1_type_mode.get() == "custom":
                self.a1_custom_row.grid(); self.a1_entry_type.config(state=NORMAL)
            else:
                self.a1_custom_row.grid_remove()
                if not init: self.a1_type_codes.set("")
        else:
            if self.a2_type_mode.get() == "custom":
                self.a2_custom_row.grid(); self.a2_entry_type.config(state=NORMAL)
            else:
                self.a2_custom_row.grid_remove()
                if not init: self.a2_type_codes.set("")

    def _choose_raw(self):
        d = filedialog.askdirectory(initialdir=self.raw_dir.get() or "/", title="選擇原始資料夾")
        if d: self.raw_dir.set(d)

    def _choose_out(self):
        d = filedialog.askdirectory(initialdir=self.out_dir.get() or "/", title="選擇輸出資料夾")
        if d: self.out_dir.set(d)

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(END, f"[{ts}] {msg}\n")
        self.log_text.see(END)

    def _queue_log(self, msg: str):
        self.msg_queue.put(("log", msg))

    def _drain_queue(self):
        try:
            while True:
                typ, payload = self.msg_queue.get_nowait()
                if typ == "log":
                    self._log(payload)
        except queue.Empty:
            pass
        finally:
            self.frame.after(120, self._drain_queue)

    def _cols_apply(self):
        sel_idx = list(self.col_list.curselection())
        sel = [self.col_list.get(i) for i in sel_idx]
        self.selected_columns = list(sel)
        self._log(f"已套用欄位 {len(sel)} 項")

    def _load_headers_union(self):
        try:
            union = get_headers_union(timeout=REQUEST_TIMEOUT)
            self.all_columns = union
            self.col_list.delete(0, END)
            for c in self.all_columns:
                self.col_list.insert(END, c)
            # 預選（依 selected_columns）
            indices_to_select = [i for i, c in enumerate(self.col_list.get(0, END)) if c in self.selected_columns]
            for i in indices_to_select:
                self.col_list.selection_set(i)
            self._queue_log(f"已載入欄位 {len(self.all_columns)} 項")
        except Exception as e:
            self._queue_log(f"欄位下載失敗：{e}")

    # ---- 啟動/停止 ----
    def _start_process(self):
        self._queue_log("開始進行合併與篩選！")
        self.btn_process.config(state=DISABLED)
        self.btn_stop.config(state=NORMAL)
        self.stop_event.clear()
        threading.Thread(target=self._worker_process, daemon=True).start()

    def _stop_process(self):
        self.stop_event.set()
        self._queue_log("停止處理中...")

    # 將 UI 參數→ProcessorConfig
    def _build_cfg_from_ui(self) -> ProcessorConfig:
        try:
            y_start = int(self.year_start.get()); y_end = int(self.year_end.get())
        except Exception:
            y_start, y_end = 2005, datetime.now(timezone.utc).year

        return ProcessorConfig(
            selected_columns=list(self.selected_columns),
            enable_year_filter=self.enable_year_filter.get(),
            year_start=y_start,
            year_end=y_end,
            only_cross_country=self.only_cross_country.get(),
            a1=SideFilter(
                country_mode=self.a1_country_mode.get(),
                countries_csv=self.actor1_countries.get(),
                type_mode=self.a1_type_mode.get(),
                type_codes_csv=self.a1_type_codes.get()
            ),
            a2=SideFilter(
                country_mode=self.a2_country_mode.get(),
                countries_csv=self.actor2_countries.get(),
                type_mode=self.a2_type_mode.get(),
                type_codes_csv=self.a2_type_codes.get()
            )
        )

    def _worker_process(self):
        try:
            raw_dir = (self.raw_dir.get() or "").strip()
            out_dir = (self.out_dir.get() or "").strip()
            out_name = (self.out_name.get().strip() or "gdelt_filtered_data.csv")
            if not raw_dir or not os.path.isdir(raw_dir):
                self._queue_log("無此資料夾或路徑（原始資料夾）。請重新選擇。")
                return
            if not out_dir or not os.path.isdir(out_dir):
                self._queue_log("無此資料夾或路徑（輸出資料夾）。請重新選擇。")
                return
            out_path = os.path.join(out_dir, out_name)

            cfg = self._build_cfg_from_ui()

            stats = process_directory(
                raw_dir=raw_dir,
                out_path=out_path,
                cfg=cfg,
                stop_flag=lambda: self.stop_event.is_set(),
                progress_cb=self._queue_log
            )

            # （選擇性）通知：保留原行為
            # if self.notify_cfg and getattr(self.notify_cfg, "enabled", False):
            #     ... 呼叫 Notifier 通知完成/錯誤 ...

            self._queue_log(f"摘要：共 {stats.get('files_total', 0)} 檔，使用 {stats.get('files_used', 0)} 檔，輸出 {stats.get('rows_out', 0):,} 筆，錯誤 {stats.get('errors', 0)}。")

        except Exception as e:
            self._queue_log(f"處理失敗：{e!r}")
        finally:
            self.btn_process.config(state=NORMAL)
            self.btn_stop.config(state=DISABLED)
