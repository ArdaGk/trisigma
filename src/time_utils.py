from datetime import datetime

def to_timestamp(rng):
    """Converts a string interval into int seconds, eg. "1m" --> 60, "2d" --> 172800
    :param rng: interval
    """
    rng = rng.lower()
    units = {'s': (['s', 'sec', 'second', 'seconds'], 1),
            'm': (['m', 'min', 'minute', 'minutes'], 60),
            'h': (['h', 'hour', 'hours'], 3600),
            'd': (['d', 'day', 'days'], 86400),
            'w': (['w', 'week', 'weeks'], 604800),
            'y': (['y', 'year', 'years'], 31536000)}
    unit = ''.join(list(filter(lambda c: c.isalpha(), rng)))
    coef = int(''.join(list(filter(lambda c: c.isnumeric(), rng))))
    for v in units.values():
        if unit in v[0]:
            result = v[1] * coef
            return result


def to_timestamp_split(rng):
    """Converts a string interval into a tuple where the 1st index represents the coefficient, and the 2nd index is the time unit represented in seconds
    eg. "1m" --> (1, 60)
        "2d" --> (2, 172800)
    :param rng: interval
    """
    rng = rng.lower()
    units = {'s': (['s', 'sec', 'second', 'seconds'], 1),
             'm': (['m', 'min', 'minute', 'minutes'], 60),
             'h': (['h', 'hour', 'hours'], 3600),
             'd': (['d', 'day', 'days'], 86400),
             'w': (['w', 'week', 'weeks'], 604800),
             'y': (['y', 'year', 'years'], 31536000)}
    unit = ''.join(list(filter(lambda c: c.isalpha(), rng)))
    coef = int(''.join(list(filter(lambda c: c.isnumeric(), rng))))
    for v in units.values():
        if unit in v[0]:
            return (coef, v[1])


def floor(date, interval, delta=None):
    """Makes a floor rounding to the given date.
    eg. date = <2022-10-28:23-53-13>, interval = "15m" --> <2022-10-28:23-45-00>
        date = <2022-10-28:23-53-13>, interval = "1d" --> <2022-10-28:00-00-00>
    :param date: the date that will be rounded.
    :type date: <datetime.datetime> or <int> (as a timestamp)
    :param interval: the interval that will be used to round the date.
    :type interval: <str>
    :param delta: (Optional) adds offset to the rounding. eg: interval="1w", delta=timedelta(days=2) will round to the last Wednesday, instead of Monday.
    :type delta: <datetime.timedelta>
    """
    if delta != None:
        delta = delta.total_seconds()
    else:
        delta = 0
    if not isinstance(date, (int, float)):
        date = date.timestamp()
    units = {'w': (604800, 345600), 'd': (86400, 0),
                'h': (3600, 0), 'm': (60, 0), 's': (1, 0)}
    freq = int(''.join([i for i in interval if i.isdigit()]))
    unit = ''.join([i for i in interval if i.isalpha()])
    coef = units[unit][0] * freq
    delt = units[unit][1] + delta

    result = (date - delt) - ((date - delt) % coef) + delt
    return datetime.fromtimestamp(int(result))


def ceil(date, interval, delta=None):
    """Makes a ceil rounding to the given date.
    eg. date = <2022-10-28:23-53-13>, interval = "15m" --> <2022-10-29:00-00-00>
        date = <2022-10-28:23-53-13>, interval = "2d" --> <2022-10-30:00-00-00>
    :param date: the date that will be rounded.
    :type date: <datetime.datetime> or <int> (as a timestamp)
    :param interval: the interval that will be used to round the date.
    :type interval: <str>
    :param delta: (Optional) adds offset to the rounding. eg: interval="1w", delta=timedelta(days=2) will round to the next Wednesday, instead of Monday.
    :type delta: <datetime.timedelta>
    """

    if delta != None:
        delta = delta.total_seconds()
    else:
        delta = 0
    if not isinstance(date, (int, float)):
        date = date.timestamp()
    units = {'w': (604800, 345600), 'd': (86400, 0),
             'h': (3600, 0), 'm': (60, 0), 's': (1, 0)}
    freq = int(''.join([i for i in interval if i.isdigit()]))
    unit = ''.join([i for i in interval if i.isalpha()])
    coef = units[unit][0] * freq
    delt = units[unit][1] + delta

    result = (date - delt) - ((date - delt) % coef) + delt + coef
    return datetime.fromtimestamp(int(result))
