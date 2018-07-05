import pymysql as MySQLdb
import xlwt
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox
from tkinter.simpledialog import askstring
from tkinter.messagebox import showinfo
from tkinter import ttk
import tkinter as tk
import itertools

db = MySQLdb.connect("localhost", '''"MySQLusername", "MySQLpassword", "MySQLdatabaseName"''')

fetchRecords = db.cursor()
headings = ["Catalog Number","DAO Accession Number","Collection","Collector Last Name(s)","Taxon Name","Geography","Year Collected"]
counter=0

# formats the raw data returned from the database search by filtering out duplicate records, counting records with
# duplicate catalog numbers and handling records with multiple collectors and/or multiple names
def format_records(raw_data):
    raw_data_dict = {}
    key_data = []
    for record in raw_data:
        if record[0] not in key_data: key_data.append(record[0])
        key = (record[0],record[4],record[2])
        if (key in raw_data_dict) and (record[3] not in raw_data_dict[key][3][0]) and (record[2]==raw_data_dict[key][2][0]):
            raw_data_dict[key][3][0] +=", " + str(record[3])
        else:
            raw_data_dict[key]=[[record[0]],[record[1]],[record[2]],[str(record[3])],[record[4]],[record[5]],[record[6]]]
    return raw_data_dict,len(key_data)

# selects all required information from the database using an identifying statement with the formatted
#  user specified statement
def fetch_info(statement):
    fetchRecords.execute("SELECT CO.CatalogNumber,CO.AltCatalogNumber,CL.CollectionName,A.LastName,T.Fullname,"
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
    print('here 5')
    return format_records(fetchRecords.fetchall())

# configures conditions into a statement that MySQL is able to interpret
def return_entry():

    input_list = [("CO.CatalogNumber LIKE'%s'",catalognum.get()),("CO.AltCatalogNumber LIKE'%s'",dao.get()),
                  ("A.LastName LIKE '%s%s%s'",('%',lastname.get(),'%')),("T.FullName LIKE'%s'",geography.get()),
                  ("YEAR(CE.StartDate) LIKE '%s'",year.get()),("G.FullName LIKE '%s%s%s'",('%',province.get(),'%'))]
    #statement_list = []
    for field in input_list:
        print(input_list)
        print(field)
        statement_list = [(field[0] % field[1] + "AND ") if "" not in field else None]

        #if field[1] != "": statement_list.append(field[0] % field[1] + "AND ")
    print(("".join(statement_list))[:-4])
    return fetch_info(("".join(statement_list))[:-4])

# saves the search results to a .xls file named by the user
def save_to_file(records):
    name = (format(askstring("Save Query Search","Save results of query as: ")))
    if name != 'None':
        wb = xlwt.Workbook()
        ws = wb.add_sheet("Query Results")
        heading_xf = xlwt.easyxf("font: bold on; align: wrap on, vert centre, horiz center")
        row1 = 0
        ws.set_panes_frozen(True)
        ws.set_horz_split_pos(row1+1)
        ws.set_remove_splits(True)
        for col1,value in enumerate(headings): ws.write(row1,col1,value,heading_xf)
        for i,row2 in enumerate(records):
            for j,col2 in enumerate(records[row2]): ws.write(i+1,j,col2[0])
        wb.save("%s.xls" % name)

# configures the display of the results of each query
def configure_results(records,tab_frame):
        global counter
        counter+=1
        tab_control.add(tab_frame, text="Query %s" % str(counter))
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
        Label(frame, text="Total Records Found: %s " % len(records[0]), font="bold").grid(column=0,row=0)
        Label(frame, text="Total Distinct Catalog Numbers: %s" % records[1], font="bold").grid(column=1,row=0)
        Button(frame,text="Save Query",command= lambda: save_to_file(records[0])).grid(column=2,row=0)
        Button(frame,text='Close Tab', command= lambda: tab_frame.destroy()).grid(column=3,row=0)
        return frame

# displays the results of each query to a new tab inside the original window
def display_results(tab_frame):
    records = return_entry()
    if records[1] != 0:
        frame = configure_results(records,tab_frame)
        for col, value in enumerate(headings): Label(frame, text="%s" % value, font="bold", relief=RIDGE).grid(column=col,row=1, sticky=NSEW)
        for i, row in enumerate(records[0]):
            for j, data in enumerate(records[0][row]):
               Label(frame, text="%s" % data[0], relief=RIDGE).grid(column=j,row=i+2,sticky=NSEW)
    else:
        messagebox.showinfo("Specify Collections Search", "No records found")

# creates entry boxes for each field a user can search by
def create_entry_box(search, row, text):
    Label(search,text="%s" % text).grid(column=0,row=row)
    name = Entry(search,width=20)
    name.grid(column=1,row=row,sticky=W)
    return name

# creates initial window and tab where search fields are input, sets global variables
def main():
    window = Tk()
    window.title("Specify Collections Search")
    window.geometry("850x350")
    global catalognum,dao,lastname,geography,year,province,tab_control
    tab_control = ttk.Notebook(window)
    search = ttk.Frame(tab_control)
    tab_control.add(search,text="Search")
    Label(search,text="Enter fields to search by").grid(column=0, row=0)
    catalognum = create_entry_box(search,2,"Catalog Number")
    dao = create_entry_box(search,3,"DAO Accession Number")
    lastname = create_entry_box(search,4,"Collector Last Name")
    geography = create_entry_box(search,5,"Taxon Name")
    year = create_entry_box(search,6,"Collection Year")
    province = create_entry_box(search,7,"Province/State")
    Button(search,text="Search",command=lambda: display_results(ttk.Frame(tab_control))).grid(column=1,row=8)
    tab_control.pack(expand=1,fill="both")
    window.mainloop()

main()
db.close()