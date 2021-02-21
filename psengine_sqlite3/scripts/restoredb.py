# IMPORTS
import os
import sqlite3

from . import pageget

def getpagelist():
    conn = sqlite3.connect('psengine.db')
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("SELECT COUNT(*) FROM pages")
    num = c.fetchone()[0]
    conn.close()
    return num

def inserts(info, wordcount):
    hashy, title, url, bodylen = info[0], info[1], info[2], info[3]
    conn = sqlite3.connect('psengine.db')
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("INSERT INTO pages(hash, title_url, bodylen) values(?, ?, ?);", (hashy, title + "||*-*||" + url, bodylen))
    pageid = c.lastrowid
   
    wordcount_toex = [(pageid, k, v) for k, v in wordcount.items()]
    c.executemany("INSERT INTO words(p_id, word, count) values(?,?,?);", wordcount_toex)
    conn.commit()
    conn.close()

def rebuilder():
    pageget.createtables()
    
    pagelisting = os.listdir("./pages")
    pages = []

    for i in pagelisting:
        bupfile = open("./pages/" + i.strip() + "/bupfile", "r", encoding = "utf-8")
        info = bupfile.readlines()
        bupfile.close()
        info = [x.strip() for x in info]
        pages.append(info)

    for i in pages:
        hashy, title, url, bodylen = i[0], i[1], i[2], i[3]
        bodyfile = open("./pages/" + hashy + "/bodycontent", encoding = "utf-8")
        body = bodyfile.read().strip()
        bodyfile.close()

        wordcount = pageget.getwordcount(body)
        inserts(i, wordcount)

def main():
    # Remove corrupted/unwanted database
    listing = os.listdir("./")
    if "psengine.db" in listing:
        print("Do you want to delete and rebuild this database? %s" % os.getcwd() + "/" + "psengine.db")
        os.remove("psengine.db")
    else:
        print("\"psengine.db\" not found. Would you like to rebuild it?")

    resp = input("Press Y|y for yes or any other key for no. ")
    if resp.strip() in ["y", "Y"]:
        print("Database removed. Rebuilding...\n")
        rebuilder()
    else:
        input("Not restoring database. Restarting...\n\n")
