from services.applogging import logger
from settings.settings import i


def render_events(events) -> str:
    """
    Formats a list of events into a Markdown table for display in a note.

    Args:
        events (List[Dict[str, str]]): A list of dictionaries representing events. Each dictionary should have the following keys:
            - Description (str): The description of the event.
            - Link (str, optional): The link to the event (default is '#').

    Returns:
        str: A Markdown table representing the events. The table has the following format:
            ## Events for
            | Start Date | End Date | Event | Link |
            |------------|----------|-------|------|
            | start_date1 | end_date1 | event_description1 | [Link](event_link1) |
            | start_date2 | end_date2 | event_description2 | [Link](event_link2) |
            ...

    Example:
        >>> format_events([
        ...     {'Description': 'Between 2010-01-11 and 2018-09-19: Addition of officer [[HEITZ, KELLY N|KELLY NICHOLAS HEITZ]], agent', 'Link': 'https://opencorporates.com/events/346987079'},
        ...     {'Description': '2010-01-11: Incorporated', 'Link': 'https://opencorporates.com/events/346987091'}
        ... ])
        '## Events for\n| Start Date | End Date | Event | Link |\n|------------|----------|-------|------|\n| 2010-01-11 | 2018-09-19 | Addition of officer [[HEITZ, KELLY N|KELLY NICHOLAS HEITZ]], agent | [Link](https://opencorporates.com/events/346987079) |\n| 2010-01-11 |  | Incorporated | [Link](https://opencorporates.com/events/346987091) |\n'
    """

    logger.info(f"{i()}✍️📆CREATING NOTE ---- format event table started")
    if not events:
        logger.info(f"{i()}❌✍️📆CREATING NOTE ---- Empty Events")
        return ""
    # l = max(len(e['Description']) for e in events)
    event_list = f"\n| {'Start Date':<10} | {'End Date':<10} | {'Event':<55} | Link |\n|{'':-<12}|{'':-<12}|{'':-<55}|------|\n"

    for event in events:
        description = event.get("Description", "")
        link = event.get("Link", "#")
        # Date = event.get('Date', '#')
        dates = "2024-08-08"  # extract_dates(Date)

        if len(dates) > 1:
            start_date, end_date = sorted(dates)[:2]
        elif len(dates) == 1:
            start_date, end_date = dates[0], ""
        else:
            start_date, end_date = "", ""

        event_list += f"| {start_date:<10} | {end_date:<10} | {description:<55} | [Link]({link}) |\n"

    logger.info(f"{i()}✅✍️📆CREATING NOTE ---- format event table finished")
    return event_list
