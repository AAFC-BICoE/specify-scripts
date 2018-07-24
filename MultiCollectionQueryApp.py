"""
Redmine Feature #6046
Using library tkinter, creates a UI that can search across all collections in schema by catalog number, DAO accession
number, collector lastname, taxon name, province and/or year. Once search results have been displayed, user has
ability to save a copy of the results in a csv file.
"""
import pymysql as MySQLdb
import csv
import tkinter as tk
import itertools
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
from tkinter import ttk

# formats records with multiple collectors to be only displayed once, counts the number of distinct catalog numbers
def format_records(raw_data):
    raw_data_dict = {}
    catalog_nums = []
    clean_data = []
    for record in raw_data:
        if record[0] not in catalog_nums: catalog_nums.append(record[0])
        key = (record[0],record[4],record[2])
        if (key in raw_data_dict) and (record[3] not in raw_data_dict[key][3][0]) and (record[2]==raw_data_dict[key][2][0]):
            raw_data_dict[key][3][0] +=", " + str(record[3])
        else:
            raw_data_dict[key]=[[record[0]],[record[1]],[record[2]],[str(record[3])],[record[4]],[record[5]],[record[6]]]
    for value in raw_data_dict:
        clean_data += [[y for x in raw_data_dict[value] for y in x]]
    return clean_data,len(catalog_nums)

# selects all required columns from schema using an identifying statement with the formatted user specified statement
def fetch_info(statement,db):
    db_fetch_records = db.cursor()
    db_fetch_records.execute("SELECT CO.CatalogNumber,CO.AltCatalogNumber,CL.CollectionName,A.LastName,T.Fullname,"
                             "G.FullName,YEAR(CE.StartDate) FROM collectionobject CO "
                             "INNER JOIN collection CL ON CL.CollectionID=CO.CollectionID "
                             "INNER JOIN collectingevent CE ON CE.CollectingEventID=CO.CollectingEventID "
                             "INNER JOIN collector C ON C.CollectingEventID=CE.CollectingEventID "
                             "INNER JOIN determination D ON D.CollectionObjectID=CO.CollectionObjectID "
                             "INNER JOIN agent A ON A.AgentID=C.AgentID "
                             "INNER JOIN taxon T ON T.TaxonID=D.TaxonID "
                             "INNER JOIN locality L ON L.LocalityID=CE.LocalityID "
                             "INNER JOIN geography G ON G.GeographyID=L.GeographyID "
                             "WHERE %s" % statement)
    return format_records(db_fetch_records.fetchall())

# configures conditions into a statement that MySQL is able to interpret
def return_entry(catalognum,dao,lastname,geography,year,province,db):
    input_list = [("CO.CatalogNumber LIKE'%s'",catalognum.get()),("CO.AltCatalogNumber LIKE'%s'",dao.get()),
                  ("A.LastName LIKE '%s%s%s'",('%',lastname.get(),'%')),("T.FullName LIKE'%s'",geography.get()),
                  ("YEAR(CE.StartDate) LIKE '%s'",year.get()),("G.FullName LIKE '%s%s%s'",('%',province.get(),'%'))]
    statement_list = list((field[0] % field[1] + "AND ") for field in input_list if field[1] != "")
    return fetch_info(("".join(statement_list))[:-4],db)

# saves the search results to a csv file named by the user
def save_to_file(records,headings):
    name = (format(askstring("Save Query Search","Save results of query as: ")))
    if name != 'None':
        with open("%s.csv" % name, "w") as file_writer:
            writer = csv.writer(file_writer)
            writer.writerow(headings)
            for row in records:
                writer.writerow(row)
        messagebox.showinfo("Success", "Report saved as %s.csv" % name)

# configures the display of the results of each query
def configure_results(records,tab_frame,tab_control,headings):
        tab_control.add(tab_frame, text="Query" )
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
        Label(frame, text="Total Records Found: %s " % len(records[0]), font="bold").grid(column=0,row=0)
        Label(frame, text="Total Distinct Catalog Numbers: %s" % records[1], font="bold").grid(column=1,row=0)
        Button(frame,text="Save Query",command= lambda: save_to_file(records[0],headings)).grid(column=2,row=0)
        Button(frame,text="Close Tab", command= lambda: tab_frame.destroy()).grid(column=3,row=0)
        return frame

# displays the results of each query to a new tab inside the original window
def display_results(tab_frame,catalognum,dao,lastname,geography,year,province,db,tab_control):
    headings = ["Catalog Number", "DAO Accession Number", "Collection", "Collector Last Name(s)", "Taxon Name",
                "Geography", "Year Collected"]
    records = return_entry(catalognum,dao,lastname,geography,year,province,db)
    if records[1] == 0:
        return messagebox.showinfo("Specify Collections Search", "No records found")
    frame = configure_results(records,tab_frame,tab_control,headings)
    for col, value in enumerate(headings):
        Label(frame, text="%s" % value, font="bold", relief=RIDGE).grid(column=col,row=1, sticky=NSEW)
    for i, row in enumerate(records[0]):
        for j, data in enumerate(row):
           Label(frame, text="%s" % data, relief=RIDGE).grid(column=j,row=i+2,sticky=NSEW)

# creates entry boxes for each field a user can search by
def create_entry_box(search, row, text):
    Label(search,text="%s" % text).grid(column=0,row=row)
    name = Entry(search,width=20)
    name.grid(column=1,row=row,sticky=W)
    return name

# creates initial window and tab where search fields are input
def main():
    db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')
    window = Tk()
    window.title("Specify Collections Search")
    window.geometry("850x350")
    tab_control = ttk.Notebook(window)
    search = ttk.Frame(tab_control)
    tab_control.add(search,text="Search")
    Label(search,text="Enter fields to search by").grid(column=0, row=0)
    catnum = create_entry_box(search,2,"Catalog Number")
    dao = create_entry_box(search,3,"DAO Accession Number")
    ln = create_entry_box(search,4,"Collector Last Name")
    geo = create_entry_box(search,5,"Taxon Name")
    yr = create_entry_box(search,6,"Collection Year")
    prov = create_entry_box(search,7,"Province/State")
    Button(search,text="Search",command=lambda:
    display_results(ttk.Frame(tab_control),catnum,dao,ln,geo,yr,prov,db,tab_control)).grid(column=1,row=8)
    tab_control.pack(expand=1,fill="both")
    window.mainloop()

if __name__ == "__main__":
    main()
