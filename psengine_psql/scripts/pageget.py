# IMPORTS
import os
import shutil
import html
import requests
import re
import hashlib
import bs4
from bs4 import BeautifulSoup as bs
from bs4.element import Comment
import collections
from collections import Counter as ctr
import psycopg2
import datetime
from datetime import datetime

# Operative functions
def createtables():
    conn = psycopg2.connect(host="127.0.0.1", database="testdb", user="psengine", password="psengine")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pages (
                 p_id SERIAL PRIMARY KEY, 
                 hash VARCHAR(32) NOT NULL,
                 title_url TEXT NOT NULL,
                 bodylen INTEGER NOT NULL);''')
    c.execute('''CREATE TABLE IF NOT EXISTS words (
                 w_id SERIAL PRIMARY KEY,
                 p_id INTEGER REFERENCES pages (p_id),
                 word TEXT NOT NULL,
                 count INTEGER NOT NULL);''')
    c.execute("CREATE OR REPLACE VIEW v_finds AS SELECT word, COUNT(word) AS finds FROM words GROUP BY word;")
    conn.commit()
    conn.close()

def checkurl(url):
    request = ""
    try:
        request = requests.get(url)
    except requests.exceptions.ConnectionError:
        print("===- Page '%s' could not be connected to. Skipping..." % url)
        file = open("invalidurls", "a", encoding = "utf-8")
        file.write(url + "\n")
        file.close()
        return False
    
    if request.status_code != 200:
        print("===- Page '%s' returned a status code of %s. Skipping..." % (url, str(request.status_code)))
        file = open("invalidurls", "a", encoding = "utf-8")
        file.write(url + "\n")
        file.close()
        return False

    return request

def reporskip(c, hashy, url):
    c.execute("SELECT COUNT(*) FROM pages WHERE hash = '%s'" % hashy)
    num = 0
    try:
        num = c.fetchone()[0]
    except:
        num = 0
    if num > 0:
        resp = input("===- Page '%s' has been added to database already. Enter <R> to replace or anything else to skip. " % url)
        if resp.strip() == "R" or resp.strip() == "r":
            c.execute("DELETE FROM pages WHERE hash = '%s';" % hashy) 
            conn.commit()
            shutil.rmtree("pages/%s" % hashy)
        else:
            return False

# Massive thanks to jbochi on StackOverflow fro `tag_visible` and `text_from_html`
# https://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text
#     - Accessed on 15/02/2020
def tag_visible(element):
    if element.parent.name in ['style', 'title', 'script', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

def text_from_html(body):
    soup = bs(body, 'html.parser')
    texts = soup.findAll(text=True)
    visible_texts = filter(tag_visible, texts)  
    return u" ".join(t.strip() for t in visible_texts)

def escapebody(content):
    return(text_from_html(content))

def getwordcount(body):
    wordcount = {}
    words = body.split(" ")
    newwords = words[0:]
    for i in range(2, 5):
        for j in range(0, len(words)):
            if len(words[j:j+i]) == i:
                newwords.append(" ".join(words[j:j+i]))
    words = newwords[0:]
 
    # For each word (and word grouping) strips whitespace and adds it to the 
    #     dictionary if absent or increments its value if present.
    for i in words:
        if i.strip() not in wordcount.keys():
            wordcount[i.strip()] = 1
        else:
            wordcount[i.strip()] = wordcount[i.strip()] + 1 
    
    # Removes oddball non-words
    # TODO: Maybe should check inside every word and split on bad whitespace 
    #       instead of stripping? Then we would remove the issue of odd word
    #       amalgams
    for i in ["", " ", "\^M"]:
        badentry = wordcount.pop(i, None)
    return wordcount

# The div intro tag from StackExchange pages that begins posts
questiondiv = "<div class=\"s-prose js-post-body\" itemprop=\"text\">"

# MAIN BODY
def recpageinfo(url):
    # Getting HTML source and quitting out if there is no page
    request = checkurl(url)
    if request is False:
        return False
    content = request.text

    soup = bs(content, 'html.parser')

    # Getting the title for the given StackExchange page and hashing the title to get a file name
    title = " ".join([tag.text for tag in soup.find_all("title")])
    hashy = str(hashlib.md5(title.encode()).hexdigest())

    # Opens a database connection and cursor used to check if a page has been 
    #     added and asks if you want to replace it; also used later for adding 
    #     page and wordcount information to the database
    conn = psycopg2.connect(host="127.0.0.1", database="testdb", user="psengine", password="psengine")
    c = conn.cursor()

    # Either skips adding a redundant page or deletes the database entries and
    #     and backup folder for it before continuing as normal
    rep = reporskip(c, hashy, url)
    if rep is False:
        return False

    # Creating the folder where the fulltext and bodytext will be stored
    os.mkdir("pages/" + hashy)

    # Creating a file containing the full source HTML
    fullhtml = open("pages/" + str(hashy) + "/" + str(hashy) + ".html", "w+", encoding = "utf-8")
    fullhtml.write(content)
    fullhtml.close()

    # Gets all posts in the StackExchange page by word, lowercases them, and 
    #     and adds them to a single line
    body = escapebody(content)

    # Content written to the bodyfile just in case you need to check it later
    bodyfile = open("pages/" + str(hashy) + "/bodycontent", "a", encoding = "utf-8")
    bodyfile.write(body)
    bodyfile.close()
    bodylen = len(body.split(" "))

    # Gets the words from the bodytext and adds new words to it by getting all 
    #     the sequential pairs, triplets, and quadruplets like what is done 
    #     for the search terms in `pagexp.py`
    wordcount = getwordcount(body)

    # Creating an information backup file
    bupfile = open("pages/" + hashy + "/bupfile", "w", encoding = "utf-8")
    bupfile.write("%s\n%s\n%s\n%s" % (hashy, title, url, str(bodylen)))
    bupfile.close()

    # Inserts into the "pages" table the page info. The pageid is saved for the 
    #     following insert into the words table
    # TODO: Maybe some of this (like hash) isn't needed? But I thought hash was  
    #       used somewhere?.replace("'", "''")
    query = "INSERT INTO pages(hash, title_url, bodylen) values('{0}', '{1}', {2});".format(hashy, title.replace("'", "''") + "||*-*||" + url.replace("'", "''"), bodylen)
    c.execute(query)
    conn.commit()
    pageid = c.lastrowid + 1
    conn.commit()
   
    # Creates a tuple with the pageid and the keys and values from the 
    #     `wordcount`, uses them to insert into the "words" table, commits our 
    #     changes, and closes the connection.
    dt = str(datetime.utcnow()).replace(" ", ":")
    queryfile = open("queryfile_%s" % dt, "w", encoding = "utf-8")
    wordcount_toex = [(pageid, k, v) for k, v in wordcount.items()]
    for wctx in wordcount_toex:
        query = "{0},\"{1}\",{2}\n".format(wctx[0], wctx[1].replace("\"", ""), wctx[2])
        queryfile.write(query)
    queryfile.close()

    queryfile = open("queryfile_%s" % dt, "r", encoding = "utf-8")
    c.copy_expert('COPY words(p_id, word, count) FROM STDIN WITH (FORMAT CSV)', queryfile)
    queryfile.close()
    os.remove("queryfile_%s" % dt)

    conn.commit()
    conn.close()

    return True

# It's called "main", but it's sorta just another function. It's not like 
#     anyone is supposed to run this on its own from the command line...
# TODO: Call it something else?
def main(intype, name):
    # Used so that `psengine.py" prints the accurate success messages
    URLSADDED = 0

    # Checking if the "pages" directory exists and creating if not
    if not os.path.isdir("pages"):
       os.mkdir("pages")

    # Opens a connection to the database "psengine.db" and creates our 
    #     tables "pages" and "words" if they don't exist and commits these 
    #     changes
    #     Also reates a view that will show the amount of pages each 
    #     recorded word was found on. I.E., if you have 1000 pages, you might 
    #     expect the "finds" number number for the word "the" to be 1000 
    #     because the word is common. BTW, the changes are commited and the
    #     connection is closed.
    createtables()
    
    # Runs `recpageinfo` on just a single URL
    if intype == "url":
        added = recpageinfo(url)
        if added is True: URLSADDED += 1

    # Opens the source list file and runs `recpageinfo` for each URL found
    if intype == "file":
        # Opening the pagelist file and running `recpageinfo` on each
        file = open(name, "r", encoding = "utf-8")
        files = file.readlines()
        file.close()
        for i in files:
            added = recpageinfo(i.strip())
            if added is True:
                URLSADDED += 1
    
    return URLSADDED
