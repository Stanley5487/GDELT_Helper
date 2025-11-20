from tkinter import Tk
from GDELT_helper.gui.main_menu import Menu

def main():
    root = Tk()
    Menu(root)
    root.mainloop()

if __name__ == "__main__":
    main()