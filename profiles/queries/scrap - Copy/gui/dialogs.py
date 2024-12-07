import tkinter as tk
# from tkinter import messagebox
from gui.controllers import create_entity, read_entity, update_entity, delete_entity

def create_dialogs(parent):
    """
    Creates a dialog box with four buttons: Create, Read, Update, and Delete.

    This function creates a dialog box with four buttons: Create, Read, Update, and Delete.
    The dialog box is displayed on the parent window.

    Parameters:
    ----------
    parent : tkinter.Tk or tkinter.Toplevel
        The parent window on which the dialog box is displayed.

    Returns:
    -------
    None

    Example:
        >>> root = tk.Tk()
        >>> create_dialogs(root)
    """
    create_button = tk.Button(parent, text="Create", command=create_entity)
    read_button = tk.Button(parent, text="Read", command=read_entity)
    update_button = tk.Button(parent, text="Update", command=update_entity)
    delete_button = tk.Button(parent, text="Delete", command=delete_entity)

    create_button.pack()
    read_button.pack()
    update_button.pack()
    delete_button.pack()
