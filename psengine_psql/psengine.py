# IMPORTS
import os
import sqlite3
import psycopg2
import datetime
from datetime import datetime

# Scripts `pageget.py` and 'pagexp.py`
import scripts
from scripts import *

# QUESTION #1
# What would you like to do? [1] Add resource(s) [2] Search resources [3] Recreate database from page backups
def q1():
    # Listing valid responses for the error/correction loop and asking the question
    valid_resps = ["1", "2", "3"]
    resp = input("What would you like to do?\n\t[1] Add resource(s)\n\t[2] Search resources\n\t[3] Recreate database from page backups\n\n").strip()

    # Error/correction loop
    while resp not in valid_resps:
        print("="*(17+len(resp)) + "<")
        print("Invalid option: %s |" % str(resp))
        print("="*(17+len(resp)) + "<")
        resp = q1()
    print("")
    return resp

# QUESTION #2
# How would you like to input new resources? [1] Input individually [2] Point to file
def q2():
    # Listing valid responses for the error/correction loop and asking the question
    valid_resps = ["1", "2"]
    resp = input("How would you like to input new resources?\n\t[1] Input individually\n\t[2] Point to file\n\n").strip()

    # Error/correction loop
    while resp not in valid_resps:
        print("="*(17+len(resp)) + "<")
        print("Invalid option: %s |" % str(resp))
        print("="*(17+len(resp)) + "<")
        resp = q1()
    print("")
    return resp

# QUESTION #3
# How would you like to search? [1] By title [2] With search terms
def q3():
    # Listing valid responses for the error/correction loop and asking the question
    valid_resps = ["1", "2", "3"]
    resp = input("How would you like to search?\n\t[1] By title\n\t[2] With search terms\n\n").strip()

    # Error/correction loop
    while resp not in valid_resps:
        print("="*(17+len(resp)) + "<")
        print("Invalid option: %s |" % str(resp))
        print("="*(17+len(resp)) + "<")
        resp = q1()
    print("")
    return resp

# ANSWERS FOR QUESTION #2
# Triggers the `pageget.py` script that will get information from pages
def sourceit(type):
    if type == "1": 
        # Takes URL input and tries to run `pageget.py`
        url = input("Please input the entire URL of the page (including \"https\"): ").strip()
        print("Retrieving page...\n")

        # Try/except is to allow interruption with <Ctrl-C>
        try:
            x = pageget.main("url", url)
            if x == 0: print("\n No URLs added.\n")
            elif x == 1: print("\nURL added!\n")
        except KeyboardInterrupt:
            os.system("cls" if os.name == "nt" else "clear")
            pass

    elif type == "2":
        # Finds source list files and displays them as options
        filelist = os.listdir("sources")
        fileopt = {}
        for i in range(0, len(filelist)):
            fileopt[str(i+1)] = "sources/" + filelist[i]

        print("\n==========")
        for i in range(0, len(filelist)):
            print("\n[{0}] - {1}".format(str(i+1), fileopt[str(i+1)]))
        print("\n==========\n")

        # Takes the number option input and tries to run `pageget.py`
        filename = fileopt[input("Please input the number of the file containing your sources: ").strip()]
        print("Retrieving pages...\n")

        # Try/except is to allow interruption with <Ctrl-C>
        try:
            print(datetime.utcnow())
            x = pageget.main("file", filename)
            if x == 0: print("\n No URLs added.\n")
            elif x == 1: print("\nURL added!\n")
            else: print("\nURLs added!\n")
            print(datetime.utcnow())
        except KeyboardInterrupt:
            os.system("cls" if os.name == "nt" else "clear")
            pass

    # Connects to the "pageexplorer.db" database (created in `pageget.py') and
    #     attempts to create an index.
    # TODO: Make sure this does *create* the database in case there's an error 
    #       that happens before `pageget.py` can get to doing it.
    # conn = sqlite3.connect('psengine.db')
    conn = psycopg2.connect(host="127.0.0.1", database="testdb", user="psengine", password="psengine")
    c = conn.cursor()
    c.execute("CREATE INDEX IF NOT EXISTS xp_index ON words(p_id, word);")
    conn.commit()
    conn.close()

# ANSWERS FOR QUESTION #3
# Triggers the `pagexp.py` script that will search information
def searchit(type):
    if type == "1":
        # Lists the available pages by title and URL.
        # conn = sqlite3.connect("psengine.db")
        conn = psycopg2.connect(host="127.0.0.1", database="testdb", user="psengine", password="psengine")
        c = conn.cursor()
        c.execute("SELECT * FROM pages")
        ind = 0

        # Try/except is to allow interruption with <Ctrl-C>
        try:
            result = c.fetchmany(10)
            while len(result) != 0:
                for i in result:
                    ind += 1
                    print("#{0:<4} {1}\n\t {2}".format(str(ind)+":".strip(), i[2].split("||*-*||")[0], i[2].split("||*-*||")[1]).strip())
                input("\nView more titles with <Enter>, or restart program with <Ctrl-c>\n")
                result = c.fetchmany(10)

            input("No more results. Restart Program with <Enter> or <Ctrl-C>.")
            conn.close()
            os.system("cls" if os.name == "nt" else "clear")

        except KeyboardInterrupt:
            conn.close()
            os.system("cls" if os.name == "nt" else "clear")

    elif type == "2":
        try:
            # Tries to run `pagexp.py`
            print(datetime.utcnow())
            pagexp.searcher()
            os.system("cls" if os.name == "nt" else "clear")
        except KeyboardInterrupt:
            print(datetime.utcnow())
            os.system("cls" if os.name == "nt" else "clear")
            pass

def restoreit():
    try:
        # Tries to run `restoredb.py`
        restoredb.main()
        os.system("cls" if os.name == "nt" else "clear")
    except KeyboardInterrupt:
        os.system("cls" if os.name == "nt" else "clear")
        pass

# The quiz structure; gets looped in the main function
def explorer():
    # Asks a question and then branches to the appropriate next question and 
    #     asks it.
    what_to_do = q1()
    if what_to_do == "1":
        sourceit(q2())
    elif what_to_do == "2":
        searchit(q3())
    else:
        restoreit()

if __name__=="__main__":
    # Runs explorer in a loop.
    while True:
        print("\n=====+- Welcome to PSENGINE -+=====\n")
        explorer()
