

import datetime


def format_date(dt: datetime.datetime) -> str:
    return dt.strftime("%d/%m/%y %H:%M:%S")


def datetime_from_ts(timestamp: float) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(timestamp)


def format_timestamp(timestamp: float) -> str:
    return format_date(datetime.datetime.fromtimestamp(timestamp))
