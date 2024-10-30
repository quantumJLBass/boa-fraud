from textwrap import dedent
from typing import Dict, List

from services.applogging import logger
from settings.settings import i


def render_relationships(branches: List[Dict[str, str]]) -> str:
    """
    Formats the given list of branch relationships into a table.

    Args:
        branches (list[dict]): A list of dictionaries representing branch relationships. Each dictionary should have the following keys:
            - 'Company' (str): The name of the company.
            - 'Company ID' (str): The ID of the company.
            - 'Jurisdiction' (str, optional): The jurisdiction of the branch. Defaults to 'N/A' if not provided.
            - 'Status' (str, optional): The status of the branch. Defaults to 'N/A' if not provided.
            - 'Type' (str, optional): The type of the branch. Defaults to 'N/A' if not provided.
            - 'Link' (str, optional): The link associated with the branch. Defaults to 'N/A' if not provided.
            - 'Start Date' (str, optional): The start date of the branch. Defaults to 'N/A' if not provided.
            - 'End Date' (str, optional): The end date of the branch. Defaults to 'N/A' if not provided.
            - 'statement_link' (str, optional): The link to the relationship statement. Defaults to 'N/A' if not provided.

    Returns:
        str: A string representing the formatted table with the branch relationships.

    Example:
        >>> branches = [
        ...     {'Company': 'Company A','Company ID': 'Company A ID', 'Jurisdiction': 'Jurisdiction 1', 'Status': 'Active', 'Type': 'Branch', 'Link': 'https://example.com/1', 'Start Date': '01 Jan 2000', 'End Date': '', 'statement_link': 'https://example.com/statement/1'},
        ...     {'Company': 'Company B','Company ID': 'Company B ID',  'Jurisdiction': 'Jurisdiction 2', 'Status': 'Inactive', 'Type': 'Branch', 'Link': 'https://example.com/2', 'Start Date': '01 Jan 2000', 'End Date': '01 Jan 2020', 'statement_link': 'https://example.com/statement/2'},
        ... ]
        >>> format_branch_relationships(branches)
        '| Company                         | Jurisdiction         | Jurisdiction         | Status   | Type       | Link                              | Start Date   | End Date     | Statement Link                     |\n|----------------------------------|----------------------|----------------------|----------|------------|-----------------------------------|--------------|--------------|-----------------------------------|\n| [[Company A]]                    | Company A ID         | Jurisdiction 1       | Active   | Branch     | [Link](https://example.com/1)     | 01 Jan 2000  | N/A          | [Statement](https://example.com/1) |\n| [[Company B]]                    | Company B ID         | Jurisdiction B       | Inactive | Branch     | [Link](https://example.com/2)     | 01 Jan 2000  | 01 Jan 2020  | [Statement](https://example.com/2) |\n'
    """

    logger.info(f"{i()}✍️👔CREATING NOTE ---- format branch table started")
    if not branches:
        logger.info(f"{i()}❌✍️👔CREATING NOTE ---- Empty branch")
        return ""

    header = f"| {'Company':<30}| {'Company ID':<20}  | {'Jurisdiction':<20} | {'Status':<8} | {'Type':<10} | {'Link':<35} | {'Start Date':<12} | {'End Date':<12} | {'Statement Link':<35} |\n"
    separator = f"|{'':-<32}|{'':-<22}|{'':-<22}|{'':-<10}|{'':-<12}|{'':-<37}|{'':-<14}|{'':-<14}|{'':-<37}|\n"

    branch_list = header + separator

    for branch in branches:
        company = branch.get("Company", "N/A") or "N/A"
        company_id = branch.get("Company ID", "N/A") or "N/A"
        jurisdiction = branch.get("Jurisdiction", "N/A") or "N/A"
        status = branch.get("Status", "N/A") or "N/A"
        branch_type = branch.get("Type", "N/A") or "N/A"
        link = branch.get("Link", "N/A") or "N/A"
        start_date = branch.get("Start Date", "N/A") or "N/A"
        end_date = branch.get("End Date", "N/A") or "N/A"
        statement_link = branch.get("statement_link", "N/A") or "N/A"

        link_formatted = f"[Link]({link})" if link != "N/A" else "N/A"
        statement_link_formatted = (
            f"[Statement]({statement_link})" if statement_link != "N/A" else "N/A"
        )

        # branch_list += "| {company:<30} | {company_id:<20} | {jurisdiction:<20} | {status:<8} | {branch_type:<10} | {link_formatted:<35} | {start_date:<12} | {end_date:<12} | {statement_link_formatted:<35} |\n".format(
        #     company=f"[[{company}]]", company_id=company_id, jurisdiction=jurisdiction, status=status, branch_type=branch_type, link_formatted=link_formatted, start_date=start_date, end_date=end_date, statement_link_formatted=statement_link_formatted)

        # branch_list += (
        #     f"| {f'[[{company}]]':<30} | {company_id:<20} | {jurisdiction:<20} | {status:<8} | {branch_type:<10} | "
        #     f"{link_formatted:<35} | {start_date:<12} | {end_date:<12} | {statement_link_formatted:<35} |\n"
        # )

        # branch_list += (
        #     "| {company:<30} | {company_id:<20} | {jurisdiction:<20} | {status:<8} | "
        #     "{branch_type:<10} | {link_formatted:<35} | {start_date:<12} | {end_date:<12} | "
        #     "{statement_link_formatted:<35} |\n"
        # ).format(
        #     company=f"[[{company}]]",
        #     company_id=company_id,
        #     jurisdiction=jurisdiction,
        #     status=status,
        #     branch_type=branch_type,
        #     link_formatted=link_formatted,
        #     start_date=start_date,
        #     end_date=end_date,
        #     statement_link_formatted=statement_link_formatted
        # )

        row_template = dedent(
            """\
            | {company:<30} | {company_id:<20} | {jurisdiction:<20} | {status:<8} | {branch_type:<10} | \
            {link_formatted:<35} | {start_date:<12} | {end_date:<12} | {statement_link_formatted:<35} |
        """
        )

        branch_list += row_template.format(
            company=f"[[{company}]]",
            company_id=company_id,
            jurisdiction=jurisdiction,
            status=status,
            branch_type=branch_type,
            link_formatted=link_formatted,
            start_date=start_date,
            end_date=end_date,
            statement_link_formatted=statement_link_formatted,
        )

    logger.info(f"{i()}✅✍️👔CREATING NOTE ---- format branch table finished")
    return branch_list
