"""
Redmine Support #12201
Using the library 'tkinter', creates a UI that is able to merge two collections together. User can choose to merge
one whole collection, or select catalog numbers to merge only part of the collection. When a merge is performed,
script checks to make sure there are no conflicting catalog numbers, then switches any reference of the collection that
is being merged to the collection that it is being merged too. If an entire collection is being merged then the empty
collection is deleted after all switches have been made. If any conflicting catalog numbers are found they are
displayed and user has option to save report of conflicts as a csv file.
"""
import pymysql as MySQLdb
import tkinter as tk
from tkinter import *
from tkinter.ttk import *
from tkinter import (messagebox, ttk)
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
from csvwriter import write_report

# creates a dictionary of the collections that are present in schema
def create_collection_dict(db):
    db_collection = db.cursor()
    coll_dict = {}
    db_collection.execute("SELECT CollectionID,CollectionName FROM collection")
    for collection in db_collection.fetchall():
        coll_dict[str(collection[0])] = collection[1]
    return coll_dict
# creates button for each collection in schema
def create_button(window, coll, icol, irow,coll_dict):
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
def check_conflict(option,db):
    db_conflict = db.cursor()
    db_conflict.execute("SELECT B.CatalogNumber,B.CollectionObjectID,A.CollectionObjectID FROM collectionobject B "
                        "INNER JOIN collectionobject A ON A.CatalogNumber=B.CatalogNumber WHERE %s" % option)
    return db_conflict.fetchall()

# selects records from collection that is being merged with any conditions the catalog numbers may have
def fetch_records(option,c1,db):
    db_select_records = db.cursor()
    db_select_records.execute("SELECT A.CatalogNumber,A.CollectionObjectID,A.CollectionID FROM collectionobject A "
                              "WHERE A.collectionID = %s %s" % (c1.get(), option))
    return db_select_records.fetchall()

# switches any references of a collection by updating tables that reference collections by column name or foreign key
def remove_references(schema, option1, constraint, option2,db,c1,c2):
    db_switch_ref = db.cursor()
    db_update = db.cursor() #maybe fixme
    db_switch_ref.execute("SELECT DISTINCT(T1.TABLE_NAME),T1.COLUMN_NAME FROM INFORMATION_SCHEMA.%s T1 %s WHERE %s IN "
                          "('CollectionID','CollectionMemberID','UserGroupScopeID') AND T1.TABLE_NAME != 'collection'"
                            % (schema, option1, constraint))
    for table in db_switch_ref.fetchall():
        db_update.execute("UPDATE %s A SET A.%s=%s WHERE A.%s=%s %s"
                          %(table[0], table[1], c2.get(), table[1], c1.get(), option2))
        db.commit()

# checks for catalog number conflicts, calls on necessary functions to merges all of one collection into another
def merge_all(tab_frame,c1,c2,db,coll_dict,tab_control):
    db_delete = db.cursor()
    conflict = check_conflict("A.CollectionID = %s AND B.CollectionID = %s" % (c1.get(), c2.get()),db)
    if len(conflict) == 0:
        remove_references("COLUMNS", "", "T1.COLUMN_NAME", "",db,c1,c2)
        remove_references("KEY_COLUMN_USAGE", "", "CONSTRAINT_SCHEMA='specify' AND REFERENCED_COLUMN_NAME", "",db,c1,c2)
        db_delete.execute("DELETE FROM collection WHERE collectionID=%s" % c1.get())
        db.commit()
        return messagebox.showinfo("Merge Successful", "Merge was successful")
    if messagebox.askyesnocancel("Error", "%s conflicts found in merge of %s into %s.\nShow conflicts?"
                                          % (len(conflict), coll_dict[c1.get()], coll_dict[c2.get()])):
        display_data(conflict, tab_frame, "Conflict Results", True, "",coll_dict,c1,c2,tab_control,db)

# calls on necessary function to merge specified records from one collection to another
def merge_some(statement,db,c1,c2):
    remove_references("COLUMNS", "INNER JOIN INFORMATION_SCHEMA.COLUMNS T2 ON T2.TABLE_NAME = T1.TABLE_NAME",
                      "T2.COLUMN_NAME LIKE 'CatalogNumber' AND T1.COLUMN_NAME", ("AND %s" % statement),db,c1,c2)
    remove_references("KEY_COLUMN_USAGE", "INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE T2 ON T2.TABLE_NAME = "
                      "T1.TABLE_NAME","T1.CONSTRAINT_SCHEMA='specify' AND T2.COLUMN_NAME LIKE 'CatalogNumber' AND "
                      "T1.REFERENCED_COLUMN_NAME ",("AND %s" % statement),db,c1,c2)
    messagebox.showinfo("Merge Successful", "Merge was successful")

