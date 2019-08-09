import contextlib
import datetime
import pytz
import re

import timespec.relative

__version__ = '1.4.0'

WEEKDAYS = [
    'mon',
    'tue',
    'wed',
    'thu',
    'fri',
    'sat',
    'sun'
]

def combine_dates_and_times(dates, times, tz=pytz.utc):
    for date in dates:
        for time in times:
            with contextlib.suppress(pytz.exceptions.NonExistentTimeError):
                yield tz.localize(datetime.datetime.combine(date, time), is_dst=None)

def date_range(start, end):
    if end < start:
        date = start
        while date > end:
            yield date
            date -= datetime.timedelta(days=1)
    else:
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

def now(tz=pytz.utc):
    return pytz.utc.localize(datetime.datetime.utcnow()).astimezone(tz)

def parse(spec, *, candidates=None, plugins={'r': timespec.relative.Relative}, reverse=False, start=None, tz=pytz.utc):
    if candidates is not None:
        candidates = sorted((candidate if is_aware(candidate) else tz.localize(candidate) for candidate in candidates), reverse=reverse)
        if len(candidates) == 0:
            raise ValueError('Empty candidates list')
    if candidates is None:
        if start is None:
            start = now(tz)
        end = start.replace(year=start.year - 10 if reverse else start.year + 10, day=28 if start.month == 2 and start.day == 29 else start.day)
    else:
        start = candidates[0]
        end = candidates[-1]
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
        match = re.fullmatch('([a-z]+):(.*)', predicate_str)
        if match:
            plugin = plugins[match.group(1)](match.group(2), start)
            year_predicates.append(plugin.year_predicate)
            month_predicates.append(plugin.month_predicate)
            day_predicates.append(plugin.day_predicate)
            date_predicates.append(plugin.date_predicate)
            hour_predicates.append(plugin.hour_predicate)
            minute_predicates.append(plugin.minute_predicate)
            second_predicates.append(plugin.second_predicate)
            time_predicates.append(plugin.time_predicate)
            datetime_predicates.append(plugin.datetime_predicate)
            continue
        try:
            date = parse_iso_date(predicate_str)
        except ValueError:
            pass # not a date
        else:
            if reverse:
                if date > start.date():
                    raise ValueError('Specified date is in the future')
            else:
                if date < start.date():
                    raise ValueError('Specified date is in the past')
            year_predicates.append(lambda y: y == date.year)
            month_predicates.append(lambda m: m == date.month)
            day_predicates.append(lambda d: d == date.day)
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
                time_predicates.append(equals_predicate(timestamp.time()))
                datetime_predicates.append(equals_predicate(timestamp))
            continue
        raise ValueError('Unknown timespec: {!r}'.format(predicate_str))
    optimized_date = candidates is None and tz == pytz.utc and all(len(pred_list) == 0 for pred_list in [year_predicates, month_predicates, day_predicates, date_predicates, datetime_predicates])
    optimized_daytime = candidates is None and tz == pytz.utc and all(len(pred_list) == 0 for pred_list in [hour_predicates, minute_predicates, second_predicates, time_predicates, datetime_predicates])
    if optimized_date and optimized_daytime:
        # no predicates and no candidates matches the start time
        assert is_aware(start)
        return start
    if optimized_date:
        # optimization: if predicates are daytime only and timezone is UTC, result must be within one day of start
        if reverse:
            dates = [start.date(), start.date() - datetime.timedelta(days=1)]
        else:
            dates = [start.date(), start.date() + datetime.timedelta(days=1)]
    else:
        if reverse:
            years = predicate_list(year_predicates, range(start.year, end.year - 1, -1))
        else:
            years = predicate_list(year_predicates, range(start.year, end.year + 1))
        months = predicate_list(month_predicates, range(1, 13))
        days = predicate_list(day_predicates, range(1, 32))
        if len(year_predicates) > 0 or len(month_predicates) > 0 or len(day_predicates) > 0:
            date_predicates += [
                lambda date: date.year in years,
                lambda date: date.month in months,
                lambda date: date.day in days
            ]
        if reverse:
            dates = date_range(start.date(), end.date() - datetime.timedelta(days=1))
        else:
            dates = date_range(start.date(), end.date() + datetime.timedelta(days=1))
    dates = predicate_list(date_predicates, dates)
    if optimized_daytime:
        # optimization: if predicates are date only and timezone is UTC, result must be the current time or start/end of day
        if reverse:
            times = [start.time().replace(microsecond=0), datetime.time(23, 59, 59)]
        else:
            times = [datetime.time(), start.time().replace(microsecond=0)]
    else:
        hours = predicate_list(hour_predicates, range(24))
        minutes = predicate_list(minute_predicates, range(60))
        seconds = predicate_list(second_predicates, range(60))
        if len(hour_predicates) > 0 or len(minute_predicates) > 0 or len(second_predicates) > 0:
            time_predicates += [
                lambda time: time.hour in hours,
                lambda time: time.minute in minutes,
                lambda time: time.second in seconds
            ]
        times = time_range(reverse=reverse)
    times = predicate_list(time_predicates, times)
    datetime_predicates += [
        lambda date_time: date_time.date() in dates,
        lambda date_time: date_time.time() in times
    ]
    if reverse:
        datetime_predicates.append(lambda date_time: date_time <= start)
    else:
        datetime_predicates.append(lambda date_time: date_time >= start)
    result = next(resolve_predicates(datetime_predicates, combine_dates_and_times(dates, times, tz) if candidates is None else candidates))
    assert is_aware(result)
    return result

def parse_iso_date(date_str):
    parts = date_str.split('-')
    if len(parts) != 3:
        raise ValueError('Failed to parse date from {!r} (format should be YYYY-MM-DD)'.format(date_str))
    return datetime.date(*map(int, parts))

def predicate_list(predicates, values):
    result = list(resolve_predicates(predicates, values))
    if len(result) == 0:
        raise ValueError('No matching datetime found')
    return result

def resolve_predicates(predicates, values):
    for val in values:
        if all(predicate(val) for predicate in predicates):
            yield val

def time_range(*, reverse=False):
    if reverse:
        for hour in range(23, -1, -1):
            for minute in range(59, -1, -1):
                for second in range(59, -1, -1):
                    yield datetime.time(hour, minute, second)
    else:
        for hour in range(24):
            for minute in range(60):
                for second in range(60):
                    yield datetime.time(hour, minute, second)

def weekday_predicate(weekday):
    return lambda date: date.weekday() == weekday
