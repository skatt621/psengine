# IMPORTS
import os
import psycopg2

from . import pageget

def getpagelist():
#    conn = sqlite3.connect('psengine.db')
    conn = psycopg2.connect(host="127.0.0.1", database="testdb", user="psengine", password="psengine")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM pages")
    num = c.fetchone()[0]
    conn.close()
    return num

def inserts(info, wordcount):
    hashy, title, url, bodylen = info[0], info[1], info[2], info[3]
#    conn = sqlite3.connect('psengine.db')
    conn = psycopg2.connect(host="127.0.0.1", database="testdb", user="psengine", password="psengine")
    c = conn.cursor()
    c.execute("INSERT INTO pages(hash, title_url, bodylen) values('%s', '%s', %s);" % (hashy, title + "||*-*||" + url, bodylen))
    conn.commit()
    pageid = c.lastrowid
   
    wordcount_toex = [(pageid, k, v) for k, v in wordcount.items()]
    for wctx in wordcount_toex:
        c.execute("INSERT INTO words(p_id, word, count) values({0}, '{1}', {2});".format(wctx[0], wctx[1], wctx[2]))
        conn.commit();

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
        print("'psengine.db' not found. Would you like to rebuild it?")

    resp = input("Press Y|y for yes or any other key for no. ")
    if resp.strip() in ["y", "Y"]:
        print("Database removed. Rebuilding...\n")
        rebuilder()
    else:
        input("Not restoring database. Restarting...\n\n")
