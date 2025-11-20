from pathlib import Path
from tkinter import Tk, Frame, Label, Button, Text, X, LEFT, BOTH
from GDELT_helper.config import NotificationConfig
from GDELT_helper.gui.download_gui import GDELTDownloaderGUI
from GDELT_helper.gui.processing_gui  import DataProcessorGUI
from GDELT_helper.gui.notify_gui import TkNotifyDialog

class Menu:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("GDELT 小幫手")
        self.root.geometry("1080x720")
        self.root.minsize(960, 640)



        self.notify_cfg = NotificationConfig()

        top = Frame(root); top.pack(fill=X, padx=12, pady=10)
        Label(top, text="請選擇模式：", font=("TkDefaultFont", 11, "bold")).pack(side=LEFT)
        Button(top, text="下載模式", command=self.open_downloader).pack(side=LEFT, padx=6)
        Button(top, text="資料處理模式", command=self.open_processor).pack(side=LEFT, padx=6)
        Button(top, text="通知設定", command=self.open_notify_settings).pack(side=LEFT, padx=6)

        self.content = Frame(root)
        self.content.pack(fill=BOTH, expand=True)

        self._show_hint()

    def _clear_content(self):
        for w in self.content.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

    def _show_hint(self):
        self._clear_content()
        hint = Frame(self.content)
        hint.pack(fill=BOTH, expand=True)

        text_widget = Text(
            hint, wrap="word", font=("Microsoft JhengHei", 12),
            spacing3=6, relief="flat", height=30
        )
        text_widget.insert("1.0", (
            "作者鑒於在使用GDELT資料庫下載與整理中的困擾經驗，遂自行開發一資料下載與處理的自動化介面程式，以期提供更直覺與便利的操作方式，減輕繁瑣流程，並節省研究時間與人力，希冀能提升此資料在研究上的應用。\n"
            "作者謹此感謝GDELT團隊開發的資料庫，為本人研究獲益良多。關於GDELT資訊，敬請參閱官方網站：https://www.gdeltproject.org/。\n"
            "若使用本程式進行研究或產出學術成果，敬請於文中適當引用本工具，以支持後續維護工作。\n\n"

            "使用說明：\n"
            "兩種模式皆需在網路環境下執行，請確保電源與網路穩定後再開始任務。\n"
            "(A) 下載模式：\n"
            "   (1) 先選擇存檔位置與年份；建議先點選「偵測最新年份」。\n"
            "   (2) 下載過程中，若選擇路徑已有目標檔案將會跳過下載 \n"
            "(B) 資料處理模式：\n"
            "   (1) 先選擇原始資料夾與輸出資料夾。\n"
            "   (2) 「全部國家」會排除國別空白列；勾選「只保留不同國家（A1≠A2）」可避免兩個行為是相同國家的配對。 \n"
            "   (3) 年份篩選的邏輯是包含該年全部，例如1979年至2014年，代表資料是涵蓋1979年到2014年12月31日。\n"
            "(C) 通知設定：\n"
            "   (1) 可設定完成通知 mail，若須使用請點選「啟用通知」，啟用前可先發出測試信，確保通知信能夠寄達。\n"
            "   (2) 若使用政大 Gmail，SMTP host 請輸入 smtp.gmail.com，SMTP port 請使用預設（587)。\n"
            "   (3) 若使用 Gmail，請先至 Google 帳號申請「應用程式密碼」，其他信箱請參考該信箱之使用規範。\n"
            "   (4) 本介面程式不會自動儲存使用者的任何資訊，故每次重啟程式若須使用此功能接續重新輸入相關資訊。\n\n"

            "作者與聯絡資訊：\n"
            "作者：洪子淳（Hong Zih Chun）\n"
            "Email：b87092@gmail.com\n"
            "若您有任何問題或建議，歡迎隨時與作者聯繫。\n"
        ))
        text_widget.config(state="disabled")
        text_widget.pack(fill=BOTH, expand=True, padx=12, pady=12)

    def open_downloader(self):
        self._clear_content()
        GDELTDownloaderGUI(self.content, notify_cfg=self.notify_cfg)

    def open_processor(self):
        self._clear_content()
        DataProcessorGUI(self.content, notify_cfg=self.notify_cfg)

    def open_notify_settings(self):
        win = TkNotifyDialog(self.root, self.notify_cfg)
        self.root.wait_window(win.top)