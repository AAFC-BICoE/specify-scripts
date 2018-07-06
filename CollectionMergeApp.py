"""
Redmine Support #12201
Using the library 'tkinter', creates a UI that allows user to merge two collections together. User can choose to merge
one whole collection, or specify fields on the catalog numbers to merge only part of the collection. When a merge is
performed, script checks to make sure there are no conflicting catalog numbers, then switches any reference of the
collection that is being merged to the collection that it is being merged too. If a complete collection is being
merged then the collection is deleted after all switches have been made. If any conflicting catalog numbers are found
they are displayed and user has option to save report to an xls file.
"""
import pymysql as MySQLdb
import xlwt
from tkinter import *
from tkinter.ttk import *
from tkinter import (messagebox, ttk)
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
import tkinter as tk

db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')

checkConflicts = db.cursor()
removeReferences = db.cursor()
updateCollection = db.cursor()
delete = db.cursor()
collectionDict = db.cursor()
selectRecords = db.cursor()

# creates a dictionary of the collections that are present in schema
def create_collection_dict():
    collectionDict.execute("SELECT CollectionID,CollectionName FROM collection")
    for collection in collectionDict.fetchall(): coll_dict[str(collection[0])] = collection[1]

# creates button for each collection in schema
def create_button(window, coll, icol, irow):
    for key in coll_dict:
        Radiobutton(window, text="%s" %coll_dict[key], value=key, var=coll).grid(column=icol, row=irow, sticky=W)
        irow += 1

# creates entry box for each field a user can select records by
def create_entry_box(search, row, col, text):
    Label(search, text="%s" % text).grid(column=col, row=row, sticky=W)
    name = Entry(search, width=20)
    name.grid(column=col + 1, row=row, sticky=W)
    return name

# selects any catalog numbers that two collections share that would create conflicts
def check_conflict(option):
    checkConflicts.execute("SELECT B.CatalogNumber,B.CollectionObjectID,A.CollectionObjectID FROM collectionobject B "
                           "INNER JOIN collectionobject A ON A.CatalogNumber=B.CatalogNumber WHERE %s" % option)
    return checkConflicts.fetchall()

# selects records from collection that is being merged with any user specified fields the catalog numbers may have
def fetch_records(option):
    selectRecords.execute("SELECT A.CatalogNumber,A.CollectionObjectID,A.CollectionID FROM collectionobject A "
                          "WHERE A.collectionID = %s %s" % (c1.get(), option))
    return selectRecords.fetchall()

# removes any references of a collection by updating tables that reference collections by column name or foreign key
def remove_references(schema, option1, constraint, option2):
    removeReferences.execute("SELECT DISTINCT(T1.TABLE_NAME),T1.COLUMN_NAME FROM INFORMATION_SCHEMA.%s T1 %s WHERE "
                             "%s IN ('CollectionID','CollectionMemberID','UserGroupScopeID') "
                             "AND T1.TABLE_NAME != 'collection'" % (schema, option1, constraint))
    for table in removeReferences.fetchall():
        updateCollection.execute("UPDATE %s A SET A.%s=%s WHERE A.%s=%s %s"
                                 %(table[0], table[1], c2.get(), table[1], c1.get(), option2))
        db.commit()

# merges all of one collection to another by first checking for any possible conflicts, then feeding necessary
# information into functions to switch all references of old collection to merged one
def merge_all(tab_frame):
    conflict = check_conflict("A.CollectionID = %s AND B.CollectionID = %s" % (c1.get(), c2.get()))
    if len(conflict) == 0:
        remove_references("COLUMNS", "", "T1.COLUMN_NAME", "")
        remove_references("KEY_COLUMN_USAGE", "", "CONSTRAINT_SCHEMA='specify' AND REFERENCED_COLUMN_NAME", "")
        delete.execute("DELETE FROM collection WHERE collectionID=%s" % c1.get())
        db.commit()
        messagebox.showinfo("Merge Successful", "Merge was successful")
        return
    if messagebox.askyesnocancel("Error", "%s conflicts found in merge of %s into %s.\nShow conflicts?"
                                          % (len(conflict), coll_dict[c1.get()], coll_dict[c2.get()])):
        display_data(conflict, tab_frame, "Conflict Results", True, "")

