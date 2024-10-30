from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Boolean, Date, Float, PrimaryKeyConstraint, DateTime, CheckConstraint, UniqueConstraint, event#, Enum,#create_engine,
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship#, sessionmaker
from db.mixins import CatalogMixin  # Import the mixin


Base = declarative_base()

class Jurisdiction(Base, CatalogMixin):
    """
    Jurisdiction details, including hierarchical relationships.
    """
    __tablename__ = 'jurisdiction'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the jurisdiction
    code = Column(String, unique=True, nullable=False)  # Unique jurisdiction code ex: us_id , 83501
    name = Column(String, nullable=False)  # Name of the jurisdiction
    country = Column(String, nullable=False)  # Country of the jurisdiction
    full_name = Column(String, nullable=True)  # Full name of the jurisdiction
    state_abv = Column(String, nullable=True)  # State abbreviation (if applicable)
    county = Column(String, nullable=True)  # County (if applicable)
    city = Column(String, nullable=True)  # City (if applicable)
    longitude = Column(Float, nullable=True)  # Longitude coordinate (if applicable)
    latitude = Column(Float, nullable=True)  # Latitude coordinate (if applicable)
    zip_code = Column(String, nullable=True)  # ZIP code (if applicable)
    area_code = Column(String, nullable=True)  # Area code of telephone number in the jurisdiction (if applicable)
    parent_jurisdiction = Column(Integer, ForeignKey('jurisdiction.id', ondelete='SET NULL'), nullable=True)  # Code of the parent jurisdiction

    # Relationships
    companies = relationship('Company', back_populates='jurisdiction')
    parent = relationship('Jurisdiction', remote_side=[id], backref='children')
    related_relationships = relationship('RelatedRelationship', back_populates='jurisdiction')
    subsidiary_relationships = relationship('SubsidiaryRelationship', back_populates='jurisdiction')
    mergers = relationship('Merger', back_populates='jurisdiction')
    lei_data = relationship('LEIData', back_populates='jurisdiction')
    lei_records = relationship('LEIRecord', back_populates='jurisdiction')
    # url_catalog = relationship('URLCatalog', back_populates='jurisdiction')
    control_statements_controlled = relationship('ControlStatement', foreign_keys='ControlStatement.controlled_company_jurisdiction', back_populates='controlled_jurisdiction')
    control_statements_controlling = relationship('ControlStatement', foreign_keys='ControlStatement.controlling_company_jurisdiction', back_populates='controlling_jurisdiction')

class Company(Base, CatalogMixin):
    """
    Company details - the business profiles or personas - a company is something registered
    as a company by a company registry.
    """
    __tablename__ = 'companies'
    company_number = Column(String, primary_key=True, unique=True)  # Unique identifier for a company
    company_name = Column(String, nullable=False)  # Name of the company
    status = Column(String, nullable=True, default=None)  # Current status of the company
    incorporation_date = Column(Date, default=None, nullable=True)  # Date of incorporation
    company_type = Column(String, nullable=True, default=None)  # Type of company
    jurisdiction = Column(String, nullable=True, default=None)
    jurisdiction_id = Column(Integer, ForeignKey('jurisdiction.id', ondelete='SET NULL'), nullable=True)  # Identifier for the jurisdiction
    registered_address = Column(String, nullable=True, default=None)  # Registered address of the company
    agent_name = Column(String, nullable=True, default=None)  # Name of the registered agent
    agent_address = Column(String, nullable=True, default=None)  # Address of the registered agent
    parent_company_name = Column(String, nullable=True, default=None)  # Name of the parent company
    parent_company_url = Column(String, nullable=True, default=None)  # URL of the parent company

    # Add constraints
    __table_args__ = (
        CheckConstraint("incorporation_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR incorporation_date IS NULL", name='incorporation_date_format'),
    )

    # Relationships
    jurisdiction = relationship('Jurisdiction', back_populates='companies', cascade='none', passive_deletes=True)
    officers = relationship('Officer', back_populates='company', foreign_keys='Officer.company_number', cascade='none', passive_deletes=True)
    events = relationship('Event', back_populates='company', foreign_keys='Event.company_number', cascade='all, delete-orphan', passive_deletes=True)
    share_parcels = relationship('ShareParcel', back_populates='owning_company', foreign_keys='ShareParcel.company_number', cascade='none', passive_deletes=True)
    share_owners = relationship('ShareParcel', back_populates='company_shareholder', foreign_keys='ShareParcel.shareholder_id_company', cascade='none', passive_deletes=True)
    related_relationships = relationship('RelatedRelationship', foreign_keys='RelatedRelationship.company_number', back_populates='company', cascade='none', passive_deletes=True)
    subsidiaries = relationship('SubsidiaryRelationship', back_populates='company', foreign_keys='SubsidiaryRelationship.company_number', cascade='none', passive_deletes=True)
    addresses = relationship('CompanyAddress', back_populates='company', foreign_keys='CompanyAddress.company_number', cascade='none', passive_deletes=True)
    people = relationship('CompanyPerson', back_populates='company', foreign_keys='CompanyPerson.company_number', cascade='none', passive_deletes=True)
    officers_assoc = relationship('CompanyOfficer', back_populates='company', foreign_keys='CompanyOfficer.company_number', cascade='none', passive_deletes=True)
    url_catalog = relationship('URLCatalog', back_populates='company', foreign_keys='URLCatalog.company_number', cascade='none', passive_deletes=True)
    control_statements = relationship('ControlStatement', back_populates='company', foreign_keys='ControlStatement.company_number', cascade='all, delete-orphan', passive_deletes=True)
    mergers = relationship('Merger', back_populates='company', foreign_keys='Merger.company_number', cascade='none', passive_deletes=True)
    mergers_as_merged = relationship('Merger', foreign_keys='Merger.merged_company_id', back_populates='merged_company', cascade='none', passive_deletes=True)
    mergers_as_surviving = relationship('Merger', foreign_keys='Merger.surviving_company_id', back_populates='surviving_company', cascade='none', passive_deletes=True)
    gazette_notices = relationship('GazetteNotice', back_populates='company', foreign_keys='GazetteNotice.company_number', cascade='all, delete-orphan', passive_deletes=True)
    total_shares = relationship('TotalShare', back_populates='company', foreign_keys='TotalShare.company_number', cascade='all, delete-orphan', passive_deletes=True)
    publications = relationship('Publication', back_populates='company', foreign_keys='Publication.company_number', cascade='none', passive_deletes=True)
    identifier_delegate = relationship('IdentifierDelegate', back_populates='company', foreign_keys='IdentifierDelegate.company_number', cascade='none', passive_deletes=True)
    akas = relationship('CompanyAKA', back_populates='company', cascade='all, delete-orphan', passive_deletes=True)

