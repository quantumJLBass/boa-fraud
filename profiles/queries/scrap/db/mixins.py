import traceback
from typing import Any, List, Optional, Union

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    Row,
    UniqueConstraint,
    event,
    insert,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Mapped, Session, declared_attr
from sqlalchemy.sql import and_, func, or_, text
from sqlalchemy.sql.elements import TextClause

import gs
from services.applogging import logger
from settings.settings import i


def convert_row_to_orm_instance(
    row_obj: Row, cls: object, session: Session
) -> Optional[object]:
    """
    Converts a SQLAlchemy Row object to its corresponding ORM instance by fetching it
    from the database using its primary key.

    This function attempts to convert a SQLAlchemy Row object to an ORM instance.
    If the input is already an ORM instance or not a Row object, it returns the input unchanged.
    If conversion fails, it returns None.

    Args:
        row_obj (Row): The SQLAlchemy Row object to convert.
        cls (object): The ORM class representing the table.
        session (Session): The SQLAlchemy session to use for fetching the ORM instance.

    Returns:
        Optional[object]: The corresponding ORM instance if found, otherwise None.

    Raises:
        SQLAlchemyError: If there's an error during the database query.

    Example:
        >>> from sqlalchemy.orm import Session
        >>> from your_orm_module import YourORMClass
        >>> session = Session()
        >>> row = session.execute("SELECT * FROM your_table LIMIT 1").fetchone()
        >>> orm_instance = convert_row_to_orm_instance(row, YourORMClass, session)
        >>> print(orm_instance)
    """
    logger.info(f"{i()} Converting a row to an ORM instance")
    if not isinstance(row_obj, Row):
        logger.debug(f"{i()} Input is not a Row object, returning as is")
        return row_obj  # It's already an ORM instance or not a Row, so no conversion needed

    try:
        # Dynamically fetch the primary key columns for the class
        mapper = inspect(cls)
        primary_key_columns = mapper.primary_key

        if not primary_key_columns:
            logger.error(
                f"{i()} No primary key defined for {cls.__name__}. Cannot convert Row to ORM instance."
            )
            return None

        # Build a condition to fetch the ORM instance using the primary key values from the Row object
        primary_key_conditions = {
            pk.name: getattr(row_obj, pk.name) for pk in primary_key_columns
        }

        # Fetch the ORM instance based on the primary key conditions
        orm_instance = session.query(cls).filter_by(**primary_key_conditions).first()

        if not orm_instance:
            logger.error(
                f"{i()} Could not convert Row to ORM instance for {cls.__name__}."
            )
            return None

        logger.debug(
            f"{i()} Successfully converted Row to ORM instance for {cls.__name__}"
        )
        return orm_instance

    except SQLAlchemyError as e:
        logger.error(f"{i()} SQLAlchemy error during Row to ORM conversion: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"{i()} Unexpected error during Row to ORM conversion: {str(e)}")
        return None


def set_attributes(instance: object, data: dict) -> None:
    """
    Sets the attributes of an instance based on a dictionary of data.
    This function expects an ORM instance, not a raw SQLAlchemy Row object.

    Args:
        instance (object): The ORM instance to update.
        data (dict): The data to set on the instance.

    Raises:
        TypeError: If the instance is a SQLAlchemy Row object instead of an ORM instance.

    Example:
        >>> from your_orm_module import YourORMClass
        >>> instance = YourORMClass()
        >>> data = {"attribute1": "value1", "attribute2": "value2"}
        >>> set_attributes(instance, data)
        >>> print(instance.attribute1)  # Output: value1
    """
    logger.info(f"{i()} Setting attributes of an ORM instance")
    if isinstance(instance, Row):
        logger.error(f"{i()} Attempted to set attributes on a SQLAlchemy Row object")
        raise TypeError(
            "Cannot set attributes on SQLAlchemy Row object. Expected ORM instance."
        )

    for key, value in data.items():
        if hasattr(instance, key):
            setattr(instance, key, value)
            logger.debug(f"{i()} Set attribute {key} to {value} on {type(instance)}")
        else:
            logger.warning(f"{i()} Attribute {key} not found on {type(instance)}")


def build_conditions(where: Union[str, List[Union[str, Any]]]) -> List[Any]:
    """
    Builds SQLAlchemy conditions from a structured list or string.

    This function processes various input formats to create SQLAlchemy conditions
    that can be used in queries. It handles both raw SQL strings and SQLAlchemy expressions,
    as well as nested conditions with OR and AND logic.

    Args:
        where (Union[str, List[Union[str, Any]]]): The input where conditions that can be provided in multiple formats.
            - A string: Raw SQL condition.
            - A list: A list of SQLAlchemy expressions or raw SQL conditions.

    Returns:
        List[Any]: A list of SQLAlchemy conditions to use in queries.

    Raises:
        TypeError: If an unsupported condition type is provided.

    Example:
        >>> conditions = build_conditions(["column1 = 'value1'", "| column2 > 5", ["& column3 < 10", "column4 IS NOT NULL"]])
        >>> print(conditions)
    """
    conditions = []
    logger.info(f"{i()} Building the where conditions")

    if isinstance(where, (str, TextClause)):
        where = [where]  # Handle the case where a single string condition is provided

    for condition in where:
        if isinstance(condition, list):
            # For sub-conditions, recursively handle `|` and `&`
            sub_conditions = []
            for c in condition:
                if isinstance(c, str):
                    # Explicitly declare string SQL conditions as text and handle OR/AND logic
                    sub_conditions.append(text(c.lstrip("|&")))
                else:
                    sub_conditions.append(c)
            conditions.append(
                or_(*sub_conditions)
                if "|" in str(condition[0])
                else and_(*sub_conditions)
            )
        elif isinstance(condition, str):
            # Handle OR/AND logic for string conditions
            if condition.startswith("| "):
                conditions.append(or_(text(condition.lstrip("| "))))
            elif condition.startswith("& "):
                conditions.append(and_(text(condition.lstrip("& "))))
            else:
                conditions.append(and_(text(condition)))
        else:
            # Assume condition is an SQLAlchemy clause or expression
            conditions.append(condition)

    logger.debug(f"{i()} Built conditions: {conditions}")
    return conditions


def build_conditions_from_unique_constraints(cls, data: dict) -> List:
    """
    Builds filter conditions based on the unique constraints or primary keys of the table.

    This function examines the given SQLAlchemy model class and the provided data
    to construct a list of conditions that can be used to uniquely identify a record.
    It prioritizes primary key columns, falling back to unique constraints if necessary.

    Args:
        cls: The SQLAlchemy model class.
        data (dict): The data to build conditions from.

    Returns:
        List: A list of SQLAlchemy conditions based on unique constraints or primary keys.

    Example:
        >>> from your_orm_module import YourORMClass
        >>> data = {"id": 1, "name": "example"}
        >>> conditions = build_conditions_from_unique_constraints(YourORMClass, data)
        >>> print(conditions)
    """
    conditions = []
    mapper = inspect(cls)
    logger.info(f"{i()} Building conditions from unique constraints for {cls.__name__}")

    # Get the table associated with the model class
    table = cls.__table__

    # Build conditions based on primary key columns
    primary_key_columns = [col.name for col in mapper.primary_key]
    if all(key in data for key in primary_key_columns):
        for key in primary_key_columns:
            conditions.append(getattr(cls, key) == data[key])
        logger.debug(
            f"{i()} Built conditions using primary key columns: {primary_key_columns}"
        )
    else:
        # Build conditions based on unique constraints
        unique_constraints = [
            constraint
            for constraint in table.constraints
            if isinstance(constraint, UniqueConstraint)
        ]
        for constraint in unique_constraints:
            constraint_columns = [col.name for col in constraint.columns]
            if all(col in data for col in constraint_columns):
                for col in constraint_columns:
                    conditions.append(getattr(cls, col) == data[col])
                logger.debug(
                    f"{i()} Built conditions using unique constraint: {constraint_columns}"
                )
                break  # Use the first matching unique constraint

    if not conditions:
        logger.warning(
            f"{i()} No conditions could be built from unique constraints or primary keys"
        )

    return conditions


class CatalogMixin:
    """
    Mixin class for cataloging and fetching records from a database table.

    This mixin provides a set of methods for common database operations such as
    inserting, updating, and retrieving records. It includes features like
    automatic 'asof' date handling, dynamic attribute access, and bulk operations.

    Attributes:
        asof (Mapped[Date]): A column representing the 'as of' date for each record.

    Note:
        This mixin assumes the use of SQLAlchemy ORM and requires a properly configured
        database session to function correctly.
    """

    @declared_attr
    def asof(self) -> Mapped[Date]:
        """
        Declares the 'asof' column for the model.

        This method uses SQLAlchemy's declared_attr to dynamically create an 'asof' column
        for each model that includes this mixin. The column is set to be non-nullable and
        defaults to the current date.

        Returns:
            Mapped[Date]: A SQLAlchemy Column object representing the 'asof' date.

        Note:
            - The column is non-nullable and defaults to the current date.
            - This uses SQLAlchemy's declared_attr to allow for dynamic column creation.
        """
        return Column(Date, nullable=False, default=func.current_date())

    @classmethod
    def __declare_last__(cls):
        """
        Sets up event listeners for the model.

        This method is called after all table-level attributes are defined.
        It sets up SQLAlchemy event listeners to automatically update the 'asof' column
        before insert and update operations.

        Note:
            - The 'before_insert' and 'before_update' events are used to ensure 'asof' is always current.
            - This method uses SQLAlchemy's event system for automatic attribute updates.
        """

        @event.listens_for(cls, "before_insert")
        @event.listens_for(cls, "before_update")
        def set_asof(_mapper, _connection, target):
            """
            Event listener to set the 'asof' attribute before insert or update.

            This function is automatically called by SQLAlchemy before insert and update operations.
            It ensures that the 'asof' field always contains the current date.

            Args:
                _mapper: The Mapper object (unused in this function)
                _connection: The Connection object (unused in this function)
                target: The model instance being inserted or updated

            Note:
                - This function is called automatically by SQLAlchemy before insert and update operations.
                - It ensures that the 'asof' field always contains the current date.
            """
            target.asof = func.current_date()

    @declared_attr
    def __table_args__(self) -> tuple:
        """
        Declares table arguments for the model.

        This method adds a CheckConstraint to ensure the 'asof' column follows the YYYY-MM-DD format.
        The constraint uses a GLOB pattern to validate the date format, helping maintain data integrity.

        Returns:
            tuple: A tuple containing SQLAlchemy table arguments.

        Note:
            - This method adds a CheckConstraint to ensure the 'asof' column follows the YYYY-MM-DD format.
            - The constraint uses a GLOB pattern to validate the date format.
            - This helps maintain data integrity by preventing invalid date formats.
        """
        return (
            CheckConstraint(
                "asof GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]'",
                name="asof_date_format",
            ),
        )

    def get(self, column_name: str) -> Optional[Any]:
        """
        Gets the value of a column dynamically.

        This method attempts to retrieve the value of a specified column from the current instance.
        It includes comprehensive error handling and logging to ensure robustness and provide
        detailed information for debugging purposes.

        Args:
            column_name (str): The name of the column to get.

        Returns:
            Optional[Any]: The value of the column if it exists, otherwise None.

        Raises:
            AttributeError: If there's an error accessing the attribute.
            Exception: For any other unexpected errors during the get process.

        Note:
            - All exceptions are caught and logged.
            - The method uses the global indentation function `i()` for consistent log formatting.
            - If the column doesn't exist, a warning is logged and None is returned.
        """
        logger.info(
            f"{i()} Attempting to get value of {column_name} from {self.__class__.__name__}"
        )
        try:
            if hasattr(self, column_name):
                value = getattr(self, column_name)
                logger.info(
                    f"{i()} Successfully got {column_name} value {value} from {self.__class__.__name__}"
                )
                return value
            else:
                logger.warning(
                    f"{i()} Column {column_name} does not exist on {self.__class__.__name__}"
                )
                return None
        except AttributeError as e:
            logger.error(f"{i()} AttributeError while getting {column_name}: {e}")
            logger.error(f"{i()} Traceback: {traceback.format_exc()}")
            return None
        except Exception as e:
            logger.error(f"{i()} Unexpected error while getting {column_name}: {e}")
            logger.error(f"{i()} Traceback: {traceback.format_exc()}")
            return None

    def set(self, column_name: str, value: Any, session: Session) -> None:
        """
        Sets the value of a column dynamically and saves the instance.

        This method attempts to set the value of a specified column on the current instance
        and then save the changes to the database. It includes comprehensive error handling
        and logging to ensure robustness and provide detailed information for debugging purposes.

        Args:
            column_name (str): The name of the column to set.
            value (Any): The value to set for the column.
            session (Session): The SQLAlchemy session to use for saving.

        Raises:
            AttributeError: If the specified column does not exist on the instance.
            SQLAlchemyError: If there's an error during the database operation.
            Exception: For any other unexpected errors during the set and save process.

        Note:
            - All exceptions are caught and logged.
            - The method uses the global indentation function `i()` for consistent log formatting.
            - If the column doesn't exist, a warning is logged and no changes are made.
            - The session is rolled back in case of any errors during the save operation.
        """
        logger.info(
            f"{i()} Attempting to set {column_name} on {self.__class__.__name__}"
        )
        try:
            if hasattr(self, column_name):
                # Set the attribute value
                setattr(self, column_name, value)
                logger.info(
                    f"{i()} Set {column_name} to {value} on {self.__class__.__name__}"
                )

                # Attempt to save the instance
                self.save(session)
                logger.info(
                    f"{i()} Successfully saved {self.__class__.__name__} after setting {column_name}"
                )
            else:
                logger.warning(
                    f"{i()} Column {column_name} does not exist on {self.__class__.__name__}. No changes made."
                )
        except AttributeError as e:
            logger.error(f"{i()} AttributeError while setting {column_name}: {e}")
            logger.error(f"{i()} Traceback: {traceback.format_exc()}")
        except SQLAlchemyError as e:
            logger.error(
                f"{i()} SQLAlchemy error while saving after setting {column_name}: {e}"
            )
            logger.error(f"{i()} Traceback: {traceback.format_exc()}")
            session.rollback()
            logger.info(f"{i()} Session rolled back due to SQLAlchemy error")
        except Exception as e:
            logger.error(
                f"{i()} Unexpected error while setting {column_name} or saving: {e}"
            )
            logger.error(f"{i()} Traceback: {traceback.format_exc()}")
            session.rollback()
            logger.info(f"{i()} Session rolled back due to unexpected error")
        finally:
            logger.debug(
                f"{i()} Set operation completed for {column_name} on {self.__class__.__name__}"
            )

    def save(self, session: Session) -> None:
        """
        Saves the current instance to the database.

        This method attempts to add the current instance to the provided SQLAlchemy session
        and commit the changes. It includes comprehensive error handling and logging to ensure
        robustness and provide detailed information for debugging purposes.

        Args:
            session (Session): The SQLAlchemy session to use for saving the instance.

        Raises:
            SQLAlchemyError: If there's an error during the database operation.
            Exception: For any other unexpected errors during the save process.

        Note:
            - All exceptions are caught, logged, and the session is rolled back in case of errors.
            - The method uses the global indentation function `i()` for consistent log formatting.
            - The session is rolled back in case of any errors during the save operation.
        """
        logger.info(
            f"{i()} Attempting to save {self.__class__.__name__} instance to the database"
        )
        try:
            # Add the instance to the session
            session.add(self)
            logger.debug(
                f"{i()} Added {self.__class__.__name__} instance to the session"
            )

            # Commit the changes
            session.commit()
            logger.info(
                f"{i()} Successfully saved {self.__class__.__name__} instance to the database"
            )

        except SQLAlchemyError as e:
            # Handle SQLAlchemy-specific errors
            logger.error(
                f"{i()} SQLAlchemy error saving {self.__class__.__name__} instance: {e}"
            )
            logger.error(f"{i()} Traceback: {traceback.format_exc()}")
            session.rollback()
            logger.info(f"{i()} Session rolled back due to SQLAlchemy error")

        except Exception as e:
            # Handle any other unexpected errors
            logger.error(
                f"{i()} Unexpected error saving {self.__class__.__name__} instance: {e}"
            )
            logger.error(f"{i()} Traceback: {traceback.format_exc()}")
            session.rollback()
            logger.info(f"{i()} Session rolled back due to unexpected error")

        finally:
            logger.debug(
                f"{i()} Save operation completed for {self.__class__.__name__} instance"
            )

    @classmethod
    def update_instance(
        cls, session: Session, instance_id: Any, data: dict
    ) -> Optional[object]:
        """
        Updates an existing instance with new data.

        This method attempts to update an existing instance of the class with the provided data.
        It first retrieves the instance using the given ID, then updates each attribute specified
        in the data dictionary. The method uses error handling to ensure robustness and provides
        detailed logging for monitoring and debugging purposes.

        Args:
            session (Session): The SQLAlchemy session to use for database operations.
            instance_id (Any): The primary key of the instance to update.
            data (dict): A dictionary containing the data to update on the instance.
                         Keys should correspond to column names, and values to the new data.

        Returns:
            Optional[object]: The updated instance if found and successfully updated, otherwise None.

        Raises:
            SQLAlchemyError: If there's an error during the database operation.
            Exception: For any other unexpected errors during the update process.

        Note:
            - This method uses the `set` method to update individual attributes, which handles
              logging and error checking for each attribute update.
            - If the instance is not found, a warning is logged, and None is returned.
            - All exceptions are caught, logged, and the session is rolled back in case of errors.
        """
        logger.info(
            f"{i()} Attempting to update {cls.__name__} instance with id {instance_id}"
        )
        try:
            instance = session.query(cls).get(instance_id)
            if instance:
                logger.debug(
                    f"{i()} Found {cls.__name__} instance with id {instance_id}"
                )
                for key, value in data.items():
                    instance.set(key, value, session)
                session.commit()
                logger.info(
                    f"{i()} Successfully updated {cls.__name__} instance with id {instance_id}"
                )
                return instance
            else:
                logger.warning(
                    f"{i()} {cls.__name__} instance with id {instance_id} not found"
                )
                return None
        except SQLAlchemyError as e:
            logger.error(
                f"{i()} SQLAlchemy error updating {cls.__name__} instance with id {instance_id}: {e}"
            )
            logger.error(traceback.format_exc())
            session.rollback()
            return None
        except Exception as e:
            logger.error(
                f"{i()} Unexpected error updating {cls.__name__} instance with id {instance_id}: {e}"
            )
            logger.error(traceback.format_exc())
            session.rollback()
            return None

    @classmethod
    def catalog(
        cls,
        data: dict,
        where: List[Union[str, Any]] = None,
        conflict_resolution: str = "IGNORE",
    ) -> Union[Any, None]:
        """
        Catalog a record in the table, either by updating an existing record or creating a new one.
        Supports SQLite conflict resolution strategies.

        This method provides a flexible way to insert or update a single record in the database.
        It first checks if a record exists based on the provided conditions or unique constraints,
        then either updates the existing record or inserts a new one. The method supports various
        SQLite conflict resolution strategies for handling potential conflicts during insertion.

        Args:
            data (dict): The record data to be cataloged.
            where (List[Union[str, Any]], optional): The conditions for fetching the record.
                If not provided, conditions are built from unique constraints. Defaults to None.
            conflict_resolution (str, optional): Conflict resolution strategy for SQLite.
                Options are "IGNORE", "REPLACE", or "NONE". Defaults to "IGNORE".

        Returns:
            Union[Any, None]: The cataloged record (ORM instance) if successful, None on failure.

        Raises:
            ValueError: If the data dictionary is empty.
            SQLAlchemyError: If there's an error during the database operation.
            Exception: For any other unexpected errors during the operation.

        Note:
            - This method uses a write session from the global state (gs.write).
            - All exceptions are caught, logged, and the session is rolled back in case of errors.
            - The method supports both updating existing records and inserting new ones.
            - When inserting, it can use SQLite's conflict resolution strategies.
        """
        try:
            if not data:
                raise ValueError("Data dictionary must be provided.")

            logger.info(f"{i()} Attempting to catalog {cls.__name__} record.")

            # Step 1: Check if the record already exists
            existing_record = cls.fetch(
                where=(
                    build_conditions(where)
                    if where
                    else build_conditions_from_unique_constraints(cls, data)
                ),
                limit=1,
            )

            # Step 2: Insert or update
            with gs.write() as session:
                if existing_record:
                    # Convert existing record from Row to ORM instance (if it's a Row)
                    existing_record = convert_row_to_orm_instance(
                        existing_record, cls, session
                    )

                    # Update existing record
                    logger.info(
                        f"{i()} Updating existing {cls.__name__} record with data: {data}"
                    )
                    set_attributes(existing_record, data)
                    session.merge(existing_record)
                    result = existing_record
                else:
                    # Insert new record
                    logger.info(f"{i()} Inserting a new record into {cls.__name__}")
                    new_record = cls(**data)
                    if conflict_resolution.upper() != "NONE":
                        columns = list(data.keys())
                        placeholders = ", ".join([f":{col}" for col in columns])
                        query = f"""
                        INSERT OR {conflict_resolution.upper()} INTO {cls.__tablename__} ({', '.join(columns)})
                        VALUES ({placeholders})
                        """
                        logger.debug(
                            f"{i()} Executing query with conflict clause: {query}"
                        )
                        session.execute(text(query), data)
                    else:
                        session.add(new_record)
                    result = new_record

                session.commit()
                logger.info(
                    f"{i()} Successfully {'updated' if existing_record else 'inserted'} {cls.__name__} record"
                )
                return result

        except ValueError as ve:
            logger.error(f"{i()} ValueError in cataloging {cls.__name__} data: {ve}")
            logger.error(traceback.format_exc())
        except SQLAlchemyError as e:
            logger.error(
                f"{i()} SQLAlchemyError in cataloging {cls.__name__} data: {e}"
            )
            logger.error(traceback.format_exc())
            with gs.write() as session:
                session.rollback()
        except Exception as e:
            logger.error(
                f"{i()} Unexpected error in cataloging {cls.__name__} data: {e}"
            )
            logger.error(traceback.format_exc())
            with gs.write() as session:
                session.rollback()

        logger.warning(f"{i()} Failed to catalog {cls.__name__} record.")
        return None

    @classmethod
    def bulk_catalog(
        cls,
        records: List[dict],
        where: List[Union[str, Any]] = None,
        additional_params: dict = None,
        conflict_resolution: str = "IGNORE",
    ) -> None:
        """
        Bulk catalog records into the table, handling inserts and updates.
        Supports conflict resolution and optimized bulk operations.

        This method provides an efficient way to insert or update multiple records
        in a single database operation. It supports various conflict resolution
        strategies and can handle additional parameters to be merged into each record.

        Args:
            records (List[dict]): List of dictionaries, each representing a record to be cataloged.
            where (List[Union[str, Any]], optional): List of SQL conditions for bulk operation.
                Can be used for more complex update operations. Defaults to None.
            additional_params (dict, optional): Additional parameters to merge into each record.
                Useful for adding common fields to all records. Defaults to None.
            conflict_resolution (str, optional): Conflict resolution strategy for SQLite.
                Options are "IGNORE", "REPLACE", or "NONE". Defaults to "IGNORE".

        Raises:
            SQLAlchemyError: If there's an error during the database operation.
            ValueError: If an invalid conflict_resolution strategy is provided.
            Exception: For any other unexpected errors during the operation.

        Note:
            - This method uses a write session from the global state (gs.write).
            - All exceptions are caught, logged, and the session is rolled back in case of errors.
            - The method doesn't return any value but logs the outcome of the operation.
            - The method uses the global indentation function `i()` for consistent log formatting.
            - Supports different conflict resolution strategies for handling duplicate records.
            - Can apply additional parameters to all records being cataloged.
        """
        try:
            logger.info(
                f"{i()} Bulk cataloging {len(records)} records for {cls.__name__}."
            )

            if not records:
                logger.warning(f"{i()} No records to catalog for {cls.__name__}.")
                return

            if additional_params:
                logger.info(f"{i()} Merging additional params: {additional_params}")
                records = [{**record, **additional_params} for record in records]

            with gs.write() as session:
                if conflict_resolution.upper() not in ["NONE", "IGNORE", "REPLACE"]:
                    raise ValueError(
                        f"Invalid conflict resolution strategy: {conflict_resolution}"
                    )

                if conflict_resolution.upper() == "NONE":
                    logger.info(
                        f"{i()} Using bulk_save_objects for inserting new records only."
                    )
                    session.bulk_save_objects([cls(**record) for record in records])
                else:
                    logger.info(
                        f"{i()} Using bulk_insert_mappings with {conflict_resolution} conflict resolution."
                    )
                    # Construct the INSERT statement with the appropriate conflict resolution clause
                    insert_stmt = insert(cls).values(records)
                    if conflict_resolution.upper() == "IGNORE":
                        insert_stmt = insert_stmt.on_conflict_do_nothing()
                    elif conflict_resolution.upper() == "REPLACE":
                        insert_stmt = insert_stmt.on_conflict_do_update(
                            constraint=cls.__table__.primary_key,
                            set_={
                                c.key: c
                                for c in insert_stmt.excluded
                                if not c.primary_key
                            },
                        )

                    session.execute(insert_stmt)

                if where:
                    logger.info(f"{i()} Applying additional WHERE conditions: {where}")
                    # TO-DO: Implement logic to apply WHERE conditions for bulk operations
                    # This might involve creating a separate UPDATE statement
                    # Example (pseudo-code):
                    # update_stmt = update(cls).where(and_(*where))
                    # session.execute(update_stmt)

                session.commit()
                logger.info(
                    f"{i()} Successfully bulk cataloged {len(records)} records for {cls.__name__}."
                )

        except SQLAlchemyError as e:
            logger.error(
                f"{i()} SQLAlchemy error during bulk cataloging for {cls.__name__}: {e}"
            )
            logger.error(traceback.format_exc())
            with gs.write() as session:
                session.rollback()
        except ValueError as e:
            logger.error(
                f"{i()} Value error during bulk cataloging for {cls.__name__}: {e}"
            )
            logger.error(traceback.format_exc())
        except Exception as e:
            logger.error(
                f"{i()} Unexpected error during bulk cataloging for {cls.__name__}: {e}"
            )
            logger.error(traceback.format_exc())
            with gs.write() as session:
                session.rollback()
        finally:
            logger.info(
                f"{i()} Bulk cataloging operation completed for {cls.__name__}."
            )

    @classmethod
    def fetch(
        cls,
        columns: List[str] = None,
        limit: int = 1000,
        sort_by: str = None,
        group_by: str = None,
        random_sample: bool = False,
        where: List[Union[str, Any]] = None,
        page: int = -1,
        per_page: int = 20,
    ) -> Union[List[tuple], dict, Optional[Any]]:
        """
        Fetches records with optional sorting, grouping, random sampling, filtering, and pagination.

        This method provides a flexible way to retrieve records from the database table associated with the class.
        It supports various operations such as column selection, sorting, grouping, random sampling, filtering,
        and pagination. The method uses SQLAlchemy's ORM query interface for efficient database interactions.

        Args:
            columns (List[str], optional): The columns to select in the query. If None, all columns are selected.
            limit (int, optional): The maximum number of records to fetch. Defaults to 1000.
            sort_by (str, optional): Column name to sort by. If provided, results are sorted by this column.
            group_by (str, optional): Column name to group by. If provided, results are grouped by this column.
            random_sample (bool, optional): Whether to randomly sample the records. Defaults to False.
            where (List[Union[str, Any]], optional): The conditions for filtering records. Can be a list of SQLAlchemy expressions or raw SQL strings.
            page (int, optional): The page number for pagination. If <= 0, pagination is not applied. Defaults to -1.
            per_page (int, optional): The number of records per page for pagination. Defaults to 20.

        Returns:
            Union[List[tuple], dict, Optional[Any]]:
                - If limit is 1 and page <= 0: Returns a single record or None if not found.
                - If page > 0: Returns a dictionary with paginated results and metadata.
                - Otherwise: Returns a list of tuples containing the fetched records.

        Raises:
            SQLAlchemyError: If there's an error executing the database query.
            Exception: For any other unexpected errors during the fetch operation.

        Note:
            - This method uses the global read session (gs.read) for database operations.
            - All exceptions are caught, logged, and gracefully handled to prevent crashes.
            - The method uses the global indentation function `i()` for consistent log formatting.
            - Supports complex querying with sorting, grouping, and filtering capabilities.
            - Implements efficient pagination for large datasets.
            - Can return results in various formats based on the query parameters.
        """
        logger.info(f"{i()} Fetching records from {cls.__name__}.")
        try:
            if gs.read is None:
                raise Exception("Read session is not initialized.")

            with gs.read() as readsession:
                # Determine which columns to fetch
                if columns is None:
                    logger.debug(f"{i()} Fetching all columns for {cls.__name__}.")
                    columns = [col.name for col in cls.__table__.columns]

                # Construct the base query
                query = readsession.query(*[getattr(cls, col) for col in columns])

                # Apply filtering conditions if provided
                if where:
                    conditions = build_conditions(where)
                    query = query.filter(*conditions)
                    logger.debug(
                        f"{i()} Applied conditions: {[str(c) for c in conditions]}"
                    )

                # Apply grouping if specified
                if group_by:
                    logger.debug(f"{i()} Grouping by: {group_by}")
                    query = query.group_by(getattr(cls, group_by))

                # Apply sorting if specified
                if sort_by:
                    logger.debug(f"{i()} Sorting by: {sort_by}")
                    query = query.order_by(getattr(cls, sort_by))

                # Handle single record fetch
                if limit == 1 and page <= 0:
                    logger.debug(f"{i()} Fetching a single record.")
                    record = query.first()
                    return record

                # Count total records for pagination or limit
                total_records = query.count()

                # Apply random sampling if requested
                if random_sample:
                    logger.debug(f"{i()} Randomly sampling {limit} records.")
                    query = query.order_by(func.random()).limit(
                        min(limit, total_records)
                    )
                else:
                    # Apply pagination if requested
                    if page > 0:
                        logger.debug(
                            f"{i()} Paginating with page {page} and per_page {per_page}."
                        )
                        offset = (page - 1) * per_page
                        query = query.offset(offset).limit(per_page)
                        total_pages = (total_records + per_page - 1) // per_page
                    else:
                        # Apply limit if no pagination
                        logger.debug(f"{i()} Limiting to {limit} records.")
                        query = query.limit(limit)

                # Execute the query and fetch results
                records = query.all()

                # Format and return the results
                if page > 0:
                    logger.debug(f"{i()} Returning paginated records.")
                    return {
                        "records": [
                            tuple(getattr(record, col) for col in columns)
                            for record in records
                        ],
                        "total_records": total_records,
                        "page": page,
                        "per_page": per_page,
                        "total_pages": total_pages,
                    }

                logger.debug(f"{i()} Returning records.")
                return [
                    tuple(getattr(record, col) for col in columns) for record in records
                ]

        except SQLAlchemyError as e:
            logger.error(
                f"{i()} SQLAlchemyError while retrieving records from {cls.__name__}: {e}"
            )
            logger.error(traceback.format_exc())
            return None if limit == 1 else []
        except Exception as e:
            logger.error(
                f"{i()} Unexpected error retrieving records from {cls.__name__}: {e}"
            )
            logger.error(traceback.format_exc())
            return None if limit == 1 else []

    @classmethod
    def exists(cls, where: List[Union[str, Any]]) -> bool:
        """
        Check if a record exists in the table based on the given conditions.

        This method uses the `fetch` method to query the database and check for the existence
        of a record matching the specified conditions. It's designed to be efficient by limiting
        the query to a single record.

        Args:
            where (List[Union[str, Any]]): A list of conditions to check for the existence of a record.
                                           These conditions are passed directly to the `fetch` method.

        Returns:
            bool: True if a record matching the conditions exists, False otherwise.

        Raises:
            SQLAlchemyError: If there's an error executing the database query.

        Example:
            >>> Company.exists([Company.company_number == "12345678"])
            True

        Note:
            This method catches and logs any exceptions that occur during the database query,
            returning False in case of an error to ensure graceful handling in the calling code.
        """
        try:
            logger.info(
                f"{i()} Checking existence in {cls.__name__} with conditions: {where}"
            )
            record = cls.fetch(where=where, limit=1)
            exists = record is not None
            logger.debug(f"{i()} Existence check result for {cls.__name__}: {exists}")
            return exists
        except SQLAlchemyError as e:
            logger.error(
                f"{i()} SQLAlchemyError checking existence in {cls.__name__}: {e}"
            )
            logger.error(traceback.format_exc())
            return False
        except Exception as e:
            logger.error(
                f"{i()} Unexpected error checking existence in {cls.__name__}: {e}"
            )
            logger.error(traceback.format_exc())
            return False

    @classmethod
    def primary_key(cls) -> Optional[str]:
        """
        Returns the name of the primary key column for the class.

        This method uses SQLAlchemy's inspect function to examine the class's
        mapper and retrieve information about its primary key. It provides a way
        to dynamically determine the primary key of a model, which can be useful
        in generic database operations.

        Returns:
            Optional[str]: The name of the primary key column if one exists,
                           or None if the class has no primary key defined.

        Raises:
            SQLAlchemyError: If there's an error inspecting the class mapper.

        Example:
            >>> class MyModel(Base, CatalogMixin):
            ...     __tablename__ = 'my_table'
            ...     id = Column(Integer, primary_key=True)
            ...
            >>> MyModel.primary_key()
            'id'

        Note:
            - This method is particularly useful for generic operations that need to know
              the primary key without hard-coding it.
            - It handles potential errors during the inspection process and logs them for debugging.
        """
        try:
            mapper = inspect(cls)
            return mapper.primary_key[0].name if mapper.primary_key else None
        except SQLAlchemyError as e:
            logger.error(f"{i()} Error inspecting primary key for {cls.__name__}: {e}")
            logger.error(traceback.format_exc())
            return None
