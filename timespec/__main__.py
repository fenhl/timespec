#!/usr/bin/env python3

"""Parse a timespec (https://github.com/fenhl/timespec).

Usage:
  timespec [options] [<predicate>...]
  timespec -h | --help
  timespec --version

Options:
  -f, --format=<format>      Print the date in the given format. [Default: %Y-%m-%d %H:%M:%S]
  -h, --help                 Print this message and exit.
  -r, --reverse              Use reverse direction instead of chronological.
  -s, --start=<datetime>     Use this datetime, given in --format, as the start time. Defaults to the current datetime.
  -z, --timezone=<timezone>  Use this timezone from the Olson timezone database. Defaults to UTC.
  --version                  Print version info and exit.
"""

import sys

sys.path.append('/opt/py')

import datetime
import docopt
import pytz
import timespec

__version__ = timespec.__version__

if __name__ == '__main__':
    arguments = docopt.docopt(__doc__, version='timespec {}'.format(__version__))
    if arguments['--timezone']:
        tz = pytz.timezone(arguments['--timezone'])
    else:
        tz = pytz.utc
    if arguments['--start']:
        start = tz.localize(datetime.datetime.strptime(arguments['--start'], arguments['--format']))
    else:
        start = datetime.datetime.now(datetime.timezone.utc).astimezone(tz)
    result = timespec.parse(arguments['<predicate>'], reverse=arguments['--reverse'], start=start, tz=tz) #TODO read candidates from stdin
    print(format(result, arguments['--format']))
