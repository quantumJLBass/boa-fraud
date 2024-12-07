import tkinter as tk
from ttkbootstrap import Style
from ttkbootstrap.constants import *
from ttkbootstrap import ttk
from ttkbootstrap.tooltip import ToolTip
from ttkbootstrap.tableview import Tableview
from tkcalendar import DateEntry
from sqlalchemy import DateTime
import gs

class GUIView(tk.Frame):
    """Base class for GUI views."""
    def __init__(self, parent, controller, model_class):
        super().__init__(parent)
        self.controller = controller
        self.model_class = model_class
        self.style = ttk.Style()  # Add this line to initialize the style
        self.create_widgets()

    def create_widgets(self):
        """_summary_

        Raises:
            NotImplementedError: _description_
        """
        raise NotImplementedError("Subclasses must implement create_widgets method.")

class ListingView(GUIView):
    """View for listing records in a table."""
    def __init__(self, parent, controller, model_class):
        self.records = []
        self.page_size = tk.StringVar(value="10")  # Default page size
        self.total_records = 0
        super().__init__(parent, controller, model_class)

    def create_widgets(self):
        """_summary_
        """
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.list_frame = ttk.Frame(self.notebook)
        self.edit_frame = EditView(self.notebook, self.controller, self.model_class)

        self.notebook.add(self.list_frame, text="List")
        self.notebook.add(self.edit_frame, text="Edit")

        # Page size selection
        page_size_label = ttk.Label(self.list_frame, text="Page Size:")
        page_size_label.pack(side=tk.LEFT, padx=5, pady=5)

        page_size_combobox = ttk.Combobox(self.list_frame, textvariable=self.page_size, values=["10", "25", "50", "100", "ALL"], state="readonly")
        page_size_combobox.pack(side=tk.LEFT, padx=5, pady=5)
        page_size_combobox.bind("<<ComboboxSelected>>", self.on_page_size_change)

        self.progress = ttk.Progressbar(self.list_frame, mode='indeterminate')
        self.progress.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.table = Tableview(
            master=self.list_frame,
            coldata=[
                {"text": column.name, "stretch": False}
                for column in self.model_class.__table__.columns
                if column.name not in self.get_hidden_columns()
            ] + [{"text": "Actions", "stretch": False}],  # Ensure the "Actions" column is included
            rowdata=[],
            paginated=True,
            searchable=False,
            autofit=True,
            autoalign=True,
            bootstyle=PRIMARY,
            pagesize=int(self.page_size.get()),  # Page size is set here
            height=10,  # Adjust as needed
            stripecolor=(gs.appcolors.light, None)
        )
        self.table.pack(fill=tk.BOTH, expand=True)

        self.table.bind("<<PageChanged>>", self.on_page_changed)
        self.table.bind("<<TreeviewSelect>>", self.on_record_select)

        self.load_records()

    def get_hidden_columns(self):
        """Return a list of columns to be hidden based on the model class."""
        return getattr(self.model_class, "__hidden_columns__", [])

    def on_page_size_change(self, event):
        """_summary_

        Args:
            event (_type_): _description_
        """
        new_page_size = int(self.page_size.get()) if self.page_size.get() != "ALL" else len(self.records)
        self.table.pagesize = new_page_size  # Update pagesize directly
        self.table.load_table_data()  # Reload the table with the new page size
        self.add_action_buttons()  # Re-add action buttons if needed

    def load_records(self):
        """_summary_
        """
        self.progress.start()
        self.after(100, self._load_records)

    def _load_records(self):
        """
        
        """
        with gs.read() as session:
            self.total_records = session.query(self.model_class).count()
            self.records = session.query(self.model_class).all()
            # Materialize the data while in the session
            self.rowdata = []
            for record in self.records:
                values = [getattr(record, column.name) for column in self.model_class.__table__.columns if column.name not in self.get_hidden_columns()]
                values.append("")  # Placeholder for Actions column
                self.rowdata.append(values)

        self.populate_table()
        self.progress.stop()

    def populate_table(self):
        """_summary_
        """
        print(f"Number of records: {len(self.rowdata)}")
        print(f"Rowdata: {self.rowdata}")

        # Prepare coldata
        coldata = [
            {"text": column.name, "stretch": False}
            for column in self.model_class.__table__.columns
            if column.name not in self.get_hidden_columns()
        ] + [{"text": "Actions", "stretch": False}]

        # Clear the table and insert new data
        self.table.purge_table_data()

        for index, row_data in enumerate(self.rowdata):
            print(f"Inserting row {index} with data: {row_data}")
            self.table.insert_row('end', row_data)  # Insert row without manually setting iid

        # Reload the table data
        self.table.build_table_data(coldata, self.rowdata)
        self.table.load_table_data()

        # Print the rows after insertion to check their iid
        for row in self.table.get_rows():
            print(f"Row after insertion: {row.iid}, Data: {row.values}")

        # After table is populated, add action buttons
        self.add_action_buttons()



    def on_page_changed(self, event):
        """_summary_

        Args:
            event (_type_): _description_
        """
        self.add_action_buttons()


    def add_action_buttons(self):
        """_summary_
        """
        for row in self.table.get_rows(visible=True):
            if row.iid is None:
                print(f"Skipping row with None iid: {row.values}")
                continue  # Skip rows with None iid

            record_id = row.values[0]  # Get the first value in the row which represents the record ID

            # Create clickable text links for Edit and Delete actions
            edit_link = "Edit"
            delete_link = "Delete"

            # Concatenate links to a single string
            action_links = f"{edit_link} | {delete_link}"

            # Set the action links in the "Actions" column
            self.table.view.set(row.iid, len(row.values) - 1, action_links)

            # Bind the event specifically to the "Actions" column for each row
            self.table.view.tag_bind(row.iid, '<Button-1>', lambda e, r=record_id: self.on_action_click(e, r))

    def on_action_click(self, event, record_id):
        """_summary_

        Args:
            event (_type_): _description_
            record_id (_type_): _description_

        Returns:
            _type_: _description_
        """
        # Get the clicked item and column
        item_id = self.table.view.identify_row(event.y)
        column = self.table.view.identify_column(event.x)

        if not item_id or column != f"#{len(self.table.view['columns'])}":
            return  # Ensure we are clicking on the "Actions" column

        # Get the action text (Edit | Delete)
        action_text = self.table.view.item(item_id, "values")[-1]

        # Check if the user clicked on "Edit" or "Delete"
        if "Edit" in action_text and event.x < (event.width / 2):  # Clicked near the first half of the action links
            print(f"Editing record ID: {record_id}")
            self.edit_record(record_id)
        elif "Delete" in action_text:
            print(f"Deleting record ID: {record_id}")
            self.delete_record(record_id)


    def edit_record(self, record_id):
        """_summary_

        Args:
            record_id (_type_): _description_
        """
        self.edit_frame.populate(self.controller.get_record(self.model_class, record_id))
        self.notebook.select(self.edit_frame)

    def delete_record(self, record_id):
        """_summary_

        Args:
            record_id (_type_): _description_
        """
        self.controller.delete_record(self.model_class, record_id)
        self.load_records()

    def on_record_select(self, event):
        """_summary_

        Args:
            event (_type_): _description_

        Returns:
            _type_: _description_
        """
        selected_item = self.table.focus()
        if not selected_item:
            return  # Exit if no item is selected

        record_id = self.table.view.item(selected_item)['values'][0]
        self.edit_record(record_id)


