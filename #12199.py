import pymysql as MySQLdb
try:                       
    db = MySQLdb.connect("localhost",#username, #password,#specify database )
except:
    print('MySQL connecting error')
    
foreignKeyCheckOff = db.cursor()
select = db.cursor()
delete = db.cursor()
foreignKeyCheckOn = db.cursor()

try:
    foreignKeyCheckOff.execute("""SET foreign_key_checks = 0""")
    select.execute("""SELECT COUNT(*) FROM (SELECT L.LocalityName, L.LocalityID
                   FROM locality L LEFT JOIN collectingevent C
                   ON C.LocalityID = L.LocalityID WHERE C.LocalityID IS NULL) AS RecordsSelected""")
    delete.execute("""DELETE L FROM locality L LEFT JOIN collectingevent C
                      ON C.LocalityID = L.LocalityID WHERE C.LocalityID IS NULL""")
    foreignKeyCheckOn.execute("""SET foreign_key_checks = 1""")
    
except:
    print('Query error')
    
data = select.fetchall()

if data[0][0] == 0:
    print('No orphan records found')
else:
    print('Number of rows successfully deleted:' , data[0][0])

db.close()
