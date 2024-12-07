import tkinter as tk
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from ttkbootstrap import ttk  # Import ttk from ttkbootstrap
from gui.controllers import GUIController
from db.dbefclasses import Base

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.style = Style(theme='darkly')
        self.title("Company Database")
        self.geometry("1200x800")

        self.active_button = None
        self.create_widgets()

    def create_widgets(self):
        self.nav_frame = ttk.Frame(self)
        self.nav_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        self.create_nav_buttons()

        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.listing_frame = ttk.Frame(self.content_frame)
        self.listing_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.edit_frame = ttk.Frame(self.content_frame)
        self.edit_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    def create_nav_buttons(self):
        canvas = tk.Canvas(self.nav_frame)
        scrollbar = ttk.Scrollbar(self.nav_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for model_class in Base.__subclasses__():
            if hasattr(model_class, '__tablename__'):
                button = ttk.Button(scrollable_frame, text=model_class.__tablename__.capitalize().ljust(35))
                button.config(command=lambda m=model_class, b=button: self.load_views(m, b))
                button.pack(fill=tk.X, pady=2)
                button.bind("<Enter>", lambda e, b=button: b.config(cursor="hand2"))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mouse wheel to scroll
        canvas.bind("<Enter>", lambda e: self._bind_mouse_wheel(canvas))
        canvas.bind("<Leave>", lambda e: self._unbind_mouse_wheel(canvas))

    def _bind_mouse_wheel(self, widget):
        widget.bind_all("<MouseWheel>", lambda event: self._on_mouse_wheel(event, widget))

    def _unbind_mouse_wheel(self, widget):
        widget.unbind_all("<MouseWheel>")

    def _on_mouse_wheel(self, event, widget):
        widget.yview_scroll(int(-1*(event.delta/120)), "units")

    def load_views(self, model_class, button):
        from gui.views import ListingView, EditView  # Import here to avoid circular import
        for widget in self.listing_frame.winfo_children():
            widget.destroy()
        for widget in self.edit_frame.winfo_children():
            widget.destroy()

        if self.active_button:
            self.active_button.config(style='TButton')
        button.config(style='success.TButton')
        self.active_button = button

        self.listing_controller = GUIController(ListingView, model_class)
        self.listing_controller.load_view(self.listing_frame)

        self.edit_controller = GUIController(EditView, model_class)
        self.edit_controller.load_view(self.edit_frame)

        self.listing_controller.set_edit_controller(self.edit_controller)
