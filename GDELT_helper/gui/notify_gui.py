from GDELT_helper.config import  NotificationConfig
from tkinter import (
    StringVar, BooleanVar,  BOTH, LEFT, RIGHT, X, Frame, Button, Label, Entry, Checkbutton, Toplevel, messagebox
)
from GDELT_helper.notify import Notifier

class TkNotifyDialog:
    def __init__(self, parent, cfg: NotificationConfig):
        self.cfg = cfg
        self.top = Toplevel(parent)
        self.top.title("通知設定")
        self.top.geometry("560x420")
        self.top.grab_set()
        self.enabled = BooleanVar(value=cfg.enabled)
        self.smtp_host = StringVar(value=cfg.smtp_host)
        self.smtp_port = StringVar(value=str(cfg.smtp_port))
        self.use_ssl = BooleanVar(value=cfg.use_ssl)
        self.username = StringVar(value=cfg.username)
        self.password = StringVar(value=cfg.password)
        self.from_addr = StringVar(value=cfg.from_addr)
        self.to_addrs = StringVar(value=cfg.to_addrs)
        self.on_finish = BooleanVar(value=cfg.on_finish)
        self.on_error = BooleanVar(value=cfg.on_error)

        frm = Frame(self.top); frm.pack(fill=BOTH, expand=True, padx=12, pady=12)

        Checkbutton(frm, text="啟用通知", variable=self.enabled).grid(row=0, column=0, sticky="w")
        Label(frm, text="SMTP Host").grid(row=1, column=0, sticky="e"); Entry(frm, textvariable=self.smtp_host, width=28).grid(row=1, column=1, sticky="w")
        Label(frm, text="SMTP Port").grid(row=2, column=0, sticky="e"); Entry(frm, textvariable=self.smtp_port, width=8).grid(row=2, column=1, sticky="w")

        Label(frm, text="帳號").grid(row=4, column=0, sticky="e"); Entry(frm, textvariable=self.username, width=28).grid(row=4, column=1, sticky="w")
        Label(frm, text="密碼/應用程式碼").grid(row=5, column=0, sticky="e"); Entry(frm, textvariable=self.password, show="*", width=28).grid(row=5, column=1, sticky="w")

        Label(frm, text="From").grid(row=6, column=0, sticky="e"); Entry(frm, textvariable=self.from_addr, width=28).grid(row=6, column=1, sticky="w")
        Label(frm, text="To（逗號分隔）").grid(row=7, column=0, sticky="e"); Entry(frm, textvariable=self.to_addrs, width=28).grid(row=7, column=1, sticky="w")

        Checkbutton(frm, text="完成時寄送", variable=self.on_finish).grid(row=8, column=0, sticky="w")
        Checkbutton(frm, text="程式錯誤即時寄送", variable=self.on_error).grid(row=8, column=1, sticky="w")

        btns = Frame(self.top); btns.pack(fill=X, padx=12, pady=(0,12))
        Button(btns, text="發送測試信", command=self._test_send).pack(side=LEFT)
        Button(btns, text="儲存", command=self._save).pack(side=RIGHT, padx=6)
        Button(btns, text="取消", command=self.top.destroy).pack(side=RIGHT)

    def _test_send(self):
        try:
            tmp = NotificationConfig(
                enabled=True,
                smtp_host=self.smtp_host.get().strip(),
                smtp_port=int(self.smtp_port.get().strip() or 587),
                use_ssl=self.use_ssl.get(),
                username=self.username.get().strip(),
                password=self.password.get(),
                from_addr=self.from_addr.get().strip(),
                to_addrs=self.to_addrs.get().strip(),
                on_finish=self.on_finish.get(),
                on_error=self.on_error.get(),
            )
            Notifier(tmp).notify("GDELT小幫手：測試通知", "這是一封測試通知郵件。")
            messagebox.showinfo("成功", "測試信寄出！")
        except Exception as e:
            messagebox.showerror("失敗", f"寄信失敗：\n{e}")

    def _save(self):
        try:
            self.cfg.enabled = self.enabled.get()
            self.cfg.smtp_host = self.smtp_host.get().strip()
            self.cfg.smtp_port = int(self.smtp_port.get().strip() or 587)
            self.cfg.use_ssl = self.use_ssl.get()
            self.cfg.username = self.username.get().strip()
            self.cfg.password = self.password.get()
            self.cfg.from_addr = self.from_addr.get().strip()
            self.cfg.to_addrs = self.to_addrs.get().strip()
            self.cfg.on_finish = self.on_finish.get()
            self.cfg.on_error = self.on_error.get()
            self.top.destroy()
        except Exception as e:
            messagebox.showerror("錯誤", f"儲存失敗：{e}")