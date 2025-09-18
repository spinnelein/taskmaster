# Test date comparison issue
from datetime import datetime, date

# Test what types we're dealing with
occurrence_date = datetime(2025, 9, 15).date()
exception_date = date(2025, 9, 15)

print(f"occurrence_date type: {type(occurrence_date)}, value: {occurrence_date}")
print(f"exception_date type: {type(exception_date)}, value: {exception_date}")
print(f"Are they equal? {occurrence_date == exception_date}")
print(f"Hash equal? {hash(occurrence_date) == hash(exception_date)}")

# Test dict lookup
test_dict = {exception_date: "found"}
print(f"Dict lookup works? {test_dict.get(occurrence_date)}")

# Test with string dates
str_date = "2025-09-15"
test_dict2 = {str_date: "found"}
print(f"String dict lookup works? {test_dict2.get(str_date)}")