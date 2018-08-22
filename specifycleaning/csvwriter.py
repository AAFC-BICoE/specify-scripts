""" Creates a csv file with specified data. Compatible with Linux and Windows"""
import csv
import sys

def write_report(file_name, heading, data):
    if sys.version_info >= (3, 0, 0):
        # Writes the data to a file if a Linux OS is detected
        with open("%s.csv" % file_name, "w", newline="") as file_writer:
            writer = csv.writer(file_writer)
            writer.writerow(heading)
            for row in data:
                writer.writerow(row)
    else:
        # Writes the data to a file if a Windows OS is detected
        with open("%s.csv" % file_name, "wb") as file_writer:
            writer = csv.writer(file_writer)
            writer.writerow(heading)
            for row in data:
                writer.writerow(row)
