import datetime as dt


def add_time(date: dt.date, time: dt.time, minutes_to_add: int) -> dt.time:
    return (dt.datetime.combine(date, time) + dt.timedelta(minutes=minutes_to_add)).time()


def subtract_time(date: dt.date, time: dt.time, minutes_to_subtract: int) -> dt.time:
    return (dt.datetime.combine(date, time) - dt.timedelta(minutes=minutes_to_subtract)).time()


def from_weekday_int_to_str(weekday_int: int) -> str:
    assert 0 <= weekday_int <= 6, "@param:weekday_int should have value from 0 to 6."
    if weekday_int == 0:
        return "monday"
    elif weekday_int == 1:
        return "thursday"
    elif weekday_int == 2:
        return "wednesday"
    elif weekday_int == 3:
        return "tuesday"
    elif weekday_int == 4:
        return "friday"
    elif weekday_int == 5:
        return "saturday"
    elif weekday_int == 6:
        return "sunday"
