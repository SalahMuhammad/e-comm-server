
def audit_info_dateformatter(obj):
    diff = obj.last_updated_at - obj.created_at
    total_seconds = int(diff.total_seconds())

    # Break into components
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    # Build the string based on conditions
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")

    time_diff = f"{' '.join(parts)}"

    return {
        'created_at': obj.created_at.strftime('%Y.%m.%d %H:%M:%S'),
        'created_by': obj.created_by.username,
        'last_updated_at': obj.last_updated_at.strftime('%Y.%m.%d %H:%M:%S'),
        'last_updated_by': obj.last_updated_by.username,
        'time_diff': time_diff
    }
