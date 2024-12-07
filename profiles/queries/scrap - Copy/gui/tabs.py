# import tkinter as tk
from tkinter import ttk
from gui.dialogs import create_dialogs

def create_tabs(root):
    """
    Creates a tab control with two tabs and adds them to the given root widget.

    Parameters:
        root (tkinter.Tk or tkinter.Toplevel): The root widget to which the tab control will be added.

    Returns:
        None
    """
    tab_control = ttk.Notebook(root)

    tab1 = ttk.Frame(tab_control)
    tab2 = ttk.Frame(tab_control)

    tab_control.add(tab1, text='Tab 1')
    tab_control.add(tab2, text='Tab 2')

    tab_control.pack(expand=1, fill='both')

    create_dialogs(tab1)
    create_dialogs(tab2)
