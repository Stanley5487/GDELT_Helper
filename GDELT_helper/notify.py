from GDELT_helper.config import NotificationConfig
import smtplib
import ssl
import threading
from email.message import EmailMessage
import traceback

class Notifier:
    def __init__(self, cfg: NotificationConfig):
        self.cfg = cfg

    def notify(self, subject: str, body: str):
        if not self.cfg.enabled:
            return
        to_list = [a.strip() for a in self.cfg.to_addrs.split(",") if a.strip()]
        if not (self.cfg.smtp_host and self.cfg.from_addr and to_list):
            return

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.cfg.from_addr
        msg["To"] = ", ".join(to_list)
        msg.set_content(body, charset="utf-8")

        if self.cfg.use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(self.cfg.smtp_host, self.cfg.smtp_port, context=context, timeout=30) as server:
                if self.cfg.username:
                    server.login(self.cfg.username, self.cfg.password)
                server.send_message(msg, mail_options=["SMTPUTF8"])
        else:
            with smtplib.SMTP(self.cfg.smtp_host, self.cfg.smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=ssl.create_default_context())
                if self.cfg.username:
                    server.login(self.cfg.username, self.cfg.password)
                server.send_message(msg, mail_options=["SMTPUTF8"])

    def safe_notify(self, subject: str, body: str):
        try:
            self.notify(subject, body)
        except Exception as e:
            print("[Notifier] 寄信失敗：", repr(e))

class HourlyTicker:
    def __init__(self, enabled: bool, callback):
        self.enabled = enabled
        self.callback = callback
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        if self.enabled:
            self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        while not self._stop.wait(3600):
            try:
                self.callback()
            except Exception:
                print("[HourlyTicker] callback failed:", traceback.format_exc())
