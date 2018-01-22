import datetime

class Relative:
    def __init__(self, spec, start):
        self.start = start
        self.spec = spec
        if self.spec.endswith('s'):
            self.delta = datetime.timedelta(seconds=float(self.spec[:-1]))
        elif self.spec.endswith('m'):
            self.delta = datetime.timedelta(minutes=float(self.spec[:-1]))
        elif self.spec.endswith('h'):
            self.delta = datetime.timedelta(hours=float(self.spec[:-1]))
        elif self.spec.endswith('d'):
            self.delta = datetime.timedelta(days=float(self.spec[:-1]))
        else:
            self.delta = datetime.timedelta(seconds=float(self.spec))
        self.end = self.start + self.delta

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
