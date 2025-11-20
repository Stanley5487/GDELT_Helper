# GUI共用
from tkinter import (
    Frame, Label, Canvas, Scrollbar, BOTH, LEFT, RIGHT, Y, X
)
from tkinter import TclError

def new_section(parent, title: str, pad=(12, 8)):
    box = Frame(parent)
    box.pack(fill=X, padx=12, pady=(8, 4))
    Label(box, text=title, font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
    inner = Frame(box)
    inner.pack(fill=X)
    return inner


class ScrollFrame(Frame):
    """
    可滾動容器：把要顯示的元件放到 self.body 裡。
    用法：
        sf = ScrollFrame(parent)
        sf.pack(fill=BOTH, expand=True)
        Label(sf.body, text="Hello").pack()
    """
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.canvas = Canvas(self, highlightthickness=0)
        self.vbar = Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vbar.set)

        self.vbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)

        # 內層承載內容
        self.body = Frame(self.canvas)
        self.win = self.canvas.create_window(0, 0, window=self.body, anchor="nw")

        # 大小改變時更新
        self.body.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # 滑輪支援
        self.canvas.bind("<Enter>", self._activate_mousewheel)
        self.canvas.bind("<Leave>", self._deactivate_mousewheel)

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.win, width=event.width)

    def _on_mousewheel(self, event):
        if not self.canvas.winfo_exists():
            return "break"
        delta = -1 * int(event.delta / 120) if getattr(event, "delta", 0) else 0
        try:
            self.canvas.yview_scroll(delta, "units")
        except TclError:
            return "break"
        return "break"

    def _on_linux_scroll(self, event):
        if not self.canvas.winfo_exists():
            return "break"
        step = 1 if event.num == 5 else -1
        try:
            self.canvas.yview_scroll(step, "units")
        except TclError:
            return "break"
        return "break"

    def _activate_mousewheel(self, _evt=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _deactivate_mousewheel(self, _evt=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def destroy(self):
        self._deactivate_mousewheel()
        super().destroy()
