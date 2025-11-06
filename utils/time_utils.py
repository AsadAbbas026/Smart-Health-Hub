import datetime

def parse_time_slot_duration(time_slot):
    try:
        time_part = time_slot.split(" ")[1]
        start_str, end_str = time_part.split(" - ")
        start_time = datetime.strptime(start_str, "%H:%M")
        end_time = datetime.strptime(end_str, "%H:%M")
        duration_hours = (end_time - start_time).total_seconds() / 3600
        return duration_hours if duration_hours > 0 else 1.0
    except (ValueError, IndexError):
        return 1.0