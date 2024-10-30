import gs
from sqlalchemy.exc import SQLAlchemyError
from services.applogging import logger
import traceback
import tkinter as tk
from ttkbootstrap import ttk

class GUIController:
    """Base class for GUI controllers."""
    def __init__(self, view_class, model_class):
        self.view_class = view_class
        self.model_class = model_class
        self.view = None

    def load_view(self, parent):
        if self.view:
            self.view.destroy()
        self.view = self.view_class(parent, self, self.model_class)
        self.view.pack(fill=tk.BOTH, expand=True)

    def show_listing_view(self, model_class):
        self.view.destroy()
        self.view = ListingView(self.view.master, self, model_class)
        self.view.pack(fill=tk.BOTH, expand=True)
        self.view.load_records()

    def show_edit_view(self, model_class, record_id):
        self.view.destroy()
        self.view = EditView(self.view.master, self, model_class, record_id)
        self.view.pack(fill=tk.BOTH, expand=True)

    def get_record(self, model_class, record_id):
        """
        Retrieve a record from the database by ID.

        Parameters
        ----------
        model_class : sqlalchemy.ext.declarative.DeclarativeMeta
            The class of the model to retrieve a record from.
        record_id : int
            The ID of the record to retrieve.

        Returns
        -------
        sqlalchemy.ext.declarative.DeclarativeMeta
            The retrieved record, or None if no record was found.
        """
        with gs.read() as readsession:
            record = readsession.query(model_class).get(record_id)
            return record

    def get_all_records(self, model_class):
        """
        Retrieve all records from the database.

        Parameters
        ----------
        model_class : sqlalchemy.ext.declarative.DeclarativeMeta
            The class of the model to retrieve records from.

        Returns
        -------
        list
            A list of records of the given model class.
        """
        with gs.read() as readsession:
            records = readsession.query(model_class).all()
            return records

    def save_record(self, model_class, record_id, data):
        """
        Save a record to the database, either by updating an existing record
        or creating a new one.

        Parameters
        ----------
        model_class : sqlalchemy.ext.declarative.DeclarativeMeta
            The class of the model to save a record of.
        record_id : int
            The ID of the record to update, or None if a new record should be created.
        data : dict
            A dictionary of column names and values to be saved.

        Returns
        -------
        None
        """
        # do not try and delete!!!  ?? need to explain why this is here... this seems like we should be using the ORM correctly and not using gs.write directly?
        try:
            with gs.write() as writesession:
                if record_id:
                    record = writesession.query(model_class).get(record_id)
                    for key, value in data.items():
                        setattr(record, key, value)
                else:
                    record = model_class(**data)
                writesession.add(record)
                writesession.commit()
        except SQLAlchemyError as e:
            logger.error(f"💥🚩 Error cataloging {model_class.__name__} data: {e}")
            logger.error(f"{traceback.format_exc()}")
            with gs.write() as writesession:
                writesession.rollback()
        except Exception as e:
            logger.error(f"💥🚩 Error cataloging {model_class.__name__} data: {e}")
            logger.error(f"{traceback.format_exc()}")
            with gs.write() as writesession:
                writesession.rollback()

    def load_edit_view(self, record_id):
        """
        Load the edit view with the given record ID.

        Parameters
        ----------
        record_id : int
            The ID of the record to load into the edit view.

        Returns
        -------
        None
        """
        with gs.read() as session:
            record = session.query(self.model_class).get(record_id)
            self.edit_controller.view.populate(record)

    def set_edit_controller(self, edit_controller):
        """
        Set the edit controller to use for loading edit views.

        Parameters
        ----------
        edit_controller : GUIController
            The edit controller to use.

        Returns
        -------
        None
        """
        self.edit_controller = edit_controller

    def refresh_listing_view(self):
        """
        Reload the records in the listing view.

        Returns
        -------
        None
        """
        self.view.load_records()

