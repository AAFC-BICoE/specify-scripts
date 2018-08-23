# specifycleaning
A package to support data cleaning and report creation for data from a Specify 6 database contained
in a MySQL schema.

## Getting Started 
These instructions will allow you to run the package on your local machine for use and testing.

### Prerequisites
- [Python >= 3.5](https://www.python.org/)
- Localhost [MySQL >= 5.5](https://dev.mysql.com/doc/mysql-getting-started/en/) server
  - Note the root username and password you create when installing MySQL 
- Data contained in a **Specify 6** schema
  - Note the name of the database where the Specify data is contained   
  
 ## Executing Scripts 
 **Executing Scripts From Command Line:**
 
 Scripts are configured to be executed from the command line. A tutorial on how  to run python scripts from Windows, 
 MacOS and Linux terminals can be found [here](https://www.pythoncentral.io/execute-python-script-file-shell/). For 
 all scripts, a list of available commands and their functions can be found by typing the ```-h``` command while 
 executing the script.  
 
 **PyMySQL Connector:**
 
 For scripts that reference the database directly, the python library ```PyMySQL``` is used. User credentials that 
 were chosen when the localhost MySQL server was installed and the name of the database that the script will 
 reference needs to be added to the command line prompt every time the script is run. An example of a (Linux) 
 connecting argument can be found below: 
 ```
  $ python my_script.py -u username -p password -d SpecifyDatabaseName ... 
 ```
 **Executing Test Scripts From Command Line:**
 
 All test scripts create and tear down their own sample database using the python library ```sqlite3 ``` and 
 therefore do not require a connection to the localhost MySQL server. These scripts can be run directly from the 
 command line with no other arguments needed. An example of a (Linux) command to run a test script can be found below: 
 ```
$ python test_script.py
```
 
 **Requirements:**
 
A list of the referenced libraries used in this package can be found in the ```REQUIREMENTS.txt``` file. 
To install the required libraries, ensure you have the latest version of ```pip``` installed.
Next run the command:

```
$ pip install -r requirements.txt
```

Further support for ```pip``` can be found [here](https://packaging.python.org/tutorials/installing-packages/).
Support for installing and using python packages can be found [here](https://docs.python.org/3/installing/) 
(for more details consult your Python IDE's instructions for importing libraries) .

 ## Licence
 This project is licensed under the MIT License - see the 
 [LICENSE](https://github.com/AAFC-BICoE/specify-scripts/blob/dev/LICENSE) file for details.
