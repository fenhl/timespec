import datetime
import re

class Relative:
    def __init__(self, spec, start):
        self.start = start
        self.spec = spec
        delta = datetime.timedelta()
        while spec:
            match = re.match('([0-9]+)([smhd])', spec)
            if not match:
                break
            delta += datetime.timedelta(**{
                {
                    's': 'seconds',
                    'm': 'minutes',
                    'h': 'hours',
                    'd': 'days'
                }[match.group(2)]: float(match.group(1))
            })
            spec = spec[len(match.group(0)):]
        if spec:
            delta = datetime.timedelta(seconds=float(spec)) # unitless suffix interpreted as seconds
        self.end = self.start + delta

    def year_predicate(self, y):
        return y == self.end.year

    def month_predicate(self, m):
        return m == self.end.month

    def day_predicate(self, d):
        return d == self.end.day

    def date_predicate(self, d):
        return True

    def hour_predicate(self, h):
        return h == self.end.hour

    def minute_predicate(self, m):
        return m == self.end.minute

    def second_predicate(self, s):
        return s == self.end.second

    def time_predicate(self, t):
        return True

    def datetime_predicate(self, dt):
        return True
