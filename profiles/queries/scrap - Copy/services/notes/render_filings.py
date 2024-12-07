from services.applogging import logger
from settings.settings import i


def render_filings(filings):
    """
    Generates a formatted table for filings including the date, description, and an optional link.

    This function takes a list of filing dictionaries as input and generates a formatted table with the following columns:
    - Date: The date of the filing.
    - Description: The description of the filing.

    If the input list is empty or None, an empty string is returned.

    Parameters:
    ----------
    filings (list): A list of dictionaries containing filing information. Each dictionary should have the following keys:
        - Date (str): The date of the filing.
        - Description (str): The description of the filing.
        - Link (str, optional): The link to the filing (default is '#').

    Returns:
    -------
    str: A formatted table representing the filings. The table has the following format:
        | Date | Description | Link |
        |------|-------------|------|
        | filing_date1 | filing_description1 | [Link](filing_link1) |
        | filing_date2 | filing_description2 | [Link](filing_link2) |
        ...

    Example:
        >>> filings = [
        ...     {'Date': '2022-01-01', 'Description': 'Annual Report', 'Link': 'https://example.com/filing1'},
        ...     {'Date': '2022-02-01', 'Description': 'Quarterly Report', 'Link': 'https://example.com/filing2'},
        ... ]
        >>> format_filings(filings)
        '| Date | Description | Link |\n|------|-------------|------|\n| 2022-01-01 | Annual Report | [Link](https://example.com/filing1) |\n| 2022-02-01 | Quarterly Report | [Link](https://example.com/filing2) |\n'
    """
    logger.info(f"{i()}✍️📑CREATING NOTE ---- format filings table started")
    if not filings:
        logger.info(f"{i()}❌✍️📑CREATING NOTE ---- Empty filings")
        return ""
    filing_list = f"| {'Date':<11} | {'Description':<30} | Link |\n|{'':-<13}|{'':-<32}|-------|\n"
    for filing in filings:
        filing_list += f"| {filing['Date']:<11} | {filing['Description']:<30} | [Link]({filing.get('Link', '#')}) |\n"
    logger.info(f"{i()}✅✍️📑CREATING NOTE ---- format filings table finished")
    return filing_list
