from services.applogging import logger
from settings.settings import i


def render_links(links):
    """
    Formats a list of links into a Markdown table for display in a note.

    Args:
        links (List[str]): A list of links to be formatted.

    Returns:
        str: A Markdown table representing the links.

    Example:
        >>> format_links(["https://example.com", "https://github.com"])
        '| Link | URL |\n|------|------|\n| [Link](https://example.com) | Link |\n| [Link](https://github.com) | Link |\n'

    Note:
        This function logs the start and end of the link table formatting process using the `logger` module.
    """

    logger.info(f"{i()}✍️🔗CREATING NOTE ---- format link table started")
    if not links:
        logger.info(f"{i()}❌✍️🔗CREATING NOTE ---- Empty link")
        return ""
    link_list = f"| Link   | {'url':<30} \n|{'':-<8}|{'':-<32}|\n"
    for link in links:
        link_list += f"| [Link]({link}) |{link:<30}|\n"
    logger.info(f"{i()}✅✍️🔗CREATING NOTE ---- format link table finished")
    return link_list
