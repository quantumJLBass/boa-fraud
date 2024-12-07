import db.dbefclasses
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

Base = declarative_base()

#we have dbenfclasses.py for each model do we not?  if there is reason we need this, maybe as the couplure from the uniformaty of the mvc to all the tables?  not seeing other wise to justify it please