class Address(Base, CatalogMixin):
    """
    Address details - purported addresses of people or businesses.
    """
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the address
    normalized_address = Column(String, unique=True, nullable=False)  # Normalized address
    street = Column(String, nullable=False)  # Street address
    street_2 = Column(String, default=None, nullable=True)  # Second line of the street address
    city = Column(String, nullable=False)  # City
    state = Column(String, nullable=False)  # State or region
    postal_code = Column(String, nullable=False)  # Postal code
    country = Column(String, nullable=False)  # Country
    raw_data = Column(Text, nullable=True)  # Raw address data

    officer_addresses = relationship('OfficerAddress', foreign_keys='OfficerAddress.address_id', back_populates='address', cascade='all, delete-orphan')
    company_addresses = relationship('CompanyAddress', foreign_keys='CompanyAddress.address_id', back_populates='address', cascade='all, delete-orphan')
    people_addresses = relationship('PeopleAddress', foreign_keys='PeopleAddress.address_id', back_populates='address', cascade='all, delete-orphan')

class Officer(Base, CatalogMixin):
    """
    Officer details - An officer is a person that has official standing within a company,
    inclusive of registered agents but excluding shareholders. In the United Kingdom, this would
    include roles such as "Secretary" and "Director". A company may also be an officer.
    An officer may be an agent/officer of multiple companies.
    """
    __tablename__ = 'officers'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the officer
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=False)  # Unique identifier for the company
    occurrence_number = Column(String)  # Occurrence number of the officer
    name = Column(String)  # Name of the officer
    status = Column(String)  # Current status of the officer
    link = Column(String)  # Link to more information about the officer
    address = Column(String)  # Address of the officer
    start_date = Column(Date, default=None, nullable=True)
    end_date = Column(Date, default=None, nullable=True)

    # Add constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),
    )

    # Relationship with Company
    company = relationship('Company', back_populates='officers')
    addresses = relationship('OfficerAddress', back_populates='officer', cascade='all, delete-orphan')
    person_officers = relationship('PersonOfficer', back_populates='officer', cascade='all, delete-orphan')
    company_officers = relationship('CompanyOfficer', back_populates='officer', cascade='all, delete-orphan')

class Person(Base, CatalogMixin):
    """
    Person details - Information about individuals.
    """
    __tablename__ = 'people'
    id = Column(Integer, primary_key=True, autoincrement=True)
    full_name = Column(String, nullable=False)
    raw_data = Column(Text, nullable=False)
    PrefixMarital = Column(String, nullable=True, default=None)
    PrefixOther = Column(String, nullable=True, default=None)
    GivenName = Column(String, nullable=True, default=None)
    FirstInitial = Column(String, nullable=True, default=None)
    MiddleName = Column(String, nullable=True, default=None)
    MiddleInitial = Column(String, nullable=True, default=None)
    Surname = Column(String, nullable=True, default=None)
    LastInitial = Column(String, nullable=True, default=None)
    SuffixGenerational = Column(String, nullable=True, default=None)
    SuffixOther = Column(String, nullable=True, default=None)
    Nickname = Column(String, nullable=True, default=None)

    # Relationships
    share_parcels = relationship('ShareParcel', back_populates='person', cascade='all, delete-orphan')
    addresses = relationship('PeopleAddress', back_populates='person', cascade='all, delete-orphan')
    officers = relationship('PersonOfficer', back_populates='person', cascade='all, delete-orphan')
    akas = relationship('PersonAKA', back_populates='person', cascade='all, delete-orphan')  # Added relationship
    company_people = relationship('CompanyPerson', back_populates='person', cascade='all, delete-orphan')

