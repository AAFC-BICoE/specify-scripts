"""
writes data passed in to a csv file with heading, compatible with linux and windows
"""
import csv, sys

def write_report(file_name,heading,data):
    if sys.version_info >= (3, 0, 0):
        with open("%s.csv" % file_name, "w", newline="") as file_writer:
            writer = csv.writer(file_writer)
            writer.writerow(heading)
            for row in data:
                writer.writerow(row)
    else:
        with open("%s.csv" % file_name, "wb") as file_writer:
            writer = csv.writer(file_writer)
            writer.writerow(heading)
            for row in data:
                writer.writerow(row)



