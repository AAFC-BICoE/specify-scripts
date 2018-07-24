"""
Redmine Support #12000
Using the library 'tkinter', creates a UI that allows a user to select .JPG files in the OS based on operations relating
to the filename (catalogNumber) OR enter the path of a CSV file and select images based on the catalog numbers in the
CSV file. Once the image has been found, creates a new directory of copies of the images that were found using the
library shutil.
NOTE: Some configurations must be done before script will work properly:
1. source path and new_folder_path must be specified first. Source path is the directory containing the images that will
    be searched on, new_folder_path is the path where the new folder containing the copies of the images will be created.
    Note the new_folder_path cannot be in the source path.
2. Script searches for .JPG files ONLY- if .jpeg or any other formats are the target of search, this must be changed.
3. Meta data may be named differently for every operating system, keys 'Subject' and 'Tags' should be updated in the
    md_dict with your os naming system - use the following to display metadata for an image in the file path 'file_name'
    >>print(Image.open(file_name,"r")._getexif())
"""
import os
import shutil
from tkinter import *
from tkinter import messagebox, filedialog
import tkinter as tk
from tkinter.simpledialog import askstring
from operator import eq, ge, le, lt, gt
from PIL import Image
from PIL.ExifTags import TAGS
import csv

# returns an int that contains only the numbers that are found in the file name that is passed in or None
def configure(cat_num):
    if cat_num:
        try:
            return int("".join([n for n in cat_num if n.isdigit()]))
        except ValueError:
            return None
    return None

# coordinates search function passing in appropriate info and operator expressions according to the drop selections
def create_image_list(r1, r2, md,source,md_dict,op_dict,md_drop,op_drop):
    if r2:
        if r1:
            if md:
                return md_search(range_file_search(r1, r2,source), md,md_dict,md_drop)
            return range_file_search(r1, r2,source)
        if md:
            return md_search(single_file_search(r2, op_dict[op_drop],source), md,md_dict,md_drop)
        return single_file_search(r2, op_dict[op_drop],source)
    if md:
        return md_search(source_search(source), md,md_dict,md_drop)
    return None

# builds dict of metadata from files passed in, searches dict and returns list of files that contain the specified MD
def md_search(files, md,md_dict,md_drop):
    file_list = []
    for file_name in files:
        exif = Image.open(file_name, "r")._getexif()
        if exif:
            meta_data = [v for (k, v) in exif.items() if TAGS.get(k) == md_dict[md_drop]]
            if meta_data:
                if md.lower() in meta_data[0].decode("utf-16").lower():
                    file_list += [file_name]
    return file_list

# returns a list of paths for each .JPG file in the source directory
def source_search(source):
    return [os.path.join(path, f) for path, sub, files in os.walk(source) for f in files if (f.endswith(".JPG"))]

# searches source directory list for file names contained by the operator passed in for the single file name entered
def single_file_search(image, op,source):
    return [file for file in source_search(source) if op(configure(os.path.basename(file)), int(image))]

# searches source list for file names in range of file names entered
def range_file_search(image1, image2,source):
    return [file for file in source_search(source) if
            ge(configure(os.path.basename(file)), int(image1)) and le(configure(os.path.basename(file)), int(image2))]

# reads file names from .csv file and searches source file list for matches
def csv_search(window,source,new_folder_path,range1,range2,meta,options1,options2,md_dict,op_dict):
    window.filename = filedialog.askopenfilename(initialdir="/", title="Select .csv file",
                                                 filetypes=(("csv files", "*.csv"), ("all files", "*.*")))
    csv_file = window.filename
    if csv_file != "None":
        try:
            csv_list = [row[0] for row in csv.reader(open(csv_file, newline=""), delimiter=" ", quotechar="|")]
        except FileNotFoundError:
            return messagebox.showerror("Error", "File not found\nCheck file path")
        images = [file for file in source_search(source) if
                  configure(os.path.basename(file)) in [configure(catnum) for catnum in csv_list]]
        search = create_image_list(range1,range2,meta,source,md_dict,op_dict,options2,options1)
        if search is not None:
            final_names = [j for j in images if (os.path.basename(j) in [os.path.basename(i) for i in search])]
            copy_files(final_names,new_folder_path)
            files_not_found(csv_list, final_names,new_folder_path)
            return
        copy_files(images,new_folder_path)
        files_not_found(csv_list,images,new_folder_path)

# asks user to name new directory, returns formatted path name or None
def name(image_list,new_folder_path):
    folder = format(askstring("", "%s image(s) found\nCreate new folder for copies" % len(image_list)))
    return str(new_folder_path % folder) if folder != "None" else None