# formats user selected fields for query to be used, displays popup window giving option to display or merge records
def format_merge(tab_frame,cat_range1,cat_range2,cat_start,cat_end,coll_dict,c1,c2,db,tab_control):
    input_list = [("CatalogNumber BETWEEN '%s'AND'%s'", (cat_range1.get(), cat_range2.get())),
                  ("CatalogNumber LIKE '%s%s'", (cat_start.get(), '%')),
                  ("CatalogNumber LIKE '%s%s'", ('%', cat_end.get()))]
    statement_list = list(field[0] % field[1] + "AND A." for field in input_list if "" not in field[1])
    statement = ("".join(statement_list))[:-6]
    data = fetch_records("AND A.%s" % statement, c1, db)
    conflict = check_conflict("A.CollectionID=%s AND B.CollectionID=%s AND A.%s"% (c1.get(), c2.get(), statement),db)
    if len(data) != 0 and len(conflict) == 0:
        popup = Toplevel()
        popup.geometry("650x100")
        popup.title("Merge Collections")
        Label(popup, text="Merge %s records from %s into %s?"
                          %(len(data), coll_dict[c1.get()], coll_dict[c2.get()]), font="bold").pack()
        Button(popup, text="Yes", command=lambda: merge_some(statement,db,c1,c2) or popup.destroy()).pack()
        Button(popup, text="Display %s records to be merged"% len(data),command=lambda:
               display_data(data,tab_frame,"Records To Be Merged",False,statement,coll_dict,c1,c2,tab_control,db)
               or popup.destroy()).pack()
        Button(popup, text="Close", command=lambda: popup.destroy()).pack()
    elif len(data) == 0:
        messagebox.showinfo("Specify Collections Merge", "No records found")
    elif len(conflict) != 0:
        if messagebox.askyesnocancel("Error", "%s conflicts found in merge of %s into %s.\nShow conflicts?"
                                              % (len(conflict), coll_dict[c1.get()], coll_dict[c2.get()])):
            display_data(conflict, tab_frame, "Conflict Results", True, "",coll_dict,c1,c2,tab_control,db)

# displays tab page for user to input record specifications
def specify_records_tab(tab_frame,tab_control,coll_dict,c1,c2,db):
    tab_control.add(tab_frame, text="Select Records To Merge")
    Label(tab_frame, text="Enter fields to merge by:", font="bold").grid(column=0, row=0, sticky=W)
    Button(tab_frame, text="Close Tab", command=lambda: tab_frame.destroy()).grid(column=4, row=0, sticky=E)
    cat_range1 = create_entry_box(tab_frame, 2, 0, "Merge catalog numbers in range:")
    cat_range2 = create_entry_box(tab_frame, 2, 2, " To ")
    cat_start = create_entry_box(tab_frame, 4, 0, "Merge catalog numbers starting with: ")
    cat_end = create_entry_box(tab_frame, 5, 0, "Merge catalog numbers ending with: ")
    Button(tab_frame, text="Merge Records", command=lambda:format_merge(
        ttk.Frame(tab_control),cat_range1,cat_range2, cat_start,cat_end,
        coll_dict,c1,c2,db,tab_control)).grid(column=4, row=6)

# saves data to a csv file that user names
def save_to_file(records, heading):
    name = (format(askstring("Save Report", "Save Report as: ")))
    if name != "None":
        write_report(name,heading,records)
        messagebox.showinfo("Success","Report saved as %s.csv"%name)

