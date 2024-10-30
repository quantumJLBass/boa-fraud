def render_link(entity_key, display_name=None, tabled=False):
    """
    Creates a Markdown link with the given `file_name` and optional `display_name`.

    Args:
        file_name (str): The name of the file to link to.
        display_name (Optional[str]): The name to display for the link. If not provided, the `file_name` will be used.
        tabled (bool, optional): Whether to use the `|` separator for the link with a delimiter between the `file_name` and `display_name` because the link is in a table. Defaults to False.

    Returns:
        str: The Markdown link with the `file_name` and `display_name`. If `display_name` is not provided or is the same as `file_name`, the link will only contain the `file_name`.

    Example:
        >>> create_link('example.md', 'Example File', True)
        '[[example.md \ |Example File]]'

        >>> create_link('example.md', 'Example File')
        '[[example.md|Example File]]'

        >>> create_link('example.md')
        '[[example.md]]'
    """
    separator = "|"
    if tabled:
        separator = "\|"
    if display_name and display_name != entity_key:
        return f"[[{entity_key}{separator}{display_name}]]"
    else:
        return f"[[{entity_key}]]"