# creates a new csv report of file names that were not found
def save_errors(image_list,new_folder_path):
    file_name = format(askstring("","Create report of %s files not found" % len(image_list)))
    new_file = str(new_folder_path%file_name)
    if new_file != "None":
        with open("%s.csv"%new_file ,"w", newline="") as csvfile:
            writer =  csv.writer(csvfile, delimiter=" ", quotechar="|", quoting=csv.QUOTE_MINIMAL)
            for i in image_list:
                writer.writerow([i])
        messagebox.showinfo("Success", "Report saved")

# displays the files that were not found and gives user option to save the data in a report
def files_not_found(csv_list, images_found,new_folder_path):
    found_images = [configure(os.path.basename(file)) for file in images_found]
    not_found = [i for i in csv_list if configure(i) not in found_images]
    if len(not_found) != 0:
        popup = Toplevel()
        popup.geometry("400x150")
        can = tk.Canvas(popup, borderwidth=0)
        frame = tk.Frame(can)
        vsb = Scrollbar(popup, orient="vertical", command=can.yview)
        vsb.pack(side="right", fill="y")
        can.configure(yscrollcommand=vsb.set)
        can.pack(side="left", fill="both", expand=True)
        can.create_window((4, 4), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda e, canvas=can: canvas.configure(scrollregion=canvas.bbox("all")))
        Label(frame, text="The following file(s) were not found:", font="bold").grid(column=0, row=0)
        Button(frame, text="Save to file", command=lambda: save_errors(not_found,new_folder_path)).grid(column=1, row=0)
        for i, row in enumerate(not_found):
            Label(frame, text="%s" % row, relief=RIDGE).grid(column=0, row=i + 1, sticky=NSEW)
        return
    return

# creates and copies images into new directory
def copy_files(image_list,new_folder_path):
    if not image_list:
        return messagebox.showinfo("", "No image(s) found")
    new_dir = name(image_list,new_folder_path)
    while new_dir is None or os.path.isdir(new_dir):
        if new_dir is None:
            return
        messagebox.showerror("Error", "A folder with that name already exists")
        new_dir = name(image_list,new_folder_path)
    os.mkdir(new_dir)
    [shutil.copy(path, new_dir) for path in image_list]
    messagebox.showinfo("Success", "New folder path:\n%s" % new_dir)

# creates entry box for each field a user can select records by and controls what boxes are disabled
def create_entry_box(window, col, row, state_toggle):
    box_name = (Entry(window, state=state_toggle))
    box_name.grid(column=col, row=row, sticky=W)
    return box_name

# traces the operator drop down menu, updates states of entry boxes
def op_drop_change(option,range1):
    op_drop = option.get()
    if op_drop == 'to':
        return range1.configure(state=NORMAL)
    return range1.configure(state=DISABLED)

# coordinates main window, creates widgets, labels, buttons, menus, calls on appropriate functions
def main():
    source = ""  # change to where images are kept
    new_folder_path = "/%s"  # change to path where new folder of image copies will be placed, KEEP '/%s'
    op_dict = {"=": eq, "<=": le, ">=": ge, ">": gt, "<": lt}
    md_dict = {"Subject": "XPSubject", "Tags": "XPKeywords"}  # update to what your OS system calls these md tags
    if not os.path.exists(source):
        return messagebox.showerror("Error", "Please check source path configuration\n Error in path %s" % source)
    window = Tk()
    window.title("Specify Image Select ")
    window.geometry("700x200")
    Label(window, text="Enter the image file name(s) to retrieve.\nNew directory will have copies of "
                       "selected files").grid(column=0, row=0, columnspan=6)
    Label(window, text="Search by file name").grid(column=0, row=1)
    Label(window, text="Search by metadata fields").grid(column=0, row=2)
    options1 = StringVar()
    options2 = StringVar()
    range1 = create_entry_box(window, 2, 1, DISABLED)
    range2 = create_entry_box(window, 4, 1, NORMAL)
    meta = create_entry_box(window, 2, 2, NORMAL)
    OptionMenu(window, options1, "=", "<=", ">=", ">", "<", "to").grid(column=3, row=1)
    OptionMenu(window, options2, "Subject", "Tags").grid(column=1, row=2, sticky=W)
    options1.trace("w", lambda *args: op_drop_change(options1,range1))
    Button(window, text="Search from a .csv file", command=lambda:
            csv_search(window,source,new_folder_path,range1.get(),range2.get(),meta.get(),
                       options1.get(),options2.get(),md_dict,op_dict)).grid(column=2, row=4)
    Button(window, text="Select image(s)", command=lambda:
            copy_files(create_image_list(configure(range1.get()), configure(range2.get()),
                        meta.get(),source,md_dict,op_dict,options2.get(),options1.get()),
                       new_folder_path)).grid(column=4, row=4)
    return window.mainloop()

if __name__ == "__main__":
    main()