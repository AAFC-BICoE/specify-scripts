"""
Searches a source directory for images from a specified csv file OR by metadata tags. If images are
found, new directory with copies of images are created in a specified path. A report of any catalog
numbers from the csv file that were not found is created. Metadata keywords are case insensitive.
"""
import os
import shutil
import csv
import argparse
import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from csvwriter import write_report

def copy_files(image_paths, destination):
    # Creates a new directory and copies images into it, returns path of new directory or False
    folder = "ImagePull[%s]" % (datetime.date.today())
    new_dir = str(destination % folder)
    try:
        os.mkdir(new_dir)
    except FileExistsError:
        return False
    for path in image_paths:
        shutil.copy(path, new_dir)
    return new_dir

def source_search(source):
    # Returns a list of each image file path in the source directory
    ext = (".JPG", ".jpg", ".JPEG", ".jpeg")
    return [os.path.join(path, f) for path, sub, files
            in os.walk(source) for f in files if f.endswith(tuple(ext))]

def md_search(image_paths, metadata, keyword):
    # Searches by keyword and metadata field entered, returns list of image paths if any found
    new_image_list = []
    for path in image_paths:
        exif = Image.open(path, "r")._getexif()
        if exif:
            data = [v for (k, v) in exif.items() if TAGS.get(k) == metadata]
            if data:
                if keyword.lower() in data[0].decode("utf-16").lower():
                    new_image_list += [path]
    return new_image_list

def csv_search(source, csv_file):
    # Reads file names from .csv file and searches source file list for matches
    try:
        csv_list = [row[0] for row in csv.reader(open(csv_file, newline=""))]
    except FileNotFoundError:
        return print("csv file not found, check file path")
    image_paths = [path for file in csv_list for path in source_search(source) if file in path]
    found_images = [os.path.basename(file) for file in image_paths]
    not_found = [[image] for image in csv_list if str(image + ".JPG") not in found_images]
    return image_paths, not_found

def csv_report(file_name, headings, data, show):
    # Creates report with passed in data, displays images to screen if specified
    if show:
        for image_name in data:
            print(image_name[0])
    write_report(file_name, headings, data)

def main():
    # Creates command line arguments, coordinates functions
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "-source", action="store", dest="source", required=True,
                        help="Source folder path where program will begin searching")
    parser.add_argument("-d", "-destination", action="store", dest="destination", required=True,
                        help="Path where new folder will be created with image copies")
    parser.add_argument("--csv", action="store", dest="csv_name",
                        help="Path of csv file containing file names, "
                             "cannot be used with --subject or --tags")
    parser.add_argument("--report", action="store_true", dest="report", default=True,
                        help="(default) creates report of file names copied")
    parser.add_argument("--show", action="store_true", dest="show",
                        help="Print filenames found to screen")
    parser.add_argument("--md", action="store", dest="metadata",
                        help="Search on metadata field entered - name specific to OS - "
                             "cannot be used with --csv, must be used with --keyword")
    parser.add_argument("--keyword", action="store", dest="keyword",
                        help="Search on the metadata field entered with keyword entered, "
                             "cannot be used with --csv, must be used with --md")
    args = parser.parse_args()
    source = args.source
    destination = args.destination + "%s"
    csv_name = args.csv_name
    report = args.report
    show = args.show
    metadata = args.metadata
    keyword = args.keyword
    image_paths = [file for file in source_search(source)]
    if os.path.exists(source) is False:
        return print("Please check source path, %s does not exist" % source)
    if os.path.exists(destination):
        return print("Please check destination path, %s does not exist" % destination)
    if report:
        if not image_paths:
            return print("No images found")
        if csv_name and (metadata or keyword):
            return print("Unable to perform metadata search while reading from csv files, "
                         "see -h for more options")
        if not (csv_name or (metadata and keyword)):
            return print("Must enter a csv file or metadata field and keyword to search by, "
                         "see -h for more options")
        if csv_name:
            image_paths, not_found = csv_search(source, csv_name)
            if not not_found:
                file_name = str(destination % ("ImagesNotFound[%s]" % (datetime.date.today())))
                csv_report(file_name, ["Image Names Not Found"], not_found, show)
                print("%s image(s) not found, report saved as %s.csv"
                      % (len(not_found), file_name))
        elif metadata:
            if keyword:
                image_paths = md_search(image_paths, metadata, keyword)
        if not image_paths:
            return print("No image(s) found, see -h for more options")
        file_path = copy_files(image_paths, destination)
        if file_path is False:
            return print("Directory %s already exists, no images copied" %
                         ("ImagePull[%s]" % (datetime.date.today())))
        return print("%s image(s) found, new folder path: %s" % (len(image_paths), file_path))
    return None

if __name__ == "__main__":
    main()
