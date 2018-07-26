"""
writes data passed in to a csv file with heading
"""
import csv

def write_report(file_name,heading,data):
    with open("%s.csv" % file_name, "w") as file_writer:
        writer = csv.writer(file_writer)
        writer.writerow(heading)
        for row in data:
            writer.writerow(row)