# merges specified records from one collection to another by passing necessary information into functions to switch
# references of old collection to merged one for user selected catalog numbers
def merge_some(statement):
    remove_references("COLUMNS", "INNER JOIN INFORMATION_SCHEMA.COLUMNS T2 ON T2.TABLE_NAME = T1.TABLE_NAME",
                      "T2.COLUMN_NAME LIKE 'CatalogNumber' AND T1.COLUMN_NAME", ("AND %s" % statement))
    remove_references("KEY_COLUMN_USAGE", "INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE T2 ON T2.TABLE_NAME=T1.TABLE_NAME",
                      "T1.CONSTRAINT_SCHEMA='specify' AND T2.COLUMN_NAME LIKE 'CatalogNumber' AND T1.REFERENCED_COLUMN_NAME ",
                       ("AND %s" % statement))
    messagebox.showinfo("Merge Successful", "Merge was successful")

# formats user selected fields in order for query to be fed into necessary functions and displays popup window giving
# user option to merge records or display the records first
def format_merge(tab_frame):
    input_list = [("CatalogNumber BETWEEN '%s'AND'%s'", (cat_range1.get(), cat_range2.get())),
                  ("CatalogNumber LIKE '%s%s'", (cat_start.get(), '%')),
                  ("CatalogNumber LIKE '%s%s'", ('%', cat_end.get()))]
    statement_list = []
    for field in input_list:
        if "" not in field[1]: statement_list.append(field[0] % field[1] + "AND A.")
    statement = ("".join(statement_list))[:-6]
    data = fetch_records("AND A.%s" % statement)
    conflict = check_conflict("A.CollectionID = %s AND B.CollectionID = %s AND A.%s"% (c1.get(), c2.get(), statement))
    if len(data) != 0 and len(conflict) == 0:
        popup = Toplevel()
        popup.geometry("650x100")
        popup.title("Merge Collections")
        Label(popup, text="Merge %s records from %s into %s?"
                          %(len(data), coll_dict[c1.get()], coll_dict[c2.get()]), font="bold").pack()
        Button(popup, text="Yes", command=lambda: merge_some(statement) or popup.destroy()).pack()
        Button(popup, text="Display %s records to be merged"% len(data),command=lambda:
                            display_data(data,tab_frame,"Records To Be Merged",False,statement) or popup.destroy()).pack()
        Button(popup, text="Close", command=lambda: popup.destroy()).pack()
    elif len(data) == 0:
        messagebox.showinfo("Specify Collections Merge", "No records found")
    elif len(conflict) != 0:
        if messagebox.askyesnocancel("Error", "%s conflicts found in merge of %s into %s.\nShow conflicts?"
                                              % (len(conflict), coll_dict[c1.get()], coll_dict[c2.get()])):
            display_data(conflict, tab_frame, "Conflict Results", True, "")

# displays tab page for user to input record specifications
def specify_records_tab(tab_frame):
    global cat_range1, cat_range2, cat_start, cat_end
    tab_control.add(tab_frame, text="Select Records To Merge")
    Label(tab_frame, text="Enter fields to merge by:", font="bold").grid(column=0, row=0, sticky=W)
    Button(tab_frame, text="Close Tab", command=lambda: tab_frame.destroy()).grid(column=4, row=0, sticky=E)
    cat_range1 = create_entry_box(tab_frame, 2, 0, "Merge catalog numbers in range:")
    cat_range2 = create_entry_box(tab_frame, 2, 2, " To ")
    cat_start = create_entry_box(tab_frame, 4, 0, "Merge catalog numbers starting with: ")
    cat_end = create_entry_box(tab_frame, 5, 0, "Merge catalog numbers ending with: ")
    Button(tab_frame, text="Merge Records", command=lambda: format_merge(ttk.Frame(tab_control))).grid(column=4, row=6)

# saves data to an xls file that user names
def save_to_file(records, heading):
    name = (format(askstring("Save Report", "Save Report as: ")))
    if name != "None":
        wb = xlwt.Workbook()
        ws = wb.add_sheet("Query Results")
        heading_xf = xlwt.easyxf("font: bold on; align: wrap on, vert centre, horiz center")
        row1 = 0
        ws.set_panes_frozen(True)
        ws.set_horz_split_pos(row1 + 1)
        ws.set_remove_splits(True)
        for col1, value in enumerate(heading): ws.write(row1, col1, value, heading_xf)
        for i, row2 in enumerate(records):
            for j, col2 in enumerate(row2): ws.write(i + 1, j, col2)
        wb.save("%s.xls" % name)

