import traceback
import random
from typing import List, Any, Union#, Dict
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect, Date, Column, CheckConstraint, event
from sqlalchemy.sql import text, and_, or_, func
from sqlalchemy.orm import declared_attr
from services.applogging import *
from gs import *

def set_attributes(
    instance: object,
    data: dict
) -> None:
    """
    Set multiple attributes on an instance from a dictionary.

    Args:
        instance: The instance to update.
        data (dict): The dictionary of attribute names and values.
    """
    for key, value in data.items():
        setattr(instance, key, value)

def build_conditions(
    where: Union[str, List[str]]
) -> List[Any]:
    """
    Builds SQLAlchemy conditions from a structured list.

    Args:
        where (list): A list of conditions with strings or lists of conditions.
                    Use '&' or no prefix for 'AND', '|' for 'OR'.

    Returns:
        list: A list of SQLAlchemy conditions.
    """
    if isinstance(where, str):
        where = [where]

    conditions = []
    for condition in where:
        if isinstance(condition, list):
            sub_conditions = [text(c.lstrip('|&')) for c in condition]
            conditions.append(or_(*sub_conditions) if '|' in condition[0] else and_(*sub_conditions))
        else:
            conditions.append(text(condition.lstrip('|&')))
    return conditions

class CatalogMixin:
    """
    Mixin class for cataloging and fetching records from a database table.
    """
    @declared_attr
    def asof(self) -> Column:
        """
        Declares the 'asof' column for the model.

        Returns:
            Column: A DateTime column with a default value of the current timestamp.
        """
        return Column(Date, nullable=False, default=func.now())

    @classmethod
    def __declare_last__(cls):
        """
        Sets up event listeners for the model.
        """
        @event.listens_for(cls, 'before_insert')
        @event.listens_for(cls, 'before_update')
        def set_asof(mapper, connection, target):
            """
            Event listener that sets the 'asof' column to the current timestamp.

            Args:
                mapper: The Mapper object which is the target of this event.
                connection: The Connection being used for the operation.
                target: The mapped instance being persisted.
            """
            target.asof = func.now()

    @declared_attr
    def __table_args__(self) -> tuple:
        """
        Declares table arguments for the model.

        Returns:
            tuple: A tuple containing table constraints.
        """
        return (
            CheckConstraint("asof GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]'", name='asof_date_format'),
        )

    @classmethod
    def catalog_record(
        cls,
        data: dict,
        where: List[str] = None
    ) -> None:
        """
        Catalog a record in the table, either by updating an existing record or creating a new one.

        Args:
            data (dict): A dictionary of column names and values to be cataloged.
            where (list, optional): A list of conditions with strings or lists of conditions.
                                    Use '&' or no prefix for 'AND', '|' for 'OR'.

        Returns:
            None
        """
        try:
            if not data:
                raise ValueError("Data dictionary must be provided.")

            # Get primary key name dynamically
            primary_key_column = inspect(cls).primary_key[0].name

            primary_key_value = data.get(primary_key_column)

            existing_record = None

            # Check if the record exists using the primary key or where conditions
            with gs.read() as readsession:
                if primary_key_value:
                    existing_record = readsession.query(cls).get(primary_key_value)
                elif where:
                    existing_record = readsession.query(cls).filter(*build_conditions(where)).first()

            # Debugging log to check the value of 'write'
            logger.debug(f"Write function: {gs.write}")

            # Write session to update or insert the record
            with gs.write() as sub_session:
                if existing_record:
                    logger.info(f"🔧🗃️ DBRECORDS -- CATALOGING ----- Updating {cls.__name__} record with ID: {primary_key_value}")
                    set_attributes(existing_record, data)
                    sub_session.merge(existing_record)  # Ensure the object is attached to the session
                else:
                    logger.info(f"🔧🗃️ DBRECORDS -- CATALOGING ----- Inserting a new record into {cls.__name__}")
                    new_record = cls(**data)
                    if not isinstance(new_record, cls):
                        raise TypeError(f"Expected instance of {cls}, got {type(new_record)}")
                    sub_session.add(new_record)

                sub_session.commit()  # Commit changes after update or insert
                logger.info(f"🔧🗃️ DBRECORDS -- CATALOGING ----- {'Updated' if existing_record else 'Inserted'} {cls.__name__} record successfully")

        except SQLAlchemyError as e:
            logger.error(f"💥🚩 Error cataloging {cls.__name__} data: {e}")
            logger.error(f"{traceback.format_exc()}")
            with gs.write() as writesession:
                writesession.rollback()
        except Exception as e:
            logger.error(f"💥🚩 Error cataloging {cls.__name__} data: {e}")
            logger.error(f"{traceback.format_exc()}")
            with gs.write() as writesession:
                writesession.rollback()


    @classmethod
    def fetch_records(
        cls,
        columns: List[str] = None,  # Set default to None
        limit: int = 1000,
        sort_by: str = None,
        group_by: str = None,
        random_sample: bool = False,
        where: List[str] = None
    ) -> List[tuple]:
        """
        Fetches records from the table with optional sorting, grouping, random sampling, and filtering.

        Args:
            columns (list, optional): List of columns to select. If None, selects all columns.
            limit (int): The maximum number of records to retrieve. Defaults to 1000.
            sort_by (str, optional): The field by which to sort the results. Defaults to None.
            group_by (str, optional): The field by which to group the results. Defaults to None.
            random_sample (bool, optional): Whether to randomly sample the results. Defaults to False.
            where (list, optional): A list of SQLAlchemy filter conditions or lists of conditions.

        Returns:
            list: A list of tuples containing the requested records.
        """
        logger.info(f"🔍 Starting to fetch records from {cls.__name__}.")
        try:
            if gs.read is None:
                raise Exception("Read session is not initialized.")

            with gs.read() as readsession:
                # If no columns are specified, select all columns
                if columns is None:
                    columns = [col.name for col in cls.__table__.columns]

                query = readsession.query(*[getattr(cls, col) for col in columns])
                if where:
                    conditions = build_conditions(where)
                    query = query.filter(and_(*conditions))
                    logger.debug(f"Applied conditions: {[str(c) for c in conditions]}")
                if group_by:
                    logger.debug(f"Grouping by: {group_by}")
                    query = query.group_by(getattr(cls, group_by))
                if sort_by:
                    logger.debug(f"Sorting by: {sort_by}")
                    query = query.order_by(getattr(cls, sort_by))

                # Log the full SQL query
                logger.debug(f"Executing SQL: {query.statement.compile(compile_kwargs={'literal_binds': True})}")

                records = []
                if random_sample:
                    count_query = readsession.query(func.count(cls.id)).filter(and_(*conditions))
                    count = count_query.scalar()
                    logger.debug(f"Count of records matching conditions: {count}")
                    if count > 0:
                        logger.debug(f"Fetching up to {limit} random records.")
                        for _ in range(min(limit, count)):
                            random_offset = random.randint(0, count - 1)
                            logger.debug(f"Random offset: {random_offset}")
                            record_query = query.offset(random_offset).limit(1)
                            logger.debug(f"Executing query: {record_query}")
                            record = record_query.all()
                            logger.debug(f"Retrieved record: {record}")
                            records.extend(record)
                    else:
                        logger.info("No records match the random sampling criteria.")
                else:
                    records = query.limit(limit).all()
                    logger.debug(f"Retrieved {len(records)} records without random sampling.")
                logger.debug(f"Retrieved {len(records)} records.")
                logger.info(f"🌎📡 Retrieved {len(records)} records from {cls.__name__}.")
                return [tuple(getattr(record, col) for col in columns) for record in records]
        except SQLAlchemyError as e:
            logger.error(f"💥🚩 Error cataloging {cls.__name__} data: {e}")
            logger.error(f"{traceback.format_exc()}")
            return []
        except Exception as e:
            logger.error(f"💥🚩 Error retrieving records from {cls.__name__}: {e}")
            logger.error(f"{traceback.format_exc()}")
            return []

    @classmethod
    def record_exists(
        cls,
        where: list
    ) -> bool:
        """
        Check if a record exists in the table based on the given conditions.

        Args:
            where (list): A list of conditions with strings or lists of conditions.
                        Use '&' or no prefix for 'AND', '|' for 'OR'.

        Returns:
            bool: True if the record exists, False otherwise.
        """
        try:
            with gs.read() as readsession:
                query = readsession.query(cls).filter(*build_conditions(where))
                return readsession.query(query.exists()).scalar()
        except SQLAlchemyError as e:
            logger.error(f"💥🚩 Error checking existence in {cls.__name__}: {e}")
            logger.error(f"{traceback.format_exc()}")
            return False
        except Exception as e:
            logger.error(f"💥🚩 Error retrieving records from {cls.__name__}: {e}")
            logger.error(f"{traceback.format_exc()}")
            return False
