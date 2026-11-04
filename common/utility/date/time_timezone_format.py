from datetime import datetime, timezone, timedelta


def get_formatted_time(offset: timedelta = timedelta(hours=3)) -> str:
    """
    Get the current time in a specified timezone offset, formatted as 
    YYYY-MM-DD HH:MM:SS.ffffff+HH (with trailing zeros removed from the offset).
    """
    tz = timezone(offset)
    formatted_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S.%f%z")
    
    # Adjust timezone format from '+0300' to '+03'
    if formatted_time.endswith("00"):
        formatted_time = formatted_time[:-2]
        
    return formatted_time

# # --- Example Usage ---

# # 1. Using the default offset (+03:00)
# print(get_formatted_time())

# # 2. Using a custom offset (e.g., -05:00)
# print(get_formatted_time(timedelta(hours=-5)))

# # 3. Using an offset with minutes (e.g., +05:30)
# print(get_formatted_time(timedelta(hours=5, minutes=30)))
