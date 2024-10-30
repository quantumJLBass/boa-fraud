TABLES_ENSURE = [
    ('companies', '''
        company_number TEXT PRIMARY KEY,        -- Unique identifier for a company
        company_name TEXT,                      -- Name of the company
        status TEXT,                            -- Current status of the company
        incorporation_date TEXT,                -- Date of incorporation
        company_type TEXT,                      -- Type of company
        jurisdiction_id INTEGER,                -- Identifier for the jurisdiction
        registered_address TEXT,                -- Registered address of the company
        agent_name TEXT,                        -- Name of the registered agent
        agent_address TEXT,                     -- Address of the registered agent
        parent_company_name TEXT,               -- Name of the parent company
        parent_company_url TEXT,                -- URL of the parent company
        FOREIGN KEY(jurisdiction_id) REFERENCES jurisdiction(id)  -- Foreign key to jurisdiction table
    ''', 'Company details - the business profiles or personas - a company is something registered as a company by a company registry.', {
        'company_number': 'Unique identifier for a company',
        'company_name': 'Name of the company',
        'status': 'Current status of the company',
        'incorporation_date': 'Date of incorporation',
        'company_type': 'Type of company',
        'jurisdiction_id': 'Identifier for the jurisdiction',
        'registered_address': 'Registered address of the company',
        'agent_name': 'Name of the registered agent',
        'agent_address': 'Address of the registered agent',
        'parent_company_name': 'Name of the parent company',
        'parent_company_url': 'URL of the parent company'
    }),
    ('addresses', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the address
        normalized_address TEXT,                -- Normalized address
        street TEXT,                            -- Street address
        street_2 TEXT,                          -- Second line of the street address
        city TEXT,                              -- City
        state TEXT,                             -- State or region
        postal_code TEXT,                       -- Postal code
        country TEXT,                           -- Country
        raw_data TEXT                           -- Raw address data
    ''', 'addresses - purported addresses of people or businesses.', {
        'id': 'Unique identifier for the address',
        'normalized_address': 'Normalized address',
        'street': 'Street address',
        'street_2': 'Second line of the street address',
        'city': 'City',
        'state': 'State or region',
        'postal_code': 'Postal code',
        'country': 'Country',
        'raw_data': 'Raw address data'
    }),
    ('officers', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the officer
        company_number TEXT,                    -- Unique identifier for the company
        occurrence_number TEXT,                 -- Occurrence number of the officer
        name TEXT,                              -- Name of the officer
        role TEXT,                              -- Role of the officer
        status TEXT,                            -- Current status of the officer
        link TEXT,                              -- Link to more information about the officer
        address TEXT,                           -- Address of the officer
        start_date TEXT,                        -- Start date of the officer's role
        end_date TEXT,                          -- End date of the officer's role
        type TEXT,                              -- Type of the officer
        FOREIGN KEY(company_number) REFERENCES companies(company_number)  -- Foreign key to companies table
    ''', 'officer details. An officer is a person that has official standing within a company, inclusive of registered agents but excluding shareholders. In the United Kingdom this would include roles such as "Secretary" and "Director".  A company may also be an officer. An officer may be an agaent/officer of multiple companies.', {
        'id': 'Unique identifier for the officer',
        'company_number': 'Unique identifier for the company',
        'occurrence_number': 'Occurrence number of the officer',
        'name': 'Name of the officer',
        'role': 'Role of the officer',
        'status': 'Current status of the officer',
        'link': 'Link to more information about the officer',
        'address': 'Address of the officer',
        'start_date': 'Start date of the officer\'s role',
        'end_date': 'End date of the officer\'s role',
        'type': 'Type of the officer'
    }),
    ('people', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the person
        name TEXT,                              -- Name of the person
        raw_data TEXT                           -- Raw data about the person
    ''', 'people details', {
        'id': 'Unique identifier for the person',
        'name': 'Name of the person',
        'raw_data': 'Raw data about the person'
    }),
    ('jurisdiction', '''
        code TEXT PRIMARY KEY,                       -- Unique jurisdiction code
        name TEXT,                                   -- Name of the jurisdiction
        country TEXT,                                -- Country of the jurisdiction
        full_name TEXT,                              -- Full name of the jurisdiction
        state_abv TEXT,                              -- State abbreviation (if applicable)
        parent_jurisdiction TEXT,                    -- Code of the parent jurisdiction
        FOREIGN KEY(parent_jurisdiction) REFERENCES jurisdiction(code)  -- Foreign key to self-reference for hierarchy
    ''', 'jurisdiction details, including hierarchical relationships', {
        'code': 'Unique jurisdiction code',
        'name': 'Name of the jurisdiction',
        'country': 'Country of the jurisdiction',
        'full_name': 'Full name of the jurisdiction',
        'state_abv': 'State abbreviation (if applicable)',
        'parent_jurisdiction': 'Code of the parent jurisdiction'
    }),
    ('company_akas', '''
        id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique identifier for the AKA
        company_number TEXT,                    -- Unique identifier for the company
        aka TEXT,                               -- Alternative name of the company
        start_date TEXT,                        -- Start date of the alternative name
        end_date TEXT,                          -- End date of the alternative name
        type TEXT CHECK (type IN ('AKA', 'PKA')),  -- Type of the alternative name
        FOREIGN KEY(company_number) REFERENCES companies(company_number)  -- Foreign key to companies table
    ''', 'alternative names for companies', {
        'id': 'Unique identifier for the AKA',
        'company_number': 'Unique identifier for the company',
        'aka': 'Alternative name of the company',
        'start_date': 'Start date of the alternative name',
        'end_date': 'End date of the alternative name',
        'type': 'Type of the alternative name'
    }),
    ('attributes', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the attribute
        company_number TEXT,                    -- Unique identifier for the company
        name TEXT,                              -- Name of the attribute
        value TEXT,                             -- Value of the attribute
        FOREIGN KEY(company_number) REFERENCES companies(company_number)  -- Foreign key to companies table
    ''', 'company attributes, stored as key-value pairs. The key is the attribute name, `name` and the value is `value`', {
        'id': 'Unique identifier for the attribute',
        'company_number': 'Unique identifier for the company',
        'name': 'Name of the attribute',
        'value': 'Value of the attribute'
    }),
    ('events', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the event
        company_number TEXT,                    -- Unique identifier for the company
        start_date TEXT,                        -- Start date of the event
        end_date TEXT,                          -- End date of the event
        description TEXT,                       -- Description of the event
        link TEXT,                              -- Link to more information about the event
        FOREIGN KEY(company_number) REFERENCES companies(company_number)  -- Foreign key to companies table
    ''', 'company events', {
        'id': 'Unique identifier for the event',
        'company_number': 'Unique identifier for the company',
        'start_date': 'Start date of the event',
        'end_date': 'End date of the event',
        'description': 'Description of the event',
        'link': 'Link to more information about the event'
    }),
    ('identifier_delegate', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the identifier delegate
        company_number TEXT,                    -- Unique identifier for the company
        identifier_system TEXT,                 -- System of the identifier
        identifier TEXT,                        -- Identifier value
        categories TEXT,                        -- Categories of the identifier
        FOREIGN KEY(company_number) REFERENCES companies(company_number)  -- Foreign key to companies table
    ''', 'identifier delegates for companies', {
        'id': 'Unique identifier for the identifier delegate',
        'company_number': 'Unique identifier for the company',
        'identifier_system': 'System of the identifier',
        'identifier': 'Identifier value',
        'categories': 'Categories of the identifier'
    }),
    ('assertions', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the assertion
        company_number TEXT,                    -- Unique identifier for the company
        title TEXT,                             -- Title of the assertion
        description TEXT,                       -- Description of the assertion
        link TEXT,                              -- Link to more information about the assertion
        FOREIGN KEY(company_number) REFERENCES companies(company_number)  -- Foreign key to companies table
    ''', 'assertions for companies', {
        'id': 'Unique identifier for the assertion',
        'company_number': 'Unique identifier for the company',
        'title': 'Title of the assertion',
        'description': 'Description of the assertion',
        'link': 'Link to more information about the assertion'
    }),
    ('filings', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the filing
        company_number TEXT,                    -- Unique identifier for the company
        date TEXT,                              -- Date of the filing
        description TEXT,                       -- Description of the filing
        link TEXT,                              -- Link to more information about the filing
        FOREIGN KEY(company_number) REFERENCES companies(company_number)  -- Foreign key to companies table
    ''', 'company filings', {
        'id': 'Unique identifier for the filing',
        'company_number': 'Unique identifier for the company',
        'date': 'Date of the filing',
        'description': 'Description of the filing',
        'link': 'Link to more information about the filing'
    }),
    ('links', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the link
        company_number TEXT,                    -- Unique identifier for the company
        link TEXT,                              -- Link URL
        FOREIGN KEY(company_number) REFERENCES companies(company_number)  -- Foreign key to companies table
    ''', 'links for companies', {
        'id': 'Unique identifier for the link',
        'company_number': 'Unique identifier for the company',
        'link': 'Link URL'
    }),
    ('trademark_registrations', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the trademark registration
        company_number TEXT,                    -- Unique identifier for the company
        trademark TEXT,                         -- Trademark
        registration_date TEXT,                 -- Registration date of the trademark
        status TEXT,                            -- Status of the trademark
        FOREIGN KEY(company_number) REFERENCES companies(company_number)  -- Foreign key to companies table
    ''', 'trademark registrations', {
        'id': 'Unique identifier for the trademark registration',
        'company_number': 'Unique identifier for the company',
        'trademark': 'Trademark',
        'registration_date': 'Registration date of the trademark',
        'status': 'Status of the trademark'
    }),
    ('industry_codes', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the industry code
        code TEXT UNIQUE,                       -- Industry code
        description TEXT,                       -- Description of the industry code
        code_scheme TEXT                        -- Scheme of the industry code
    ''', 'industry codes', {
        'id': 'Unique identifier for the industry code',
        'code': 'Industry code',
        'description': 'Description of the industry code',
        'code_scheme': 'Scheme of the industry code'
    }),
    ('company_industry_codes', '''
        company_number TEXT,                    -- Unique identifier for the company
        industry_code_id INTEGER,               -- Unique identifier for the industry code
        statement_link TEXT,                    -- Link to the statement
        FOREIGN KEY(company_number) REFERENCES companies(company_number),  -- Foreign key to companies table
        FOREIGN KEY(industry_code_id) REFERENCES industry_codes(id),       -- Foreign key to industry codes table
        PRIMARY KEY (company_number, industry_code_id)                      -- Composite primary key
    ''', 'company industry codes', {
        'company_number': 'Unique identifier for the company',
        'industry_code_id': 'Unique identifier for the industry code',
        'statement_link': 'Link to the statement'
    }),
    ('classifications', '''
        id INTEGER PRIMARY KEY,                 -- Unique primary key identifier for the classification
        classification TEXT UNIQUE              -- Classification
    ''', 'classifications', {
        'id': 'Unique identifier for the classification',
        'classification': 'Classification'
    }),
    ('publications', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the publication
        name TEXT UNIQUE,                       -- Name of the publication
        company_number TEXT,                    -- Company number of the publication
        FOREIGN KEY(company_number) REFERENCES companies(company_number),  -- Foreign key to companies table
    ''', 'publications', {
        'id': 'Unique identifier for the publication',
        'name': 'Name of the publication',
        'company_number': 'Company number of the publication'
    }),
    ('gazette_notices', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the gazette notice
        company_number TEXT,                    -- Unique identifier for the company
        date TEXT,                              -- Date of the notice
        publication_id INTEGER,                 -- Unique identifier for the publication
        notice TEXT,                            -- Notice text
        classification_id INTEGER,              -- Unique identifier for the classification
        FOREIGN KEY(company_number) REFERENCES companies(company_number),  -- Foreign key to companies table
        FOREIGN KEY(publication_id) REFERENCES publications(id),           -- Foreign key to publications table
        FOREIGN KEY(classification_id) REFERENCES classifications(id)      -- Foreign key to classifications table
    ''', 'gazette notices', {
        'id': 'Unique identifier for the gazette notice',
        'company_number': 'Unique identifier for the company',
        'date': 'Date of the notice',
        'publication_id': 'Unique identifier for the publication',
        'notice': 'Notice text',
        'classification_id': 'Unique identifier for the classification'
    }),
    ('total_shares', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the total shares
        company_number TEXT,                    -- Unique identifier for the company
        number INTEGER,                         -- Number of shares
        share_class TEXT,                       -- Class of the shares
        FOREIGN KEY(company_number) REFERENCES companies(company_number)  -- Foreign key to companies table
    ''', 'total shares', {
        'id': 'Unique identifier for the total shares',
        'company_number': 'Unique identifier for the company',
        'number': 'Number of shares',
        'share_class': 'Class of the shares'
    }),
    ('related_relationships', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the relationship
        company_number TEXT,                    -- Unique identifier for the company
        related_company TEXT,                   -- Related company name
        related_company_id TEXT,                -- Unique identifier of the related company
        jurisdiction_code TEXT,                 -- Jurisdiction code of the related company
        status TEXT,                            -- Status of the relationship
        type TEXT,                              -- Type of the relationship (parent, subsidiary, etc.)
        link TEXT,                              -- Link to more information about the company relationship
        start_date TEXT,                        -- Start date of the relationship
        end_date TEXT,                          -- End date of the relationship
        statement_link TEXT,                    -- Link to the statement
        FOREIGN KEY(company_number) REFERENCES companies(company_number),  -- Foreign key to companies table
        FOREIGN KEY(related_company_id) REFERENCES companies(company_number),  -- Foreign key to related company
        FOREIGN KEY(jurisdiction_code) REFERENCES jurisdiction(code)  -- Foreign key to jurisdiction table
    ''', 'company relationships', {
        'id': 'Unique identifier for the relationship',
        'company_number': 'Unique identifier for the company',
        'related_company': 'Related company name',
        'related_company_id': 'Unique identifier of the related company',
        'jurisdiction_code': 'Jurisdiction code of the related company',
        'status': 'Status of the relationship',
        'type': 'Type of the relationship',
        'link': 'Link to more information about the company relationship',
        'start_date': 'Start date of the relationship',
        'end_date': 'End date of the relationship',
        'statement_link': 'Link to the statement'
    }),
    ('share_parcel', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the share parcel
        company_number TEXT,                    -- Unique identifier for the company
        shareholder_id INTEGER,                 -- Unique identifier for the shareholder
        shareholder TEXT,                       -- Name of the shareholder
        number_of_shares TEXT,                  -- Number of shares
        voting_percentage TEXT,                 -- Voting percentage of the shares
        FOREIGN KEY(company_number) REFERENCES companies(company_number),  -- Foreign key to companies table
        FOREIGN KEY(shareholder_id) REFERENCES people(id) ON DELETE SET NULL,  -- Foreign key to people table, can be null
        FOREIGN KEY(shareholder_id) REFERENCES companies(company_number) ON DELETE SET NULL  -- Foreign key to companies table, can be null
    ''', 'share parcels. Share Parcels show the company shareholders and corresponding shareholding in the company', {
        'id': 'Unique identifier for the share parcel',
        'company_number': 'Unique identifier for the company',
        'shareholder_id': 'Unique identifier for the shareholder',
        'shareholder': 'Name of the shareholder',
        'number_of_shares': 'Number of shares',
        'voting_percentage': 'Voting percentage of the shares'
    }),
    ('subsidiary_relationships', '''
        id INTEGER PRIMARY KEY,                 -- Unique identifier for the subsidiary relationship
        company_number TEXT,                    -- Unique identifier for the company
        subsidiary_company TEXT,                -- Name of the subsidiary company
        subsidiary_company_id TEXT,             -- Unique identifier for the subsidiary company
        jurisdiction_code TEXT,                 -- Jurisdiction code for the subsidiary company
        status TEXT,                            -- Status of the subsidiary company
        type TEXT,                              -- Type of the subsidiary company
        link TEXT,                              -- Link to more information about the subsidiary company
        start_date TEXT,                        -- Start date of the subsidiary relationship
        end_date TEXT,                          -- End date of the subsidiary relationship
        statement_link TEXT,                    -- Link to the statement
        FOREIGN KEY(company_number) REFERENCES companies(company_number),  -- Foreign key to companies table
        FOREIGN KEY(subsidiary_company_id) REFERENCES companies(company_number),  -- Foreign key to subsidiary company
        FOREIGN KEY(jurisdiction_code) REFERENCES jurisdiction(code)  -- Foreign key to jurisdiction table
    ''', 'subsidiary relationships', {
        'id': 'Unique identifier for the subsidiary relationship',
        'company_number': 'Unique identifier for the company',
        'subsidiary_company': 'Name of the subsidiary company',
        'subsidiary_company_id': 'Unique identifier for the subsidiary company',
        'jurisdiction_code': 'Jurisdiction code for the subsidiary company',
        'status': 'Status of the subsidiary company',
        'type': 'Type of the subsidiary company',
        'link': 'Link to more information about the subsidiary company',
        'start_date': 'Start date of the subsidiary relationship',
        'end_date': 'End date of the subsidiary relationship',
        'statement_link': 'Link to the statement'
    }),
    ('mergers', '''
        id INTEGER PRIMARY KEY,                   -- Unique identifier for the merger
        company_number TEXT,                      -- Unique identifier for the company
        merged_company_name TEXT,                 -- Name of the merged company
        merged_company_id TEXT,                   -- Unique identifier for the merged company
        surviving_company_name TEXT,              -- Name of the surviving company
        surviving_company_id TEXT,                -- Unique identifier for the surviving company
        jurisdiction_id INTEGER,                  -- Jurisdiction of the merger
        statement_link TEXT,                      -- Link to the statement
        start_date TEXT,                          -- Start date of the merger
        end_date TEXT,                            -- End date of the merger
        raw_data TEXT,                            -- Raw data about the merger
        FOREIGN KEY(company_number) REFERENCES companies(company_number),  -- Foreign key to companies table
        FOREIGN KEY(merged_company_id) REFERENCES companies(company_number),  -- Foreign key to merged company in companies table
        FOREIGN KEY(surviving_company_id) REFERENCES companies(company_number),  -- Foreign key to surviving company in companies table
        FOREIGN KEY(jurisdiction_id) REFERENCES jurisdiction(id)  -- Foreign key to jurisdiction table
    ''', 'mergers, including details about the merged and surviving companies', {
        'id': 'Unique identifier for the merger',
        'company_number': 'Unique identifier for the company',
        'merged_company_name': 'Name of the merged company',
        'merged_company_id': 'Unique identifier for the merged company',
        'surviving_company_name': 'Name of the surviving company',
        'surviving_company_id': 'Unique identifier for the surviving company',
        'jurisdiction_id': 'Jurisdiction of the merger',
        'statement_link': 'Link to the statement',
        'start_date': 'Start date of the merger',
        'end_date': 'End date of the merger',
        'raw_data': 'Raw data about the merger'
    }),
    ('control_statements', '''
        id INTEGER PRIMARY KEY AUTOINCREMENT,           -- Unique identifier for the control statement
        company_number TEXT,                            -- Unique identifier for the company
        controlled_company_name TEXT,                   -- Name of the controlled company
        controlled_company_number TEXT,                 -- Unique identifier for the controlled company
        controlled_company_jurisdiction TEXT,           -- Jurisdiction code for the controlled company
        controlling_company_name TEXT,                  -- Name of the controlling company
        controlling_company_number TEXT,                -- Unique identifier for the controlling company
        controlling_company_jurisdiction TEXT,          -- Jurisdiction code for the controlling company
        start_date TEXT,                                -- Start date of the control statement
        end_date TEXT,                                  -- End date of the control statement
        mechanisms TEXT,                                -- Control mechanisms used
        statement_link TEXT,                            -- Link to the control statement document
        raw_data TEXT,                                  -- Raw data related to the control statement
        FOREIGN KEY(company_number) REFERENCES companies(company_number),              -- Foreign key to companies table
        FOREIGN KEY(controlled_company_number) REFERENCES companies(company_number),   -- Foreign key to companies table
        FOREIGN KEY(controlling_company_number) REFERENCES companies(company_number),  -- Foreign key to companies table
        FOREIGN KEY(controlled_company_jurisdiction) REFERENCES jurisdiction(code),    -- Foreign key to jurisdiction table
        FOREIGN KEY(controlling_company_jurisdiction) REFERENCES jurisdiction(code)    -- Foreign key to jurisdiction table
    ''', 'control statements between companies', {
        'id': 'Unique identifier for the control statement',
        'company_number': 'Unique identifier for the company',
        'controlled_company_name': 'Name of the controlled company',
        'controlled_company_number': 'Unique identifier for the controlled company',
        'controlled_company_jurisdiction': 'Jurisdiction code for the controlled company',
        'controlling_company_name': 'Name of the controlling company',
        'controlling_company_number': 'Unique identifier for the controlling company',
        'controlling_company_jurisdiction': 'Jurisdiction code for the controlling company',
        'start_date': 'Start date of the control statement',
        'end_date': 'End date of the control statement',
        'mechanisms': 'Control mechanisms used',
        'statement_link': 'Link to the control statement document',
        'raw_data': 'Raw data related to the control statement'
    }),
    ('control_mechanisms', '''
        id INTEGER PRIMARY KEY,             -- Unique identifier for the control mechanism
        mechanism TEXT                      -- Description of the control mechanism
    ''', 'control mechanisms. Control mechanisms define the methods of control or influence one entity has over another.', {
        'id': 'Unique identifier for the control mechanism',
        'mechanism': 'Description of the control mechanism'
    }),
    ('control_statement_mechanisms', '''
        control_statement_id INTEGER,       -- Identifier for the control statement
        mechanism_id INTEGER,               -- Identifier for the control mechanism
        FOREIGN KEY(control_statement_id) REFERENCES control_statements(id),  -- Foreign key to control statements
        FOREIGN KEY(mechanism_id) REFERENCES control_mechanisms(id),          -- Foreign key to control mechanisms
        PRIMARY KEY (control_statement_id, mechanism_id)                      -- Composite primary key for uniqueness
    ''', 'Table to map control statements to their mechanisms.', {
        'control_statement_id': 'Identifier for the control statement',
        'mechanism_id': 'Identifier for the control mechanism'
    }),
    ('person_akas', '''
        id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Unique identifier for the alternate name record
        person_id INTEGER,                     -- Identifier for the person
        aka TEXT,                              -- Alternate name (Also Known As)
        FOREIGN KEY(person_id) REFERENCES people(id)  -- Foreign key to people table
    ''', 'alternate names (AKAs) for people.', {
        'id': 'Unique identifier for the alternate name record',
        'person_id': 'Identifier for the person',
        'aka': 'Alternate name (Also Known As)'
    }),
    ('company_addresses', '''
        company_number TEXT,                 -- Unique identifier for the company
        address_id INTEGER,                  -- Identifier for the address
        FOREIGN KEY(company_number) REFERENCES companies(company_number),  -- Foreign key to companies table
        FOREIGN KEY(address_id) REFERENCES addresses(id),                  -- Foreign key to addresses table
        PRIMARY KEY (company_number, address_id)                           -- Composite primary key for uniqueness
    ''', 'Table to map companies to their addresses.', {
        'company_number': 'Unique identifier for the company',
        'address_id': 'Identifier for the address'
    }),
    ('company_people', '''
        company_number TEXT,                 -- Unique identifier for the company
        person_id INTEGER,                   -- Identifier for the person
        FOREIGN KEY(company_number) REFERENCES companies(company_number),  -- Foreign key to companies table
        FOREIGN KEY(person_id) REFERENCES people(id),                      -- Foreign key to people table
        PRIMARY KEY (company_number, person_id)                            -- Composite primary key for uniqueness
    ''', 'Table to map companies to their associated people.', {
        'company_number': 'Unique identifier for the company',
        'person_id': 'Identifier for the person'
    }),
    ('people_addresses', '''
        person_id INTEGER,                   -- Identifier for the person
        address_id INTEGER,                  -- Identifier for the address
        FOREIGN KEY(person_id) REFERENCES people(id),                      -- Foreign key to people table
        FOREIGN KEY(address_id) REFERENCES addresses(id),                  -- Foreign key to addresses table
        PRIMARY KEY (person_id, address_id)                                -- Composite primary key for uniqueness
    ''', 'Table to map people to their addresses.', {
        'person_id': 'Identifier for the person',
        'address_id': 'Identifier for the address'
    }),
    ('person_officers', '''
        person_id INTEGER,                   -- Identifier for the person
        officer_id INTEGER,                  -- Identifier for the officer
        FOREIGN KEY(person_id) REFERENCES people(id),                      -- Foreign key to people table
        FOREIGN KEY(officer_id) REFERENCES officers(id),                   -- Foreign key to officers table
        PRIMARY KEY (person_id, officer_id)                                -- Composite primary key for uniqueness
    ''', 'Table to map people to their officer roles.', {
        'person_id': 'Identifier for the person',
        'officer_id': 'Identifier for the officer'
    }),
    ('company_officers', '''
        company_number TEXT,                 -- Unique identifier for the company
        officer_id INTEGER,                  -- Identifier for the officer
        FOREIGN KEY(company_number) REFERENCES companies(company_number),  -- Foreign key to companies table
        FOREIGN KEY(officer_id) REFERENCES officers(id),                   -- Foreign key to officers table
        PRIMARY KEY (company_number, officer_id)                           -- Composite primary key for uniqueness
    ''', 'Table to map companies to their officers.', {
        'company_number': 'Unique identifier for the company',
        'officer_id': 'Identifier for the officer'
    }),
    ('url_catalog', '''
        id INTEGER PRIMARY KEY,              -- Unique identifier for the URL
        url TEXT UNIQUE,                     -- URL for the resource
        company_number TEXT,                 -- Unique identifier for the company
        jurisdiction_id INTEGER,             -- Identifier for the jurisdiction
        completed BOOLEAN DEFAULT FALSE,     -- Flag indicating if the URL has been processed
        html_content TEXT,                   -- HTML content of the page
        parent_id INTEGER,                   -- Identifier for the parent URL
        FOREIGN KEY(parent_id) REFERENCES url_catalog(id),                  -- Foreign key to parent URL
        FOREIGN KEY(company_number) REFERENCES companies(company_number),  -- Foreign key to companies table
        FOREIGN KEY(jurisdiction_id) REFERENCES jurisdiction(id)           -- Foreign key to jurisdiction table
    ''', 'Table to catalog URLs and their metadata.', {
        'id': 'Unique identifier for the URL',
        'url': 'URL for the resource',
        'company_number': 'Unique identifier for the company',
        'jurisdiction_id': 'Identifier for the jurisdiction',
        'completed': 'Flag indicating if the URL has been processed',
        'html_content': 'HTML content of the page',
        'parent_id': 'Identifier for the parent URL'
    }),
    ('lei_records', '''
        lei TEXT PRIMARY KEY,                -- Legal Entity Identifier (LEI)
        entity_legal_name TEXT,              -- Legal name of the entity
        registration_status TEXT,            -- Status of the LEI registration
        entity_status TEXT,                  -- Status of the entity
        jurisdiction_id INTEGER,             -- Identifier for the jurisdiction
        registered_address TEXT,             -- Registered address of the entity
        headquarters_address TEXT,           -- Headquarters address of the entity
        registration_date TEXT,              -- Date of registration
        next_renewal_date TEXT,              -- Next renewal date for the LEI
        managing_lou TEXT,                   -- Managing Local Operating Unit (LOU)
        validated_at TEXT,                   -- Date of validation
        FOREIGN KEY(jurisdiction_id) REFERENCES jurisdiction(id)  -- Foreign key to jurisdiction table
    ''', 'LEI records.', {
        'lei': 'Legal Entity Identifier (LEI)',
        'entity_legal_name': 'Legal name of the entity',
        'registration_status': 'Status of the LEI registration',
        'entity_status': 'Status of the entity',
        'jurisdiction_id': 'Identifier for the jurisdiction',
        'registered_address': 'Registered address of the entity',
        'headquarters_address': 'Headquarters address of the entity',
        'registration_date': 'Date of registration',
        'next_renewal_date': 'Next renewal date for the LEI',
        'managing_lou': 'Managing Local Operating Unit (LOU)',
        'validated_at': 'Date of validation'
    }),

    ('lei_entities', '''
        id INTEGER PRIMARY KEY,              -- Unique identifier for the LEI entity
        lei TEXT,                            -- Legal Entity Identifier (LEI)
        entity_name TEXT,                    -- Name of the entity
        country TEXT,                        -- Country of the entity
        entity_type TEXT,                    -- Type of the entity
        FOREIGN KEY(lei) REFERENCES lei_records(lei)  -- Foreign key to LEI records table
    ''', 'LEI entities.', {
        'id': 'Unique identifier for the LEI entity',
        'lei': 'Legal Entity Identifier (LEI)',
        'entity_name': 'Name of the entity',
        'country': 'Country of the entity',
        'entity_type': 'Type of the entity'
    }),
    ('lei_data', '''
        id TEXT PRIMARY KEY,                    -- Unique identifier for the LEI data
        lei TEXT UNIQUE,                        -- Legal Entity Identifier (LEI) code
        status TEXT,                            -- Status of the LEI
        creation_date TEXT,                     -- Creation date of the LEI
        registered_as TEXT,                     -- Registered name of the entity
        jurisdiction_id INTEGER,                -- Identifier for the jurisdiction
        category TEXT,                          -- Category of the LEI
        legal_form_id TEXT,                     -- Identifier for the legal form
        legal_form_other TEXT,                  -- Other legal form details
        associated_lei TEXT,                    -- Associated LEI code
        associated_name TEXT,                   -- Associated name
        expiration_date TEXT,                   -- Expiration date of the LEI
        expiration_reason TEXT,                 -- Reason for expiration
        successor_lei TEXT,                     -- Successor LEI code
        successor_name TEXT,                    -- Successor name
        sub_category TEXT,                      -- Sub-category of the LEI
        FOREIGN KEY (lei) REFERENCES lei_records(lei),  -- Foreign key to LEI records table
        FOREIGN KEY (jurisdiction_id) REFERENCES jurisdiction(id)  -- Foreign key to jurisdiction table
    ''', 'LEI data.', {
        'id': 'Unique identifier for the LEI data',
        'lei': 'Legal Entity Identifier (LEI) code',
        'status': 'Status of the LEI',
        'creation_date': 'Creation date of the LEI',
        'registered_as': 'Registered name of the entity',
        'jurisdiction_id': 'Identifier for the jurisdiction',
        'category': 'Category of the LEI',
        'legal_form_id': 'Identifier for the legal form',
        'legal_form_other': 'Other legal form details',
        'associated_lei': 'Associated LEI code',
        'associated_name': 'Associated name',
        'expiration_date': 'Expiration date of the LEI',
        'expiration_reason': 'Reason for expiration',
        'successor_lei': 'Successor LEI code',
        'successor_name': 'Successor name',
        'sub_category': 'Sub-category of the LEI'
    }),
    ('lei_entity', '''
        id TEXT PRIMARY KEY,                    -- Unique identifier for the LEI entity
        lei TEXT,                               -- Legal Entity Identifier (LEI) code
        legal_name TEXT,                        -- Legal name of the entity
        language TEXT,                          -- Language of the legal name
        FOREIGN KEY (lei) REFERENCES lei_data(lei)  -- Foreign key to LEI data table
    ''', 'LEI entity details.', {
        'id': 'Unique identifier for the LEI entity',
        'lei': 'Legal Entity Identifier (LEI) code',
        'legal_name': 'Legal name of the entity',
        'language': 'Language of the legal name'
    }),
    ('lei_address', '''
        id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique identifier for the address
        lei TEXT,                               -- Legal Entity Identifier (LEI) code
        address_type TEXT,                      -- Type of the address (e.g., registered, headquarters)
        language TEXT,                          -- Language of the address
        address_lines TEXT,                     -- Lines of the address
        city TEXT,                              -- City of the address
        region TEXT,                            -- Region of the address
        country TEXT,                           -- Country of the address
        postal_code TEXT,                       -- Postal code of the address
        FOREIGN KEY (lei) REFERENCES lei_data(lei)  -- Foreign key to LEI data table
    ''', 'addresses associated with LEIs.', {
        'id': 'Unique identifier for the address',
        'lei': 'Legal Entity Identifier (LEI) code',
        'address_type': 'Type of the address',
        'language': 'Language of the address',
        'address_lines': 'Lines of the address',
        'city': 'City of the address',
        'region': 'Region of the address',
        'country': 'Country of the address',
        'postal_code': 'Postal code of the address'
    }),
    ('lei_registration', '''
        id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique identifier for the registration
        lei TEXT,                               -- Legal Entity Identifier (LEI) code
        initial_registration_date TEXT,         -- Initial registration date of the LEI
        last_update_date TEXT,                  -- Last update date of the LEI
        status TEXT,                            -- Status of the LEI registration
        next_renewal_date TEXT,                 -- Next renewal date of the LEI
        managing_lou TEXT,                      -- Managing Local Operating Unit (LOU)
        corroboration_level TEXT,               -- Level of corroboration
        validated_at_id TEXT,                   -- Identifier for the validation
        validated_as TEXT,                      -- Validated as type
        FOREIGN KEY (lei) REFERENCES lei_data(lei)  -- Foreign key to LEI data table
    ''', 'LEI registration details.', {
        'id': 'Unique identifier for the registration',
        'lei': 'Legal Entity Identifier (LEI) code',
        'initial_registration_date': 'Initial registration date of the LEI',
        'last_update_date': 'Last update date of the LEI',
        'status': 'Status of the LEI registration',
        'next_renewal_date': 'Next renewal date of the LEI',
        'managing_lou': 'Managing Local Operating Unit (LOU)',
        'corroboration_level': 'Level of corroboration',
        'validated_at_id': 'Identifier for the validation',
        'validated_as': 'Validated as type'
    }),
    ('lei_relationships', '''
        id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique identifier for the relationship
        lei TEXT,                               -- Legal Entity Identifier (LEI) code
        relationship_type TEXT,                 -- Type of the relationship
        related_link TEXT,                      -- Link to the related entity
        FOREIGN KEY (lei) REFERENCES lei_data(lei)  -- Foreign key to LEI data table
    ''', 'relationships between LEI entities.', {
        'id': 'Unique identifier for the relationship',
        'lei': 'Legal Entity Identifier (LEI) code',
        'relationship_type': 'Type of the relationship',
        'related_link': 'Link to the related entity'
    }),
    ('lei_links', '''
        id INTEGER PRIMARY KEY AUTOINCREMENT,   -- Unique identifier for the link
        lei TEXT,                               -- Legal Entity Identifier (LEI) code
        self_link TEXT,                         -- Self link
        managing_lou_link TEXT,                 -- Link to the managing LOU
        lei_issuer_link TEXT,                   -- Link to the LEI issuer
        field_modifications_link TEXT,          -- Link to field modifications
        direct_parent_link TEXT,                -- Link to the direct parent
        ultimate_parent_link TEXT,              -- Link to the ultimate parent
        direct_children_link TEXT,              -- Link to direct children
        ultimate_children_link TEXT,            -- Link to ultimate children
        FOREIGN KEY (lei) REFERENCES lei_data(lei)  -- Foreign key to LEI data table
    ''', 'various links related to LEI entities.', {
        'id': 'Unique identifier for the link',
        'lei': 'Legal Entity Identifier (LEI) code',
        'self_link': 'Self link',
        'managing_lou_link': 'Link to the managing LOU',
        'lei_issuer_link': 'Link to the LEI issuer',
        'field_modifications_link': 'Link to field modifications',
        'direct_parent_link': 'Link to the direct parent',
        'ultimate_parent_link': 'Link to the ultimate parent',
        'direct_children_link': 'Link to direct children',
        'ultimate_children_link': 'Link to ultimate children'
    })
]