from datetime import datetime

def to_timestamp(range):
    range = range.lower()
    units = {'s': (['s', 'sec', 'second', 'seconds'], 1),
            'm': (['m', 'min', 'minute', 'minutes'], 60),
            'h': (['h', 'hour', 'hours'], 3600),
            'd': (['d', 'day', 'days'], 86400),
            'w': (['w', 'week', 'weeks'], 604800),
            'y': (['y', 'year', 'years'], 31536000)}
    unit = ''.join(list(filter(lambda c: c.isalpha(), range)))
    coef = int(''.join(list(filter(lambda c: c.isnumeric(), range))))
    for v in units.values():
        if unit in v[0]:
            result = v[1] * coef
            return result


def to_timestamp_split(range):
    range = range.lower()
    units = {'s': (['s', 'sec', 'second', 'seconds'], 1),
             'm': (['m', 'min', 'minute', 'minutes'], 60),
             'h': (['h', 'hour', 'hours'], 3600),
             'd': (['d', 'day', 'days'], 86400),
             'w': (['w', 'week', 'weeks'], 604800),
             'y': (['y', 'year', 'years'], 31536000)}
    unit = ''.join(list(filter(lambda c: c.isalpha(), range)))
    coef = int(''.join(list(filter(lambda c: c.isnumeric(), range))))
    for v in units.values():
        if unit in v[0]:
            return (coef, v[1])


def floor(date, interval, delta=None):
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
