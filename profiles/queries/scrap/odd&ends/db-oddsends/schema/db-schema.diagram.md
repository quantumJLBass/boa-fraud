classDiagram
direction BT
class addresses {
   varchar normalized_address
   varchar street
   varchar street_2
   varchar city
   varchar state
   varchar postal_code
   varchar country
   text raw_data
   integer id
}
class assertions {
   varchar company_number
   varchar title
   varchar description
   varchar link
   integer id
}
class attributes {
   varchar company_number
   varchar name
   varchar value
   integer id
}
class classifications {
   varchar classification
   integer id
}
class companies {
   text company_number
   text company_name
   text status
   text incorporation_date
   text company_type
   text jurisdiction
   text registered_address
   text agent_name
   text agent_address
   text parent_company_name
   text parent_company_url
   integer jurisdiction_id
}
class company_addresses {
   varchar company_number
   integer address_id
}
class company_akas {
   varchar company_number
   varchar aka
   varchar start_date
   varchar end_date
   varchar(12) type
   varchar(2) language
   integer id
}
class company_industry_codes {
   varchar statement_link
   varchar company_number
   integer industry_code_id
}
class company_officers {
   varchar company_number
   integer officer_id
}
class company_people {
   varchar company_number
   integer person_id
}
class control_mechanisms {
   text mechanism
   integer id
}
class control_statement_mechanisms {
   integer control_statement_id
   integer mechanism_id
}
class control_statements {
   varchar company_number
   varchar controlled_company_name
   varchar controlled_company_number
   varchar controlled_company_jurisdiction
   varchar controlling_company_name
   varchar controlling_company_number
   varchar controlling_company_jurisdiction
   varchar start_date
   varchar end_date
   text mechanisms
   varchar statement_link
   text raw_data
   integer id
}
class events {
   varchar company_number
   varchar start_date
   varchar end_date
   varchar description
   varchar link
   integer id
}
class filings {
   varchar company_number
   varchar date
   varchar description
   varchar link
   integer id
}
class gazette_notices {
   varchar company_number
   varchar date
   integer publication_id
   text notice
   integer classification_id
   integer id
}
class identifier_delegate {
   varchar company_number
   varchar identifier_system
   varchar identifier
   varchar categories
   integer id
}
class industry_codes {
   varchar code
   varchar description
   varchar code_scheme
   integer id
}
class jurisdiction {
   varchar code
   varchar name
   varchar country
   varchar full_name
   varchar state_abv
   varchar county
   varchar city
   float longitude
   float latitude
   varchar zip_code
   varchar area_code
   integer parent_jurisdiction
   integer id
}
class jurisdiction_old {
   varchar code
   varchar name
   varchar country
   varchar full_name
   varchar state_abv
   integer parent_jurisdiction
   integer id
}
class lei_address {
   varchar lei
   varchar address_type
   varchar language
   text address_lines
   varchar city
   varchar region
   varchar country
   varchar postal_code
   integer id
}
class lei_data {
   varchar lei
   varchar status
   varchar creation_date
   varchar registered_as
   integer jurisdiction_id
   varchar category
   varchar legal_form_id
   varchar legal_form_other
   varchar associated_lei
   varchar associated_name
   varchar expiration_date
   varchar expiration_reason
   varchar successor_lei
   varchar successor_name
   varchar sub_category
   varchar id
}
class lei_entities {
   varchar lei
   varchar entity_name
   varchar country
   varchar entity_type
   integer id
}
class lei_entity {
   varchar lei
   varchar legal_name
   varchar language
   varchar id
}
class lei_links {
   varchar lei
   varchar self_link
   varchar managing_lou_link
   varchar lei_issuer_link
   varchar field_modifications_link
   varchar direct_parent_link
   varchar ultimate_parent_link
   varchar direct_children_link
   varchar ultimate_children_link
   integer id
}
class lei_records {
   varchar entity_legal_name
   varchar registration_status
   varchar entity_status
   integer jurisdiction_id
   varchar registered_address
   varchar headquarters_address
   varchar registration_date
   varchar next_renewal_date
   varchar managing_lou
   varchar validated_at
   varchar lei
}
class lei_registration {
   varchar lei
   varchar initial_registration_date
   varchar last_update_date
   varchar status
   varchar next_renewal_date
   varchar managing_lou
   varchar corroboration_level
   varchar validated_at_id
   varchar validated_as
   integer id
}
class lei_relationships {
   varchar lei
   varchar relationship_type
   varchar related_link
   integer id
}
class links {
   varchar company_number
   varchar link
   integer id
}
class mergers {
   varchar company_number
   varchar merged_company_name
   varchar merged_company_id
   varchar surviving_company_name
   varchar surviving_company_id
   integer jurisdiction_id
   varchar statement_link
   varchar start_date
   varchar end_date
   text raw_data
   integer id
}
class officers {
   varchar company_number
   varchar occurrence_number
   varchar name
   varchar role
   varchar status
   varchar link
   varchar address
   varchar start_date
   varchar end_date
   varchar type
   integer id
}
class people {
   varchar name
   text raw_data
   integer id
}
class people_addresses {
   integer person_id
   integer address_id
}
class person_akas {
   integer person_id
   varchar aka
   varchar start_date
   varchar end_date
   varchar(12) type
   varchar(2) language
   integer id
}
class person_officers {
   integer person_id
   integer officer_id
}
class publications {
   varchar name
   varchar company_number
   integer id
}
class related_relationships {
   varchar company_number
   varchar related_company
   varchar related_company_id
   varchar jurisdiction_code
   varchar status
   varchar type
   varchar link
   varchar start_date
   varchar end_date
   varchar statement_link
   integer id
}
class share_parcel {
   varchar company_number
   integer shareholder_id_person
   varchar shareholder_id_company
   varchar shareholder
   varchar number_of_shares
   varchar voting_percentage
   integer id
}
class sqlite_master {
   text type
   text name
   text tbl_name
   int rootpage
   text sql
}
class sqlite_sequence {
   unknown name
   unknown seq
}
class subsidiary_relationships {
   varchar company_number
   varchar subsidiary_company
   varchar subsidiary_company_id
   varchar jurisdiction_code
   varchar status
   varchar type
   varchar link
   varchar start_date
   varchar end_date
   varchar statement_link
   integer id
}
class total_shares {
   varchar company_number
   integer number
   varchar share_class
   integer id
}
class trademark_registrations {
   varchar company_number
   varchar trademark
   varchar registration_date
   varchar status
   integer id
}
class url_catalog {
   integer parent_id
   text company_number
   text jurisdiction
   text url
   text html_content
   datetime cached_on
   boolean completed
   integer id
}