class PersonAKA(Base, CatalogMixin):
    """
    Alternate names (AKAs) for people.
    """
    __tablename__ = 'person_akas'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the alternate name record
    person_id = Column(Integer, ForeignKey('people.id'), nullable=False)  # Identifier for the person
    aka = Column(String, nullable=False)  # Alternate name (Also Known As)
    start_date = Column(Date, default=None, nullable=True)  # Start date of the alternative name
    end_date = Column(Date, default=None, nullable=True)  # End date of the alternative name
    type = Column(String(12), nullable=True)  # Type of the alternative name
    language = Column(String(2), default='en', nullable=True)  # Language code, 2 characters long

    # Add constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),
        CheckConstraint("type IN ('trading', 'abbreviation', 'legal', 'published', 'dba', 'aka', 'alias') OR type IS NULL", name='person_aka_type')
    )

    # Relationships
    person = relationship('Person', back_populates='akas')

class CompanyAKA(Base, CatalogMixin):
    """
    Alternative names for companies.
    """
    __tablename__ = 'company_akas'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the AKA
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=False)  # Unique identifier for the company
    aka = Column(String, nullable=False)  # Alternative name of the company
    start_date = Column(Date, default=None, nullable=True)  # Start date of the alternative name
    end_date = Column(Date, default=None, nullable=True)  # End date of the alternative name
    type = Column(String(12), nullable=True)  # Type of the alternative name
    language = Column(String(2), default='en', nullable=True)  # Language code, 2 characters long

    # Add constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),
        CheckConstraint("type IN ('trading', 'abbreviation', 'legal', 'published', 'dba', 'aka', 'alias') OR type IS NULL", name='company_aka_type')
    )

    # Relationships
    company = relationship('Company', back_populates='akas')  # Assuming there's a back_populates in Company

class Attribute(Base, CatalogMixin):
    """
    Company attributes, stored as key-value pairs. The key is the attribute name, `name`,
    and the value is `value`.
    """
    __tablename__ = 'attributes'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the attribute
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=False)  # Unique identifier for the company
    name = Column(String, nullable=False)  # Name of the attribute
    value = Column(String, nullable=False)  # Value of the attribute

    # Add unique constraint
    __table_args__ = (
        UniqueConstraint('company_number', 'name', 'value', name='uix_company_name_value'),
    )

class Event(Base, CatalogMixin):
    """
    Company events.
    """
    __tablename__ = 'events'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the event
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=False)  # Unique identifier for the company
    start_date = Column(Date, default=None, nullable=True)  # Start date of the event
    end_date = Column(Date, default=None, nullable=True)  # End date of the event
    description = Column(String, nullable=True)  # Description of the event
    link = Column(String, nullable=True)  # Link to more information about the event

    # Add constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),
    )

    # Relationship with Company
    company = relationship('Company', back_populates='events')

class IdentifierDelegate(Base, CatalogMixin):
    """
    Identifier delegates for companies.
    """
    __tablename__ = 'identifier_delegate'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the identifier delegate
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=False)  # Unique identifier for the company
    identifier_system = Column(String, default=None, nullable=True)  # System of the identifier
    identifier = Column(String, default=None, nullable=True)  # Identifier value
    categories = Column(String, default=None, nullable=True)  # Categories of the identifier

    # Relationships
    company = relationship('Company', back_populates='identifier_delegate')

class Assertion(Base, CatalogMixin):
    """
    Assertions for companies.
    """
    __tablename__ = 'assertions'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the assertion
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=False)  # Unique identifier for the company
    title = Column(String, nullable=False)  # Title of the assertion
    description = Column(String, nullable=False)  # Description of the assertion
    link = Column(String, nullable=True)  # Link to more information about the assertion

    # Add unique constraint
    __table_args__ = (
        UniqueConstraint('company_number', 'title', 'description', name='uix_assertions_company_title_description'),
    )

    # Relationship with Company
    company = relationship('Company', back_populates='assertions')

class Filing(Base, CatalogMixin):
    """
    Company filings.
    """
    __tablename__ = 'filings'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the filing
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=False)  # Unique identifier for the company
    date = Column(String)  # Date of the filing
    description = Column(String)  # Description of the filing
    link = Column(String)  # Link to more information about the filing

class Link(Base, CatalogMixin):
    """
    Links for companies.
    """
    __tablename__ = 'links'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the link
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=False)  # Unique identifier for the company
    link = Column(String, nullable=False)  # Link URL

    # Add unique constraint
    __table_args__ = (
        UniqueConstraint('company_number', 'link', name='uix_company_link'),
    )

    # Relationship with Company
    company = relationship('Company', back_populates='links')

class TrademarkRegistration(Base, CatalogMixin):
    """
    Trademark registrations.
    """
    __tablename__ = 'trademark_registrations'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the trademark registration
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=False)  # Unique identifier for the company
    trademark = Column(String)  # Trademark
    registration_date = Column(String)  # Registration date of the trademark
    status = Column(String)  # Status of the trademark

class IndustryCode(Base, CatalogMixin):
    """
    Industry codes.
    """
    __tablename__ = 'industry_codes'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the industry code
    code = Column(String, unique=True)  # Industry code
    description = Column(String)  # Description of the industry code
    code_scheme = Column(String)  # Scheme of the industry code