class EditView(GUIView):
    """Generic view for editing records in non-relationship tables."""
    def __init__(self, parent, controller, model_class):
        self.record_id = None
        self.entries = {}
        super().__init__(parent, controller, model_class)

    def create_widgets(self):
        """
        Creates the widgets for the edit view, including labels, entries, and buttons.

        This method is responsible for setting up the form frame, creating labels and entries for each column in the model class,
        and adding save and cancel buttons.
        """
        self.form_frame = ttk.Frame(self)
        self.form_frame.pack(fill=tk.BOTH, expand=True)

        for i, column in enumerate(self.model_class.__table__.columns):
            column_name = column.name
            if column_name == 'id':
                continue

            label = ttk.Label(self.form_frame, text=column_name.capitalize() + ":")
            label.grid(row=i, column=0, sticky="e", padx=5, pady=5)

            if isinstance(column.type, DateTime):
                entry = DateEntry(self.form_frame)
            else:
                entry = ttk.Entry(self.form_frame)

            entry.grid(row=i, column=1, padx=5, pady=5)
            self.entries[column_name] = entry

        save_button = ttk.Button(self.form_frame, text="Save", command=self.save_record)
        save_button.grid(row=len(self.model_class.__table__.columns), column=0, columnspan=2, padx=5, pady=10)

        cancel_button = ttk.Button(self.form_frame, text="Cancel", command=self.cancel_edit)
        cancel_button.grid(row=len(self.model_class.__table__.columns) + 1, column=0, columnspan=2, padx=5, pady=10)

    def populate(self, record):
        """
        Populates the edit view with data from the given record.

        This method sets the record ID and then populates each entry field with the corresponding value from the record.

        Args:
            record: The record to populate the view with.
        """
        self.record_id = record.id
        for column_name, entry in self.entries.items():
            value = getattr(record, column_name)
            entry.delete(0, tk.END)
            entry.insert(0, value)

    def save_record(self):
        """
        Saves the edited record.

        This method retrieves the data from the entry fields, saves the record using the controller, and then refreshes the listing view.
        """
        data = {}
        for column_name, entry in self.entries.items():
            data[column_name] = entry.get()

        self.controller.save_record(self.model_class, self.record_id, data)
        self.controller.refresh_listing_view()
        self.cancel_edit()

    def cancel_edit(self):
        """
        Cancels the edit operation.

        This method resets the record ID, clears the entry fields, and then selects the listing frame.
        """
        self.record_id = None
        for entry in self.entries.values():
            entry.delete(0, tk.END)
        self.master.select(self.master.list_frame)