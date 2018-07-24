# Specify Data Cleaning and Reporting Scripts
A collection of scripts to be used for data cleaning and making reports with AAFC data contained in a MySQL database.
## Getting Started 
### Prerequisites
- [Python >=3.5](https://www.python.org/)
- localhost [MySQL >=5.5](https://dev.mysql.com/doc/mysql-getting-started/en/) server
  - Note the root username and password you create when installing MySQL 
- AAFC Specify Data
- MS Excel 97/2000/XP/2003 XLS or equivalent  
 
 ## Running Scripts 
 **pymysql Connector:**
 
 For each script the python library ```pymysql``` requires a connector statement containing the credentials for the localhost MySQL Server. The username and password that was chosen 
 when MySQL was installed and the name of the database that contains the specify data should be input into the string placeholder as:
 ```
  db = MySQLdb.connect("localhost", "username", "password", "SpecifyDatabaseName")
 ```
 **Other Python Libraries:**
 
 All libraries used in this repository are standard Python 3.x packages. Instructions on how to install and use them can be found
 [here](https://docs.python.org/3/installing/) (for more details consult your Python IDE's instructions for importing libraries) 
 
 ## Licence
 This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/AAFC-BICoE/specify-scripts/blob/dev/LICENSE) file for details
