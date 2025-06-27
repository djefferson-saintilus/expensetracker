import sqlite3
import datetime

# Register adapter for datetime.date
sqlite3.register_adapter(datetime.date, lambda d: d.isoformat())

# Register adapter for datetime.datetime
sqlite3.register_adapter(datetime.datetime, lambda dt: dt.isoformat(" "))

# Register converter for date strings back to datetime.date
def convert_date(s):
    return datetime.datetime.strptime(s.decode(), "%Y-%m-%d").date()

sqlite3.register_converter("DATE", convert_date)

# Register converter for datetime strings back to datetime.datetime
def convert_datetime(s):
    return datetime.datetime.strptime(s.decode(), "%Y-%m-%d %H:%M:%S")

sqlite3.register_converter("TIMESTAMP", convert_datetime)

# When connecting, enable detect_types
conn = sqlite3.connect('expenses.db', detect_types=sqlite3.PARSE_DECLTYPES)
