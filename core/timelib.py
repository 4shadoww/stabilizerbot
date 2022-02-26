import datetime

time_format = "%Y-%m-%dT%H:%M:%SZ"

def to_string(time):
    return time.strftime(time_format)

def to_datetime(time):
    return datetime.datetime.strptime(time, time_format)
