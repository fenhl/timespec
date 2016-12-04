import sys

import contextlib
import datetime
import pytz

__version__ = '1.1.2'

WEEKDAYS = [
    'mon',
    'tue',
    'wed',
    'thu',
    'fri',
    'sat',
    'sun'
]

def date_range(start, end):
    date = start
    while date < end:
        yield date
        date += datetime.timedelta(days=1)

def equals_predicate(value):
    return lambda v: v == value

def is_aware(datetime_or_time):
    if isinstance(datetime_or_time, datetime.datetime):
        return datetime_or_time.tzinfo is not None and datetime_or_time.tzinfo.utcoffset(datetime_or_time) is not None
    elif isinstance(datetime_or_time, datetime.time):
        return datetime_or_time.tzinfo is not None and datetime_or_time.tzinfo.utcoffset(None) is not None
    else:
        raise TypeError('Can only test datetime or time objects for awareness')

def modulus_predicate(modulus):
    return lambda v: v % modulus == 0

def parse(spec, *, start=None, tz=pytz.utc):
    if start is None:
        start = datetime.datetime.now(tz)
    year_predicates = []
    month_predicates = []
    day_predicates = []
    date_predicates = []
    hour_predicates = []
    minute_predicates = []
    second_predicates = []
    time_predicates = []
    datetime_predicates = []
    for predicate_str in spec:
        with contextlib.suppress(ValueError):
            end_date = parse_iso_date(predicate_str)
            if end_date < start.date():
                sys.exit('[!!!!] specified date is in the past')
            year_predicates.append(lambda y: y == end_date.year)
            month_predicates.append(lambda m: m == end_date.month)
            day_predicates.append(lambda d: d == end_date.day)
            continue
        if ':' in predicate_str:
            if len(predicate_str.split(':')) == 3:
                hours, minutes, seconds = ((None if time_unit == '' else int(time_unit)) for time_unit in predicate_str.split(':'))
                if hours is not None:
                    hour_predicates.append(equals_predicate(hours))
                if minutes is not None:
                    minute_predicates.append(equals_predicate(minutes))
                if seconds is not None:
                    second_predicates.append(equals_predicate(seconds))
            else:
                hours, minutes = ((None if time_unit == '' else int(time_unit)) for time_unit in predicate_str.split(':'))
                if hours is not None:
                    hour_predicates.append(equals_predicate(hours))
                if minutes is not None:
                    minute_predicates.append(equals_predicate(minutes))
            continue
        if predicate_str.lower() in WEEKDAYS:
            date_predicates.append(weekday_predicate(WEEKDAYS.index(predicate_str.lower())))
            continue
        if predicate_str.endswith('s'):
            second_predicates.append(modulus_predicate(int(predicate_str[:-1])))
            continue
        if predicate_str.endswith('m'):
            minute_predicates.append(modulus_predicate(int(predicate_str[:-1])))
            continue
        if predicate_str.endswith('h'):
            hour_predicates.append(modulus_predicate(int(predicate_str[:-1])))
            continue
        if predicate_str.endswith('d'):
            day_predicates.append(modulus_predicate(int(predicate_str[:-1])))
            continue
        with contextlib.suppress(ValueError):
            predicate_int = int(predicate_str)
            if 1000000000 <= predicate_int:
                timestamp = datetime.datetime.fromtimestamp(predicate_int, tz)
                date_predicates.append(equals_predicate(timestamp.date()))
                time_predicates.append(equals_predicate(timestamp.timetz()))
                datetime_predicates.append(equals_predicate(timestamp))
            continue
        sys.exit('[!!!!] unknown timespec')
    years = predicate_list(year_predicates, range(start.year, start.year + 100))
    months = predicate_list(month_predicates, range(1, 13))
    days = predicate_list(day_predicates, range(1, 32))
    if len(year_predicates) > 0 or len(month_predicates) > 0 or len(day_predicates) > 0:
        date_predicates += [
            lambda date: date.year in years,
            lambda date: date.month in months,
            lambda date: date.day in days
        ]
    dates = predicate_list(date_predicates, date_range(start.date(), start.date().replace(year=start.year + 10)))
    hours = predicate_list(hour_predicates, range(24))
    minutes = predicate_list(minute_predicates, range(60))
    seconds = predicate_list(second_predicates, range(60))
    if len(hour_predicates) > 0 or len(minute_predicates) > 0 or len(second_predicates) > 0:
        time_predicates += [
            lambda time: time.hour in hours,
            lambda time: time.minute in minutes,
            lambda time: time.second in seconds
        ]
    times = predicate_list(time_predicates, time_range(tz))
    datetime_predicates += [
        lambda date_time: date_time > start,
        lambda date_time: date_time.date() in dates,
        lambda date_time: date_time.timetz() in times
    ]
    end_date = next(resolve_predicates(datetime_predicates, (datetime.datetime.combine(date, time) for date in dates for time in times)))
    assert is_aware(end_date)
    return end_date

def parse_iso_date(date_str):
    parts = date_str.split('-')
    if len(parts) != 3:
        raise ValueError('Failed to parse date from {!r} (format should be YYYY-MM-DD)'.format(date_str))
    return datetime.date(*map(int, parts))

def predicate_list(predicates, values):
    result = list(resolve_predicates(predicates, values))
    if len(result) == 0:
        sys.exit('[!!!!] no matching datetime found')
    return result

def resolve_predicates(predicates, values):
    for val in values:
        if all(predicate(val) for predicate in predicates):
            yield val

def time_range(tz=datetime.timezone.utc):
    for hour in range(24):
        for minute in range(60):
            for second in range(60):
                yield datetime.time(hour, minute, second, tzinfo=tz)

def weekday_predicate(weekday):
    return lambda date: date.weekday() == weekday
