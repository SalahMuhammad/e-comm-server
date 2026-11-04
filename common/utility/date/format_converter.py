from datetime import datetime



input_format_options = {
    1: {"from": "%B %d, %Y", "to": "%Y-%m-%d"},
    2: {"from": "%Y-%m-%d", "to": "%B %d, %Y"},
    3: {"from": "%m/%d/%Y", "to": "%Y-%m-%d"},
    4: {"from": "%d/%m/%Y", "to": "%Y-%m-%d"},
    5: {"from": "%Y/%m/%d", "to": "%Y-%m-%d"},
    6: {"from": "%b %d, %Y", "to": "%Y-%m-%d"},
    7: {"from": "%d %B %Y", "to": "%Y-%m-%d"},
    8: {"from": "%d-%m-%Y", "to": "%Y-%m-%d"},
    9: {"from": "%m-%d-%Y", "to": "%Y-%m-%d"},
    10: {"from": "%Y%m%d", "to": "%Y-%m-%d"},
    11: {"from": "%A, %B %d, %Y", "to": "%Y-%m-%d"},
}

def date_format_converter(
    date_string="November 2, 2026",
    format_option=1,
):
    """Convert a date string using a numbered format from input_format_options.

    Available input format options (option number: format) are:
    1: ``%B %d, %Y``; 2: ``%Y-%m-%d``; 3: ``%m/%d/%Y``;
    4: ``%d/%m/%Y``; 5: ``%Y/%m/%d``; 6: ``%b %d, %Y``;
    7: ``%d %B %Y``; 8: ``%d-%m-%Y``; 9: ``%m-%d-%Y``;
    10: ``%Y%m%d``; 11: ``%A, %B %d, %Y``.

    """
    formats = input_format_options[format_option]
    parsed_date = datetime.strptime(date_string, formats["from"])
    return parsed_date.strftime(formats["to"])