# creates display tab and configures data to display, creates buttons depending on what data is being displayed
def configure_data_display(data_list, tab_frame, tab_name, heading, toggle, statement):
    tab_control.add(tab_frame, text=tab_name)
    canvas = tk.Canvas(tab_frame, borderwidth=0)
    frame = tk.Frame(canvas)
    vsb = tk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
    hsb = tk.Scrollbar(tab_frame, orient="horizontal", command=canvas.xview)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    canvas.configure(yscrollcommand=vsb.set)
    canvas.configure(xscrollcommand=hsb.set)
    canvas.pack(side="left", fill="both", expand=True)
    canvas.create_window((4, 4), window=frame, anchor="nw")
    frame.bind("<Configure>", lambda event, canvas=canvas: canvas.configure(scrollregion=canvas.bbox("all")))
    Label(frame, text="Total Records: %s " % len(data_list), font="bold").grid(column=0, row=0)
    Button(frame, text="Close Tab", command=lambda: tab_frame.destroy()).grid(column=3, row=0)
    if toggle:
        Button(frame, text="Save %s" %tab_name, command=lambda: save_to_file(data_list, heading)).grid(column=2, row=0)
        return frame
    Button(frame, text="Merge Records", command=lambda: merge_some(statement)).grid(column=2, row=0)
    return frame

# displays data in a table with headings depending on what the toggle is
def display_data(data, tab_frame, tab_name, toggle, statement):
    data_list = []
    for record in data:
        if toggle:
            heading = ["CatalogNumber","CollectionObjectID 1","Collection Name","CollectionObjectID 2","Collection Name"]
            data_list.append((record[0], record[1], coll_dict[c1.get()], record[2], coll_dict[c2.get()]))
        else:
            heading = ["CatalogNumber", "CollectionObjectID", "Collection Name"]
            data_list.append((record[0], record[1], coll_dict[c1.get()]))
    frame = configure_data_display(data_list, tab_frame, tab_name, heading, toggle, statement)
    for colx, value in enumerate(heading):
        Label(frame, text="%s" % value, font="bold", relief=RIDGE).grid(column=colx, row=1, sticky=NSEW)
    for i, row in enumerate(data_list):
        for j, col in enumerate(row):
            Label(frame, text="%s" % col, relief=RIDGE).grid(column=j, row=i + 2, sticky=NSEW)

# checks to make sure merge is legal and displays popup menu
def merge_options(tab_frame):
    if c1.get() == c2.get():
        messagebox.askretrycancel("Error", "Cannot merge a collection with itself")
        return
    num_records = len(fetch_records(""))
    if num_records != 0:
        popup = Toplevel()
        popup.geometry("650x100")
        popup.title("Merge Collections")
        Label(popup, text="Move ALL %s records from %s to %s?"
                          % (num_records, coll_dict[c1.get()], coll_dict[c2.get()]), font="bold").pack()
        Button(popup, text="Merge all %s records" % num_records,
               command= lambda: merge_all(tab_frame) or popup.destroy()).pack()
        Button(popup, text="Select records to merge", command=lambda: specify_records_tab(tab_frame) or popup.destroy()).pack()
        Button(popup, text="Close", command=lambda: popup.destroy()).pack()
        return
    messagebox.showinfo("Specify Collections Merge", "No records found")
    return

# creates initial display and coordinates program functions
def main():
    window = Tk()
    window.title("Specify Collection Merge")
    window.geometry("750x350")
    global tab_control, c1, c2,coll_dict
    coll_dict = {}
    tab_control = ttk.Notebook(window)
    merge = ttk.Frame(tab_control)
    tab_control.add(merge, text="Merge")
    create_collection_dict()
    Label(merge, text="Select collections to merge:", font="bold").grid(column=0, row=0, sticky=W)
    Label(merge, text="Collection 1", font="bold").grid(column=0, row=3, sticky=W)
    Label(merge, text="Collection 2", font="bold").grid(column=20, row=3, sticky=W)
    Label(merge, text="Merge into", font="bold").grid(column=1, row=3, sticky=W)
    c1 = StringVar(False)
    c2 = StringVar(False)
    create_button(merge, c1, 0, 4)
    create_button(merge, c2, 20, 4)
    Button(merge, text="Merge Collections",
           command=lambda: merge_options(ttk.Frame(tab_control))).grid(column=1,row=12,sticky=W)
    tab_control.pack(expand=1, fill="both")
    window.mainloop()

main()
db.close()