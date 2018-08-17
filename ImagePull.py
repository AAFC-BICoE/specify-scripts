"""
Using command line arguments, searches a source directory for images from a specified csv file, or by metadata tags.
Once images are found, they are copied to a new directory in a specified path. If searching from a csv, report of any
catalog numbers that were not found is created. File name search is done by looking at the integers in the file name
only, so 123_A.JPG and 123_B.JPG will be selected by searching for just 123.JPG. Metadata tags are case insensitive.
***Some operating systems name metadata tags differently, under function 'metadata_search', the dictionary
'system_names" may need to have its VALUES changed to what the particular OS calls the fields 'subject' and 'tags'.
Currently supports naming for ubuntu 14.04 metadata tag ***
"""
import os, shutil, csv, argparse, datetime
from PIL import Image
from PIL.ExifTags import TAGS
from csvwriter import write_report

# returns an int that contains only numbers that are found in the file name that is passed in, or None if no ints found
def configure(catalog_number):
    try:
        return int("".join([n for n in catalog_number if n.isdigit()]))
    except ValueError:
        return None

# if show is specified, prints images found to screen with .JPG ending
def display(found_images):
    for image_name in found_images:
        print(str(image_name) + ".JPG")

# creates a csv report of files names from the csv file that were not found
def files_not_found(not_found,destination):
    file_name = "ImagesNotFound[%s]" % (datetime.date.today())
    new_file = str(destination % file_name)
    heading= ["Image Names Not Found"]
    write_report(new_file,heading,not_found)
    print("%s image(s) not found, report saved as %s.csv" % (len(not_found), file_name))

# creates a new directory and copies images into it with date stamp in directory name
def copy_files(image_paths,destination):
    folder = "ImagePull[%s]" % (datetime.date.today())
    new_dir = str(destination % folder)
    try:
        os.mkdir(new_dir)
    except FileExistsError:
        print("Directory %s already exists, no images copied" % folder)
        return False
    [shutil.copy(path, new_dir) for path in image_paths]
    print("%s image(s) found, new folder path: %s" % (len(image_paths), new_dir))

# returns a list of each .JPG file path in the source directory
def source_search(source):
    return [os.path.join(path, f) for path, sub, files in os.walk(source) for f in files if (f.endswith(".JPG"))]

# searches 'subject' and 'tags' metadata fields, returns image paths if keywords are found in fields
def multi_md_search(image_paths,field1,field2,keyword1,keyword2):
    image_list = []
    metadata_dict = {}
    for path in image_paths:
        exif = Image.open(path, "r")._getexif()
        if exif:
            for k,v in exif.items():
                metadata_dict[TAGS.get(k)] = v
            if (field1 in metadata_dict) and (field2 in metadata_dict):
                if (keyword1.lower() in metadata_dict[field1].decode("utf-16").lower()) \
                        and (keyword2.lower() in metadata_dict[field2].decode("utf-16").lower()):
                    image_list += [path]
    return image_list

# searches for single metadata field, returns list of image paths if keyword is found in field
def single_md_search(image_paths,field,keyword):
    new_image_list = []
    for path in image_paths:
        exif = Image.open(path, "r")._getexif()
        if exif:
            meta_data = [v for (k, v) in exif.items() if TAGS.get(k) == field]
            if meta_data:
                if keyword.lower() in meta_data[0].decode("utf-16").lower():
                    new_image_list += [path]
    return new_image_list

# reads file names from .csv file and searches source file list for matches, creates csv of catalog numbers not found
def csv_search(source,destination,csv_file):
    try:
        csv_list = [row[0] for row in csv.reader(open(csv_file, newline=""))]
    except FileNotFoundError:
        return print("csv file not found, check file path")
    from_csv = [configure(catalog_number) for catalog_number in csv_list]
    image_paths = [file for file in source_search(source) if configure(os.path.basename(file)) in from_csv]
    found_images = [configure(os.path.basename(file)) for file in image_paths]
    not_found = [[image] for image in csv_list if configure(image) not in found_images]
    if len(not_found) != 0:
       files_not_found(not_found,destination)
    return image_paths

# creates command line arguments, coordinates other functions depending on what arguments are called
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s","-source",action="store", dest= "source",required=True,
                        help="Source folder path where program will begin searching")
    parser.add_argument("-d","-destination",action="store",dest="destination",required=True,
                        help="Path where new folder will be created with image copies")
    parser.add_argument("--csv", action="store", dest="csv_name",
                        help="Path of csv file containing file names, cannot be used with --subject or --tags")
    parser.add_argument("--report", action="store_true",default=True,dest="report",
                        help="(default) creates report of file names copied")
    parser.add_argument("--show", action="store_true", dest="show", help="Print filenames found to screen")
    parser.add_argument("--subject", action="store", dest="subject",
                        help= "Search on the metadata field 'Subject' with keyword entered, cannot be used with --csv")
    parser.add_argument("--tags",action="store",dest="tags",
                        help="Search on the metadata field 'Tags' with keyword entered, cannot be used with --csv")
    args = parser.parse_args()
    source = args.source
    destination = args.destination + "%s"
    csv_name= args.csv_name
    report = args.report
    show = args.show
    subject = args.subject
    tags= args.tags
    system_names = {"subject": "XPSubject","tags": "XPKeywords"}  ## VALUES MAY NEED TO BE CHANGED FOR DIFFERENT OPERATING SYSTEMS
    image_paths = [file for file in source_search(source)]
    if os.path.exists(source) is False:
        return print("Please check source path, %s does not exist" % source)
    if os.path.exists(destination):
        return print("Please check destination path, %s does not exist" % destination)
    if report:
        if not image_paths:
            return print("No images found")
        if csv_name and (subject or tags):
            return print("Unable to perform metadata search while reading from csv files, see -h for more options")
        elif not (csv_name or subject or tags):
            return print("Must enter at least one argument, see -h for more options")
        elif csv_name:
            image_paths = csv_search(source, destination, csv_name)
        elif subject and tags:
            image_paths = multi_md_search(image_paths, system_names["subject"], system_names["tags"], subject, tags)
        elif subject and not tags:
            image_paths = single_md_search(image_paths, system_names["subject"], subject)
        elif tags and not subject:
            image_paths = single_md_search(image_paths, system_names["tags"], tags)
        if len(image_paths) == 0:
            return print("No image(s) found, see -h for more options")
        found_images = [configure(os.path.basename(file)) for file in image_paths]
        if show:
            display(found_images)
        copy_files(image_paths, destination)

if __name__ == "__main__":
    main()