class CompanyIndustryCode(Base, CatalogMixin):
    """
    Company industry codes.
    """
    __tablename__ = 'company_industry_codes'

    company_number = Column(String, ForeignKey('companies.company_number', ondelete="CASCADE", onupdate="NO ACTION"), nullable=False)
    industry_code_id = Column(Integer, ForeignKey('industry_codes.id', ondelete="CASCADE", onupdate="NO ACTION"), nullable=False)  # Unique identifier for the industry code
    statement_link = Column(String, nullable=True)  # Link to the statement

    __table_args__ = (
        PrimaryKeyConstraint('company_number', 'industry_code_id'),
    )

    # Relationships
    company = relationship('Company', back_populates='industry_codes')
    industry_code = relationship('IndustryCode', back_populates='companies')

class Classification(Base, CatalogMixin):
    """
    Classifications.
    """
    __tablename__ = 'classifications'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique primarykey identifier for the classification
    classification = Column(String, unique=True)  # Classification

    # Relationships
    gazette_notices = relationship('GazetteNotice', back_populates='classification')

class Publication(Base, CatalogMixin):
    """
    Publications.
    """
    __tablename__ = 'publications'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the publication
    name = Column(String, unique=True)  # Name of the publication
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=False)  # Company number of the publication

    # Relationships
    company = relationship('Company', back_populates='publications')
    gazette_notices = relationship('GazetteNotice', back_populates='publication', cascade='all, delete-orphan')

class GazetteNotice(Base, CatalogMixin):
    """
    Gazette notices.
    """
    __tablename__ = 'gazette_notices'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the gazette notice
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=False)  # Unique identifier for the company
    date = Column(String)  # Date of the notice
    link = Column(String)  # Link to the notice
    publication_id = Column(Integer, ForeignKey('publications.id'))  # Unique identifier for the publication
    notice = Column(Text)  # Notice text
    classification_id = Column(Integer, ForeignKey('classifications.id'))  # Unique identifier for the classification

    # Relationships
    company = relationship('Company', back_populates='gazette_notices')
    publication = relationship('Publication', back_populates='gazette_notices')
    classification = relationship('Classification', back_populates='gazette_notices')

class TotalShare(Base, CatalogMixin):
    """
    Total shares.
    """
    __tablename__ = 'total_shares'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the total shares
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=False)  # Unique identifier for the company
    number = Column(Integer)  # Number of shares
    share_class = Column(String)  # Class of the shares

    # Relationships
    company = relationship('Company', back_populates='total_shares')