# creates display tab and configures data to display, creates buttons depending on what data is being displayed
def configure_data_display(tab_control,data_list, tab_frame, tab_name, heading, toggle, statement,db,c1,c2):
    tab_control.add(tab_frame, text=tab_name)
    can = tk.Canvas(tab_frame, borderwidth=0)
    frame = tk.Frame(can)
    vsb = tk.Scrollbar(tab_frame, orient="vertical", command=can.yview)
    hsb = tk.Scrollbar(tab_frame, orient="horizontal", command=can.xview)
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    can.configure(yscrollcommand=vsb.set)
    can.configure(xscrollcommand=hsb.set)
    can.pack(side="left", fill="both", expand=True)
    can.create_window((4, 4), window=frame, anchor="nw")
    frame.bind("<Configure>", lambda event, canvas=can: canvas.configure(scrollregion=canvas.bbox("all")))
    Label(frame, text="Total Records: %s " % len(data_list), font="bold").grid(column=0, row=0)
    Button(frame, text="Close Tab", command=lambda: tab_frame.destroy()).grid(column=3, row=0)
    if toggle:
        Button(frame, text="Save %s" %tab_name, command=lambda: save_to_file(data_list, heading)).grid(column=2, row=0)
        return frame
    Button(frame, text="Merge Records", command=lambda: merge_some(statement,db,c1,c2)).grid(column=2, row=0)
    return frame

# displays data in a table with headings and data depending on what the user is displaying (conflicts or merge)
def display_data(data, tab_frame, tab_name, toggle, statement,coll_dict, c1,c2, tab_control,db):
    if toggle:
        heading = ["CatalogNumber","CollectionObjectID 1","Collection Name","CollectionObjectID 2","Collection Name"]
        data_list = list((record[0],record[1],coll_dict[c1.get()],record[2],coll_dict[c2.get()]) for record in data)
    else:
        heading = ["CatalogNumber", "CollectionObjectID", "Collection Name"]
        data_list = list((record[0],record[1],coll_dict[c1.get()]) for record in data)
    frame = configure_data_display(tab_control,data_list, tab_frame, tab_name, heading, toggle, statement,db,c1,c2)
    for colx, value in enumerate(heading):
        Label(frame, text="%s" % value, font="bold", relief=RIDGE).grid(column=colx, row=1, sticky=NSEW)
    for i, row in enumerate(data_list):
        for j, col in enumerate(row):
            Label(frame, text="%s" % col, relief=RIDGE).grid(column=j, row=i + 2, sticky=NSEW)

# checks to make sure merge is legal and displays popup menu
def merge_options(tab_frame,c1,c2,db,coll_dict,tab_control):
    if c1.get() == c2.get():
        return messagebox.askretrycancel("Error", "Cannot merge a collection with itself")
    num_records = len(fetch_records("",c1,db))
    if num_records == 0:
        return messagebox.showinfo("Specify Collections Merge", "No records found")
    popup = Toplevel()
    popup.geometry("650x100")
    popup.title("Merge Collections")
    Label(popup, text="Move ALL %s records from %s to %s?"
                      % (num_records, coll_dict[c1.get()], coll_dict[c2.get()]), font="bold").pack()
    Button(popup, text="Merge all %s records" % num_records,
           command= lambda: merge_all(tab_frame,c1,c2,db,coll_dict,tab_control) or popup.destroy()).pack()
    Button(popup, text="Select records to merge", command=lambda:
                            specify_records_tab(tab_frame,tab_control,coll_dict,c1,c2,db) or popup.destroy()).pack()
    Button(popup, text="Close", command=lambda: popup.destroy()).pack()

# creates initial display and coordinates program functions
def main():
    db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')
    window = Tk()
    window.title("Specify Collection Merge")
    window.geometry("750x350")
    tab_control = ttk.Notebook(window)
    merge = ttk.Frame(tab_control)
    tab_control.add(merge, text="Merge")
    coll_dict = create_collection_dict(db)
    Label(merge, text="Select collections to merge:", font="bold").grid(column=0, row=0, sticky=W)
    Label(merge, text="Collection 1", font="bold").grid(column=0, row=3, sticky=W)
    Label(merge, text="Collection 2", font="bold").grid(column=20, row=3, sticky=W)
    Label(merge, text="Merge into", font="bold").grid(column=1, row=3, sticky=W)
    c1 = StringVar(False)
    c2 = StringVar(False)
    create_button(merge, c1, 0, 4,coll_dict)
    create_button(merge, c2, 20, 4,coll_dict)
    Button(merge, text="Merge Collections", command=lambda:
                merge_options(ttk.Frame(tab_control), c1, c2,db,coll_dict,tab_control)).grid(column=1,row=12,sticky=W)
    tab_control.pack(expand=1, fill="both")
    window.mainloop()

if __name__ == "__main__":
    main()