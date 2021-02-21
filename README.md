# psengine
A Python 3-based search engine for locally-stored webpages. Uses either SQLite3 and PostgreSQL. Should work on Windows and Linux/Mac 

# Intructions  
1. Pip(3) install dependencies using the "pep_req.txt" file.
2. Choose the version you want, change directories, and run the "psengine.py" script with Python 3.x.  
*(If you are using the PostgreSQL version, you need to have a PostgreSQL server running somewhere you can access along with credentials fora user with full permissions/superuser permissions on the specific database. Change the connection string where it appears in each ".py" file.)*  

3. Add some resources. Use either a single URL or a file containing a URL on each line.  
4. Search the resources by either listing them or using search terms.   
5. Reset the database any time using the reset.sh/reset.bat script (depending on whether you are using Windows or Linux/Mac) or the "restore database" option in the main script.  