class RelatedRelationship(Base, CatalogMixin):
    """
    Company relationships.
    """
    __tablename__ = 'related_relationships'
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_number = Column(String, ForeignKey('companies.company_number', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=False)  # Associated company number
    related_company = Column(String, nullable=True)  # Name of the related company
    related_company_id = Column(String, ForeignKey('companies.company_number', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=True)  # Related company ID
    jurisdiction_code = Column(String, ForeignKey('jurisdiction.code', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=True)  # Jurisdiction code
    status = Column(String, nullable=True)  # Status of the relationship
    type = Column(String, nullable=True)  # Type of relationship
    link = Column(String, nullable=True)  # Link related to the relationship
    start_date = Column(String, default=None, nullable=True)  # Start date of the relationship
    end_date = Column(String, default=None, nullable=True)  # End date of the relationship
    statement_link = Column(String, nullable=True)  # Statement link

    # Add constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),
    )

    # Relationships
    company = relationship('Company', foreign_keys=[company_number], back_populates='related_relationships')
    related_company_obj = relationship('Company', foreign_keys=[related_company_id])
    jurisdiction = relationship('Jurisdiction', back_populates='related_relationships')

class ShareParcel(Base, CatalogMixin):
    """
    Share parcels. Share Parcels show the company shareholders and corresponding shareholding in the company.
    """
    __tablename__ = 'share_parcel'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the share parcel
    company_number = Column(String, ForeignKey('companies.company_number', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=False)  # Unique identifier for the company
    shareholder_id_person = Column(Integer, ForeignKey('people.id', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=True)  # Unique identifier for the shareholder (person)
    shareholder_id_company = Column(String, ForeignKey('companies.company_number', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=True)  # Unique identifier for the shareholder (company)
    shareholder = Column(String, nullable=True)  # Name of the shareholder
    number_of_shares = Column(String, nullable=True)  # Number of shares
    voting_percentage = Column(String, nullable=True)  # Voting percentage of the shares

    # Relationships
    person = relationship('Person', back_populates='share_parcels', foreign_keys=[shareholder_id_person])  # Relationship to Person
    company_shareholder = relationship('Company', back_populates='share_owners', foreign_keys=[shareholder_id_company])  # Relationship to Company as Shareholder
    owning_company = relationship('Company', back_populates='share_parcels', foreign_keys=[company_number])  # Relationship to Owning Company

class SubsidiaryRelationship(Base, CatalogMixin):
    """
    Subsidiary relationships.
    """
    __tablename__ = 'subsidiary_relationships'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the subsidiary relationship
    company_number = Column(String, ForeignKey('companies.company_number', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=False)  # Unique identifier for the company
    subsidiary_company = Column(String, nullable=True)  # Name of the subsidiary company
    subsidiary_company_id = Column(String, ForeignKey('companies.company_number', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=True)  # Unique identifier for the subsidiary company
    jurisdiction_code = Column(String, ForeignKey('jurisdiction.code', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=True)  # Jurisdiction code for the subsidiary company
    status = Column(String, nullable=True)  # Status of the subsidiary company
    type = Column(String, nullable=True)  # Type of the subsidiary company
    link = Column(String, nullable=True)  # Link to more information about the subsidiary company
    start_date = Column(String, default=None, nullable=True)  # Start date of the subsidiary relationship
    end_date = Column(String, default=None, nullable=True)  # End date of the subsidiary relationship
    statement_link = Column(String, nullable=True)  # Statement link

    # Constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),  # Format constraint for start date
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),  # Format constraint for end date
    )

    # Relationships
    company = relationship('Company', foreign_keys=[company_number], back_populates='subsidiaries')  # Relationship to Owning Company
    subsidiary_company_obj = relationship('Company', foreign_keys=[subsidiary_company_id])  # Relationship to Subsidiary Company
    jurisdiction = relationship('Jurisdiction', back_populates='subsidiary_relationships')  # Relationship to Jurisdiction

class Merger(Base, CatalogMixin):
    """
    Mergers, including details about the merged and surviving companies.
    """
    __tablename__ = 'mergers'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the merger
    company_number = Column(String, ForeignKey('companies.company_number', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=False)  # Unique identifier for the company
    merged_company_name = Column(String, nullable=True)  # Name of the merged company
    merged_company_id = Column(String, ForeignKey('companies.company_number', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=True)  # Unique identifier for the merged company
    surviving_company_name = Column(String, nullable=True)  # Name of the surviving company
    surviving_company_id = Column(String, ForeignKey('companies.company_number', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=True)  # Unique identifier for the surviving company
    jurisdiction_id = Column(Integer, ForeignKey('jurisdiction.id', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=True)  # Jurisdiction of the merger
    statement_link = Column(String, nullable=True)  # Link to the statement
    start_date = Column(String, default=None, nullable=True)  # Start date of the merger
    end_date = Column(String, default=None, nullable=True)  # End date of the merger
    raw_data = Column(Text, nullable=True)  # Raw data about the merger

    # Constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),  # Format constraint for start date
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),  # Format constraint for end date
    )

    # Relationships
    company = relationship('Company', foreign_keys=[company_number], back_populates='mergers')  # Relationship to Owning Company
    merged_company = relationship('Company', foreign_keys=[merged_company_id], back_populates='mergers_as_merged')  # Relationship to Merged Company
    surviving_company = relationship('Company', foreign_keys=[surviving_company_id], back_populates='mergers_as_surviving')  # Relationship to Surviving Company
    jurisdiction = relationship('Jurisdiction', foreign_keys=[jurisdiction_id], back_populates='mergers')  # Relationship to Jurisdiction

class ControlStatement(Base, CatalogMixin):
    """
    Control statements between companies.
    """
    __tablename__ = 'control_statements'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the control statement
    company_number = Column(String, ForeignKey('companies.company_number', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=False)  # Unique identifier for the company
    controlled_company_name = Column(String, nullable=True)  # Name of the controlled company
    controlled_company_number = Column(String, ForeignKey('companies.company_number', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=False)  # Unique identifier for the controlled company
    controlled_company_jurisdiction = Column(String, ForeignKey('jurisdiction.code', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=True)  # Jurisdiction code for the controlled company
    controlling_company_name = Column(String, nullable=True)  # Name of the controlling company
    controlling_company_number = Column(String, ForeignKey('companies.company_number', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=False)  # Unique identifier for the controlling company
    controlling_company_jurisdiction = Column(String, ForeignKey('jurisdiction.code', ondelete='NO ACTION', onupdate='NO ACTION'), nullable=True)  # Jurisdiction code for the controlling company
    start_date = Column(String, default=None, nullable=True)  # Start date of the control statement
    end_date = Column(String, default=None, nullable=True)  # End date of the control statement
    mechanisms = Column(Text, nullable=True)  # Control mechanisms used
    statement_link = Column(String, nullable=True)  # Link to the control statement document
    raw_data = Column(Text, nullable=True)  # Raw data related to the control statement

    # Constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),  # Format constraint for start date
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),  # Format constraint for end date
    )

    # Relationships
    company = relationship('Company', foreign_keys=[company_number], back_populates='control_statements')  # Relationship to Owning Company
    controlled_company = relationship('Company', foreign_keys=[controlled_company_number])  # Relationship to Controlled Company
    controlling_company = relationship('Company', foreign_keys=[controlling_company_number])  # Relationship to Controlling Company
    controlled_jurisdiction = relationship('Jurisdiction', foreign_keys=[controlled_company_jurisdiction], back_populates='control_statements_controlled')  # Relationship to Controlled Jurisdiction
    controlling_jurisdiction = relationship('Jurisdiction', foreign_keys=[controlling_company_jurisdiction], back_populates='control_statements_controlling')  # Relationship to Controlling Jurisdiction

class ControlMechanism(Base, CatalogMixin):
    """
    Control mechanisms. Control mechanisms define the methods of control or influence one entity has over another.
    """
    __tablename__ = 'control_mechanisms'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the control mechanism
    mechanism = Column(Text)  # Description of the control mechanism

class ControlStatementMechanism(Base, CatalogMixin):
    """
    Table to map control statements to their mechanisms.
    """
    __tablename__ = 'control_statement_mechanisms'
    control_statement_id = Column(Integer, ForeignKey('control_statements.id'))  # Identifier for the control statement
    mechanism_id = Column(Integer, ForeignKey('control_mechanisms.id'))  # Identifier for the control mechanism

    # Add primarykey constraint
    __table_args__ = (
        PrimaryKeyConstraint('control_statement_id', 'mechanism_id'),
    )

class CompanyAddress(Base, CatalogMixin):
    """
    Table to map companies to their addresses.
    """
    __tablename__ = 'company_addresses'
    company_number = Column(String, ForeignKey('companies.company_number', ondelete="CASCADE", onupdate="NO ACTION"), primary_key=True)  # Unique identifier for the company
    address_id = Column(Integer, ForeignKey('addresses.id', ondelete="CASCADE", onupdate="NO ACTION"), primary_key=True)  # Unique identifier for the address
    type = Column(String, ForeignKey('address_types.code', ondelete="SET NULL", onupdate="NO ACTION"), nullable=True)  # Address type code
    start_date = Column(Date, default=None, nullable=True)  # Start date of the address
    end_date = Column(Date, default=None, nullable=True)  # End date of the address

    # Add constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),  # Format constraint for start date
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),  # Format constraint for end date
    )

    # Relationships
    company = relationship('Company', back_populates='addresses')  # Relationship to the company
    address = relationship('Address', back_populates='company_addresses')  # Relationship to the address
    address_type = relationship('AddressType', back_populates='company_addresses')  # Relationship to the address type

class PeopleAddress(Base, CatalogMixin):
    """
    Table to map people to their addresses.
    """
    __tablename__ = 'people_addresses'
    person_id = Column(Integer, ForeignKey('people.id', ondelete="CASCADE"), primary_key=True)  # Identifier for the person
    address_id = Column(Integer, ForeignKey('addresses.id', ondelete="CASCADE"), primary_key=True)  # Identifier for the address
    type = Column(String, ForeignKey('address_types.code', ondelete="SET NULL"), nullable=True)  # Address type code
    start_date = Column(Date, default=None, nullable=True)  # Start date of the address
    end_date = Column(Date, default=None, nullable=True)  # End date of the address

    # Add constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),  # Format constraint for start date
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),  # Format constraint for end date
    )

    # Relationships
    person = relationship('Person', back_populates='addresses')  # Relationship to the person
    address = relationship('Address', back_populates='people_addresses')  # Relationship to the address
    address_type = relationship('AddressType', back_populates='people_addresses')  # Relationship to the address type

class OfficerAddress(Base, CatalogMixin):
    """
    Table to map officers to their addresses.
    """
    __tablename__ = 'officer_addresses'
    officer_id = Column(Integer, ForeignKey('officers.id', ondelete="CASCADE"), primarykey=True)
    address_id = Column(Integer, ForeignKey('addresses.id', ondelete="CASCADE"), primarykey=True)
    type = Column(String, ForeignKey('address_types.code', ondelete="SET NULL"), nullable=True)
    start_date = Column(Date, default=None, nullable=True)
    end_date = Column(Date, default=None, nullable=True)

    # Add constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),
    )

    officer = relationship('Officer', back_populates='addresses')
    address = relationship('Address', back_populates='officer_addresses')
    address_type = relationship('AddressType', back_populates='officer_addresses')

class CompanyPerson(Base, CatalogMixin):
    """
    Table to map companies to their associated people.
    """
    __tablename__ = 'company_people'
    company_number = Column(String, ForeignKey('companies.company_number', ondelete="CASCADE"), primary_key=True)  # Identifier for the company
    person_id = Column(Integer, ForeignKey('people.id', ondelete="CASCADE"), primary_key=True)  # Identifier for the person
    role = Column(String, ForeignKey('role_types.code', ondelete="SET NULL"), nullable=True)  # Role type code
    start_date = Column(Date, default=None, nullable=True)  # Start date of the role
    end_date = Column(Date, default=None, nullable=True)  # End date of the role

    # Add constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),  # Format constraint for start date
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),  # Format constraint for end date
    )

    # Relationships
    company = relationship('Company', back_populates='people')  # Relationship to the company
    person = relationship('Person', back_populates='company_people')  # Relationship to the person
    role_type = relationship('RoleType', back_populates='company_person_roles')  # Relationship to the role type

class PersonOfficer(Base, CatalogMixin):
    """
    Table to map people to their officer roles.
    """
    __tablename__ = 'person_officers'
    person_id = Column(Integer, ForeignKey('people.id', ondelete="CASCADE"), primarykey=True)
    officer_id = Column(Integer, ForeignKey('officers.id', ondelete="CASCADE"), primarykey=True)
    role = Column(String, ForeignKey('role_types.code', ondelete="SET NULL"), nullable=True)
    start_date = Column(Date, default=None, nullable=True)
    end_date = Column(Date, default=None, nullable=True)

    # Add constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),
    )

    person = relationship('Person', back_populates='officers')
    officer = relationship('Officer', back_populates='person_officers')
    role_type = relationship('RoleType', back_populates='person_officer_roles')

class CompanyOfficer(Base, CatalogMixin):
    """
    Table to map companies to their officers.
    """
    __tablename__ = 'company_officers'
    company_number = Column(String, ForeignKey('companies.company_number', ondelete="CASCADE"), primary_key=True)  # Identifier for the company
    officer_id = Column(Integer, ForeignKey('officers.id', ondelete="CASCADE"), primary_key=True)  # Identifier for the officer
    role = Column(String, ForeignKey('role_types.code', ondelete="SET NULL"), nullable=True)  # Role type code
    start_date = Column(Date, default=None, nullable=True)  # Start date of the role
    end_date = Column(Date, default=None, nullable=True)  # End date of the role

    # Add constraints
    __table_args__ = (
        CheckConstraint("start_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR start_date IS NULL", name='start_date_format'),
        CheckConstraint("end_date GLOB '[0-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]' OR end_date IS NULL", name='end_date_format'),
    )

    # Relationships
    company = relationship('Company', back_populates='officers_assoc')
    officer = relationship('Officer', back_populates='company_officers')
    role_type = relationship('RoleType', back_populates='company_officer_roles')

class RoleType(Base, CatalogMixin):
    """
    Types of roles for officers.
    """
    __tablename__ = 'role_types'
    code = Column(String, nullable=False, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Backpopulates relationships
    company_person_roles = relationship('CompanyPerson', back_populates='role_type', cascade='all, delete-orphan')
    person_officer_roles = relationship('PersonOfficer', back_populates='role_type', cascade='all, delete-orphan')
    company_officer_roles = relationship('CompanyOfficer', back_populates='role_type', cascade='all, delete-orphan')

class AddressType(Base, CatalogMixin):
    """
    Types of addresses.
    """
    __tablename__ = 'address_types'
    code = Column(String, nullable=False, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Backpopulates relationships
    company_addresses = relationship('CompanyAddress', back_populates='address_type', cascade='all, delete-orphan')
    people_addresses = relationship('PeopleAddress', back_populates='address_type', cascade='all, delete-orphan')
    officer_addresses = relationship('OfficerAddress', back_populates='address_type', cascade='all, delete-orphan')

class LEIRecord(Base, CatalogMixin):
    """
    LEI records.
    """
    __tablename__ = 'lei_records'
    lei = Column(String, primary_key=True)  # Legal Entity Identifier (LEI)
    entity_legal_name = Column(String)  # Legal name of the entity
    registration_status = Column(String)  # Status of the LEI registration
    entity_status = Column(String)  # Status of the entity
    jurisdiction_id = Column(Integer, ForeignKey('jurisdiction.id'))  # Identifier for the jurisdiction
    registered_address = Column(String)  # Registered address of the entity
    headquarters_address = Column(String)  # Headquarters address of the entity
    registration_date = Column(String)  # Date of registration
    next_renewal_date = Column(String)  # Next renewal date for the LEI
    managing_lou = Column(String)  # Managing Local Operating Unit (LOU)
    validated_at = Column(String)  # Date of validation

    # Relationships
    jurisdiction = relationship('Jurisdiction', back_populates='lei_records')
    lei_entities = relationship('LEIEntity', back_populates='lei_record')

class LEIEntity(Base, CatalogMixin):
    """
    LEI entities.
    """
    __tablename__ = 'lei_entities'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the LEI entity
    lei = Column(String, ForeignKey('lei_records.lei'))  # Legal Entity Identifier (LEI)
    entity_name = Column(String)  # Name of the entity
    country = Column(String)  # Country of the entity
    entity_type = Column(String)  # Type of the entity

    # Relationships
    lei_record = relationship('LEIRecord', back_populates='lei_entities')

class LEIData(Base, CatalogMixin):
    """
    LEI data.
    """
    __tablename__ = 'lei_data'
    id = Column(String, primary_key=True)  # Unique identifier for the LEI data
    lei = Column(String, unique=True)  # Legal Entity Identifier (LEI) code
    status = Column(String)  # Status of the LEI
    creation_date = Column(String)  # Creation date of the LEI
    registered_as = Column(String)  # Registered name of the entity
    jurisdiction_id = Column(Integer, ForeignKey('jurisdiction.id'))  # Identifier for the jurisdiction
    category = Column(String)  # Category of the LEI
    legal_form_id = Column(String)  # Identifier for the legal form
    legal_form_other = Column(String)  # Other legal form details
    associated_lei = Column(String)  # Associated LEI code
    associated_name = Column(String)  # Associated name
    expiration_date = Column(String)  # Expiration date of the LEI
    expiration_reason = Column(String)  # Reason for expiration
    successor_lei = Column(String)  # Successor LEI code
    successor_name = Column(String)  # Successor name
    sub_category = Column(String)  # Sub-category of the LEI

    # Relationships
    jurisdiction = relationship('Jurisdiction', back_populates='lei_data')
    lei_entity_details = relationship('LEIEntityDetail', back_populates='lei_data')
    lei_addresses = relationship('LEIAddress', back_populates='lei_data')
    lei_registrations = relationship('LEIRegistration', back_populates='lei_data')
    lei_relationships = relationship('LEIRelationship', back_populates='lei_data')
    lei_links = relationship('LEILink', back_populates='lei_data')

class LEIEntityDetail(Base, CatalogMixin):
    """
    LEI entity details.
    """
    __tablename__ = 'lei_entity'
    id = Column(String, primary_key=True)  # Unique identifier for the LEI entity
    lei = Column(String, ForeignKey('lei_data.lei'))  # Legal Entity Identifier (LEI) code
    legal_name = Column(String)  # Legal name of the entity
    language = Column(String)  # Language of the legal name

    # Relationships
    lei_data = relationship('LEIData', back_populates='lei_entity_details')

class LEIAddress(Base, CatalogMixin):
    """
    Addresses associated with LEIs.
    """
    __tablename__ = 'lei_address'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the address
    lei = Column(String, ForeignKey('lei_data.lei'))  # Legal Entity Identifier (LEI) code
    address_type = Column(String)  # Type of the address (e.g., registered, headquarters)
    language = Column(String)  # Language of the address
    address_lines = Column(Text)  # Lines of the address
    city = Column(String)  # City of the address
    region = Column(String)  # Region of the address
    country = Column(String)  # Country of the address
    postal_code = Column(String)  # Postal code of the address

    # Relationships
    lei_data = relationship('LEIData', back_populates='lei_addresses')

class LEIRegistration(Base, CatalogMixin):
    """
    LEI registration details.
    """
    __tablename__ = 'lei_registration'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the registration
    lei = Column(String, ForeignKey('lei_data.lei'))  # Legal Entity Identifier (LEI) code
    initial_registration_date = Column(String)  # Initial registration date of the LEI
    last_update_date = Column(String)  # Last update date of the LEI
    status = Column(String)  # Status of the LEI registration
    next_renewal_date = Column(String)  # Next renewal date of the LEI
    managing_lou = Column(String)  # Managing Local Operating Unit (LOU)
    corroboration_level = Column(String)  # Level of corroboration
    validated_at_id = Column(String)  # Identifier for the validation
    validated_as = Column(String)  # Validated as type

    # Relationships
    lei_data = relationship('LEIData', back_populates='lei_registrations')

class LEIRelationship(Base, CatalogMixin):
    """
    Relationships between LEI entities.
    """
    __tablename__ = 'lei_relationships'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the relationship
    lei = Column(String, ForeignKey('lei_data.lei'))  # Legal Entity Identifier (LEI) code
    relationship_type = Column(String)  # Type of the relationship
    related_link = Column(String)  # Link to the related entity

    # Relationships
    lei_data = relationship('LEIData', back_populates='lei_relationships')

class LEILink(Base, CatalogMixin):
    """
    Various links related to LEI entities.
    """
    __tablename__ = 'lei_links'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the link
    lei = Column(String, ForeignKey('lei_data.lei'))  # Legal Entity Identifier (LEI) code
    self_link = Column(String)  # Self link
    managing_lou_link = Column(String)  # Link to the managing LOU
    lei_issuer_link = Column(String)  # Link to the LEI issuer
    field_modifications_link = Column(String)  # Link to field modifications
    direct_parent_link = Column(String)  # Link to the direct parent
    ultimate_parent_link = Column(String)  # Link to the ultimate parent
    direct_children_link = Column(String)  # Link to direct children
    ultimate_children_link = Column(String)  # Link to ultimate children

    # Relationships
    lei_data = relationship('LEIData', back_populates='lei_links')

class URLCatalog(Base, CatalogMixin):
    """
    Table to catalog URLs and their metadata.
    """
    __tablename__ = 'url_catalog'
    id = Column(Integer, primary_key=True, autoincrement=True)  # Unique identifier for the URL
    url = Column(String, unique=True)  # URL for the resource
    company_number = Column(String, ForeignKey('companies.company_number'), nullable=True)  # Unique identifier for the company
    # jurisdiction_id = Column(Integer, ForeignKey('jurisdiction.id'))  # Identifier for the jurisdiction
    jurisdiction = Column(String)  # Text field for jurisdiction
    completed = Column(Boolean, default=False)  # Flag indicating if the URL has been processed
    html_content = Column(Text)  # HTML content of the page
    parent_id = Column(Integer, ForeignKey('url_catalog.id'), nullable=True)  # Identifier for the parent URL
    cached_on = Column(DateTime, default=None)  # DateTime when the content was cached

    # Relationships
    company = relationship('Company', back_populates='url_catalog')
    # jurisdiction = relationship('Jurisdiction', back_populates='url_catalog')
    parent = relationship('URLCatalog', remote_side=[id], backref='children')

@event.listens_for(URLCatalog.html_content, 'set')
def set_cached_on(
    target,
    value,
    oldvalue,
    initiator
):
    """
    Event listener for the 'html_content' attribute of the URLCatalog model.

    When the 'html_content' attribute is set, this function is called to update the 'cached_on' attribute
    of the URLCatalog model. If the 'html_content' is not None and has changed from the previous value,
    the 'cached_on' attribute is set to the current datetime. Otherwise, the 'cached_on' attribute is set to None.

    Args:
        target (URLCatalog): The URLCatalog instance being modified.
        value (str): The new value of the 'html_content' attribute.
        oldvalue (str): The previous value of the 'html_content' attribute.
        initiator (sa.orm.attributes.Event): The event that triggered the modification.
    """
    if value is not None and value != oldvalue:
        target.cached_on = datetime.now()
    else:
        target.cached_on = None
