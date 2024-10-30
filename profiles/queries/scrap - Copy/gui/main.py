import tkinter as tk
from gui.tabs import create_tabs

def start_gui():
    """
    Starts the application GUI.

    This function initializes a root tkinter window and sets its title to "Application GUI".
    It then calls the `create_tabs` function to create the tabs and add them to the root window.
    Finally, it starts the main event loop of the application.

    Parameters:
    None

    Returns:
    None
    """
    root = tk.Tk()
    root.title("Application GUI")
    create_tabs(root)
    root.mainloop()

if __name__ == "__main__":
    start_gui()