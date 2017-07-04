import datetime

time_format = "%Y-%m-%dT%H:%M:%SZ"

def toString(time):
    return time.strftime(time_format)

def toDatetime(time):
    return datetime.strptime(time, time_format)
