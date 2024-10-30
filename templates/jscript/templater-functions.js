module.exports = {
    root_url: function (tp) {
        // Return the root URL from the JSON data
        return tp.file.path.split('/')[0]; // Adjust this to your structure
    },
    get_attribute: function (tp, attribute) {
        // Fetch the attribute from the JSON data
        let data = JSON.parse(tp.file.content);
        return data.Attributes[attribute] || '';
    },
    format_attributes: function (tp) {
        let data = JSON.parse(tp.file.content).Attributes;
        let attributes_md = "";
        for (let key in data) {
            if (Array.isArray(data[key])) {
                value = data[key].join(', ');
            } else {
                value = data[key];
            }
            attributes_md += `${key.toLowerCase().replace(' ', '-')}: ${value}\n`;
        }
        return attributes_md;
    },
    get_officers: function (tp) {
        // Fetch officers data from the JSON
        let data = JSON.parse(tp.file.content);
        return data.Officers || [];
    },
    format_table: function (entries, entry_type = 'officer') {
        if (!entries.length) {
            return "";
        }
        let table = "| Name | Role | Status | Link |\n|------|------|--------|------|\n";
        entries.forEach(entry => {
            table += `| ${entry.Name} | ${entry.Role || 'N/A'} | ${entry.Status || 'N/A'} | [Link](${entry.Link || '#'}) |\n`;
        });
        return table;
    },
    get_events: function (tp) {
        // Fetch events data from the JSON
        let data = JSON.parse(tp.file.content);
        return data.Events || [];
    },
    format_events: function (events) {
        if (!events.length) {
            return "";
        }
        let event_list = "| Date | Event | Link |\n|------|-------|------|\n";
        events.forEach(event => {
            event_list += `| ${event.Date} | ${event.Description} | [Link](${event.Link || '#'}) |\n`;
        });
        return event_list;
    },
    get_filings: function (tp) {
        // Fetch filings data from the JSON
        let data = JSON.parse(tp.file.content);
        return data.Filings || [];
    },
    format_filings: function (filings) {
        if (!filings.length) {
            return "";
        }
        let filing_list = "| Date | Description |\n|------|-------------|\n";
        filings.forEach(filing => {
            filing_list += `| ${filing.Date} | ${filing.Description} |\n`;
        });
        return filing_list;
    },
    get_assertions: function (tp) {
        // Fetch assertions data from the JSON
        let data = JSON.parse(tp.file.content);
        return data.Assertions || {};
    },
    format_assertions: function (assertions) {
        if (!Object.keys(assertions).length) {
            return "";
        }
        let assertion_list = "| Title | Description |\n|-------|-------------|\n";
        if ('Company Addresses' in assertions) {
            assertions['Company Addresses'].forEach(address => {
                assertion_list += `| ${address.Title} | ${address.Description} |\n`;
            });
        }
        if ('Telephone Numbers' in assertions) {
            assertions['Telephone Numbers'].forEach(phone => {
                assertion_list += `| ${phone.Title} | ${phone.Description} |\n`;
            });
        }
        return assertion_list;
    },
    get_branches: function (tp) {
        // Fetch branch relationships data from the JSON
        let data = JSON.parse(tp.file.content);
        return data.Branch_relationship || [];
    },
    format_branch_relationships: function (branches) {
        if (!branches.length) {
            return "";
        }
        let branch_list = "| Company | Jurisdiction | Status | Type |\n|---------|--------------|--------|------|\n";
        branches.forEach(branch => {
            branch_list += `| ${branch.Company} | ${branch.Jurisdiction || 'N/A'} | ${branch.Status || 'N/A'} | ${branch.Type || 'N/A'} |\n`;
        });
        return branch_list;
    },
    get_links: function (tp) {
        // Fetch links data from the JSON
        let data = JSON.parse(tp.file.content);
        return data.Links || [];
    },
    format_links: function (links) {
        if (!links.length) {
            return "";
        }
        let link_list = "| Link |\n|------|\n";
        links.forEach(link => {
            link_list += `| [Link](${link}) |\n`;
        });
        return link_list;
    }
};
