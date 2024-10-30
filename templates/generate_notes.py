import os
import json
from datetime import datetime
import re

# Define paths
json_directory = "path/to/your/json/data"  # Update this path
output_directory = "path/to/your/obsidian/vault"  # Update this path

def format_date(date_str):
    try:
        date_part = re.split(r"\s\(", date_str)[0]
        date_obj = datetime.strptime(date_part, '%d %B %Y')
        return date_obj.strftime('%d %B %Y')
    except ValueError:
        return date_str

def create_note_content(data, root_url):
    attributes = data.get('Attributes', {})
    events = data.get('Events', [])
    filings = data.get('Filings', [])
    assertions = data.get('Assertions', {})
    officers = data.get('Officers', [])
    branches = data.get('Branch_relationship', [])
    links = data.get('Links', [])

    sections = [
        f"## General Data\n{format_attributes(attributes)}" if attributes else "",
        f"## Directors / Officers\n{format_table(officers, 'officer')}" if officers else "",
        f"## Events\n{format_events(events)}" if events else "",
        f"## Filings\n{format_filings(filings)}" if filings else "",
        f"## Assertions\n{format_assertions(assertions)}" if assertions else "",
        f"## Branch Relationships\n{format_branch_relationships(branches)}" if branches else "",
        f"## Links\n{format_links(links)}" if links else "",
    ]

    sections = [section for section in sections if section]  # Filter out empty sections

    frontmatter = f"""---
page-title: Company Overview - {data['Company Name']}
url/uri:
  - {root_url}
date: {format_date(attributes.get('Incorporation Date', ''))}
tags:
  - Company-Details/General-Information
company-number: {attributes.get('Company Number', '')}
native-company-number: {attributes.get('Native Company Number', '')}
status: {attributes.get('Status', '')}
incorporation-date: {format_date(attributes.get('Incorporation Date', ''))}
company-type: {attributes.get('Company Type', '')}
jurisdiction: {attributes.get('Jurisdiction', '')}
registered-address: {attributes.get('Registered Address', '')}
---

"""

    return frontmatter + "\n".join(sections) + f"\n\n## Source\n[Source]({root_url})\n"

def format_attributes(attributes):
    attributes_md = ""
    for key, value in attributes.items():
        if isinstance(value, list):
            value = ', '.join(value)
        attributes_md += f"{key.lower().replace(' ', '-')}: {value}\n"
    return attributes_md

def format_table(entries, entry_type='officer'):
    if not entries:
        return ""
    table = "| Name | Role | Status | Link |\n|------|------|--------|------|\n"
    for entry in entries:
        table += f"| {entry['Name']} | {entry.get('Role', 'N/A')} | {entry.get('Status', 'N/A')} | [Link]({entry.get('Link', '#')}) |\n"
    return table

def format_events(events):
    if not events:
        return ""
    event_list = "| Date | Event | Link |\n|------|-------|------|\n"
    for event in events:
        event_list += f"| {event['Date']} | {event['Description']} | [Link]({event.get('Link', '#')}) |\n"
    return event_list

def format_filings(filings):
    if not filings:
        return ""
    filing_list = "| Date | Description |\n|------|-------------|\n"
    for filing in filings:
        filing_list += f"| {filing['Date']} | {filing['Description']} |\n"
    return filing_list

def format_assertions(assertions):
    if not assertions:
        return ""
    assertion_list = "| Title | Description |\n|-------|-------------|\n"
    if 'Company Addresses' in assertions:
        for address in assertions['Company Addresses']:
            assertion_list += f"| {address['Title']} | {address['Description']} |\n"
    if 'Telephone Numbers' in assertions:
        for phone in assertions['Telephone Numbers']:
            assertion_list += f"| {phone['Title']} | {phone['Description']} |\n"
    return assertion_list

def format_branch_relationships(branches):
    if not branches:
        return ""
    branch_list = "| Company | Jurisdiction | Status | Type |\n|---------|--------------|--------|------|\n"
    for branch in branches:
        branch_list += f"| {branch['Company']} | {branch.get('Jurisdiction', 'N/A')} | {branch.get('Status', 'N/A')} | {branch.get('Type', 'N/A')} |\n"
    return branch_list

def format_links(links):
    if not links:
        return ""
    link_list = "| Link |\n|------|\n"
    for link in links:
        link_list += f"| [Link]({link}) |\n"
    return link_list

# Process JSON files
json_files = [f for f in os.listdir(json_directory) if f.endswith('.json')]
for json_file in json_files:
    with open(os.path.join(json_directory, json_file), 'r', encoding='utf-8') as file:
        data = json.load(file)
        for entity_url, entity_data in data.items():
            if 'Company Name' in entity_data:
                entity_name = entity_data['Company Name']
                root_url = entity_url
                note_content = create_note_content(entity_data, root_url)
                output_path = os.path.join(output_directory, f"{entity_name}.md")
                with open(output_path, 'w', encoding='utf-8') as note_file:
                    note_file.write(note_content)

print("Notes have been generated and saved to the output directory.")