assertions  -->  companies : company_number
attributes  -->  companies : company_number
companies  -->  jurisdiction : jurisdiction_id:id
company_addresses  -->  addresses : address_id:id
company_addresses  -->  companies : company_number
company_akas  -->  companies : company_number
company_industry_codes  -->  companies : company_number
company_industry_codes  -->  industry_codes : industry_code_id:id
company_officers  -->  companies : company_number
company_officers  -->  officers : officer_id:id
company_people  -->  companies : company_number
company_people  -->  people : person_id:id
control_statement_mechanisms  -->  control_mechanisms : mechanism_id:id
control_statement_mechanisms  -->  control_statements : control_statement_id:id
control_statements  -->  companies : company_number
control_statements  -->  companies : controlling_company_number:company_number
control_statements  -->  companies : controlled_company_number:company_number
control_statements  -->  jurisdiction : controlling_company_jurisdiction:code
control_statements  -->  jurisdiction : controlled_company_jurisdiction:code
events  -->  companies : company_number
filings  -->  companies : company_number
gazette_notices  -->  classifications : classification_id:id
gazette_notices  -->  companies : company_number
gazette_notices  -->  publications : publication_id:id
identifier_delegate  -->  companies : company_number
jurisdiction  -->  jurisdiction : parent_jurisdiction:id
jurisdiction_old  -->  jurisdiction : parent_jurisdiction:id
lei_address  -->  lei_data : lei
lei_data  -->  jurisdiction : jurisdiction_id:id
lei_entities  -->  lei_records : lei
lei_entity  -->  lei_data : lei
lei_links  -->  lei_data : lei
lei_records  -->  jurisdiction : jurisdiction_id:id
lei_registration  -->  lei_data : lei
lei_relationships  -->  lei_data : lei
links  -->  companies : company_number
mergers  -->  companies : company_number
mergers  -->  companies : surviving_company_id:company_number
mergers  -->  companies : merged_company_id:company_number
mergers  -->  jurisdiction : jurisdiction_id:id
officers  -->  companies : company_number
people_addresses  -->  addresses : address_id:id
people_addresses  -->  people : person_id:id
person_akas  -->  people : person_id:id
person_officers  -->  officers : officer_id:id
person_officers  -->  people : person_id:id
publications  -->  companies : company_number
related_relationships  -->  companies : company_number
related_relationships  -->  companies : related_company_id:company_number
related_relationships  -->  jurisdiction : jurisdiction_code:code
share_parcel  -->  companies : company_number
share_parcel  -->  companies : shareholder_id_company:company_number
share_parcel  -->  people : shareholder_id_person:id
subsidiary_relationships  -->  companies : subsidiary_company_id:company_number
subsidiary_relationships  -->  companies : company_number
subsidiary_relationships  -->  jurisdiction : jurisdiction_code:code
total_shares  -->  companies : company_number
trademark_registrations  -->  companies : company_number
url_catalog  -->  companies : company_number
url_catalog  -->  url_catalog : parent_id:id
