# IMPORTS
import hashlib
import psycopg2

def searcher():
    # SEARCH BODY - gets done once, but is looped in `psengine.py`
    # Lists of matchscore objects: lists that contain a URL and a search score
    #     for a given term. Each list is for something different:
    #       - url_matchscore is for raw matchscore (calculation below)
    #       - url_titlescore is for how well the terms match the page title
    #       - url_cnsecscore is a rating for how many consecutive term 
    #           groupings are found in a given URL
 
    url_matchscore = []
    url_titlescore = []
    url_cnsecscore = []

    # Opens the connection to the database to be used throughout `searcher()`
#    conn = sqlite3.connect('psengine.db')
    conn = psycopg2.connect(host="127.0.0.1", database="testdb", user="psengine", password="psengine")
    c = conn.cursor()
    
    # Uncomment these lines if you want to try setting Pragmas
    # c.execute("PRAGMA cache_size=-2000;")
    
    # Getting search terms
    print("")
    terms = input("What is/are your search terms (delimit with spaces)? ")
    print("")
    terms = [x.lower() for x in terms.split(" ")]
    
    # Getting each term into a list along with each pair/triplet/quadruplet
    newterms = terms[0:]
    for i in range(2, 5):
        for j in range(0, len(terms)):
            if len(terms[j:j+i]) == i:
                newterms.append(" ".join(terms[j:j+i]))
    
    # Removing duplicates in terms
    terms = set(newterms)
    
    # Gets the number of articles each term/term grouping is found in and 
    #     records them in a dictionary for the search algo to use later
    commonalities = {}
    for i in terms:
        c.execute("SELECT sum(finds) FROM v_finds WHERE word LIKE '%s';" % i.replace("'", "''"))
        num = c.fetchone()[0]
        if num is not None:
            commonalities[i] = int(num)
        else:
            commonalities[i] = 0

    # Getting the list of pages recorded
    c.execute("SELECT * FROM pages")
    pages = c.fetchall()

    # Loops through each given page
    for page in pages:
        # Getting the title and URL from the aptly named "page.title_url"
        #     column and turns the title into a list of its words and its 
        #     2x/3x/4x consecutive groupings
        title_url = page[2].split("||*-*||")
        title, url = title_url[0], title_url[1]
        title = [x.lower() for x in title.split(" ")]
        newtitle = title[0:]
        for i in range(2, 5):
            for j in range(0, len(title)):
                if len(title[j:j+i]) == i:
                    newtitle.append(" ".join(title[j:j+i]))
        title = set(newtitle)

        # Used to store the wordcounts for the given page
        wordcount = {}

        # Gets the words for the given page from the "words" table
        c.execute("SELECT word, count FROM words WHERE p_id = %s" % page[0])
        words = c.fetchall()
   
        # Populates the dictionary
        for i in words:
            wordcount[i[0]] = i[1]

        # The rating values for each type of page ranking
        matchscore = 0
        titlescore = 0
        cnsecscore = 0

        
        # A downranking modifier used to adjust the matchscore for abnormally
        #     large pages
        # TODO: Maybe we should emphasize large pages somehow? There is more 
        #       activity on them, after all.
        pagelength = 1/(int(page[3]) + 1)

        # Loops through the terms/term groupings
        for term in terms:
            # A downranking modifier used to adjust the matchscore for 
            #     abnormally prevalent words
            commonality = 1/(commonalities[term] + 1)
            # Loops through the wordcount dictionary and sets the match and 
            #     consecutive scores
            for word in wordcount.keys():
                if term == word or term in word or word in term:
                    matchscore += wordcount[word] * commonality * pagelength
                    cnsecscore += i.count(" ")
        
        # Checks the terms/groupings that are the same between the term and 
        #     title and uses that to set the title score
        titlescore = len(terms.intersection(title))

        # Appends the pages rank to the appropriate lists
        # TODO: Remove the final element. There were more-or-less for testing
        url_matchscore.append([url, matchscore, "match"])
        url_titlescore.append([url, titlescore, "title"])
        url_cnsecscore.append([url, cnsecscore, "cnsecscore"])

    # Closes the database connection
    conn.close()

    # Sorts each result list by the second element, the rank, so the highest 
    #     rank is at the top
    hi_matchscore = sorted(url_matchscore, key = lambda x: (-x[1], x[0]))
    hi_titlescore = sorted(url_titlescore, key = lambda x: (-x[1], x[0]))
    hi_cnsecscore = sorted(url_cnsecscore, key = lambda x: (-x[1], x[0]))

    # The entire top list that gets calculated
    # TODO: Can get large. Maybe we should split processing?
    top = []

    # A list of hashes that shows which pages have been shown already; used in 
    #     entriesleft loop
    hashes = []

    # Gets our lists iterable, sets the number of elements we want from each 
    #     (six, four, and three, respectively), and sets `entriesleft` to 
    #     CONSUME each list. Change these to change the order results are 
    #     taken from the lists or the number of results to take from each
    # TODO: Wasn't this in a callable function?
    listolist = [hi_matchscore, hi_titlescore, hi_cnsecscore]
    listonums = [6, 4, 3]
    entriesleft = sum([len(x) for x in listolist])

    # Loops until all lists in `listolist` are empty
    while entriesleft != 0:
        for i in range(0, len(listolist)):
            for j in range(0, listonums[i]):
                try:
                    # Takes the topmost element from the given list by 
                    #     removing it and sets up a hash on the URL to make 
                    #     sure we don't append an already displayed URL
                    pick = listolist[i].pop(0)
                    hashy = (hashlib.md5(pick[0].encode()).hexdigest())
                    if hashy not in hashes:
                        top.append(pick)
                        entriesleft -= 1
                        hashes.append(hashy)
                except IndexError:
                    # We need to throw this error and zero out the `listonums`
                    #     entry so that the loop doesn't try to get elements
                    #     from the list that just emptied out
                    listonums[i] = 0
                    continue
        # If we're lucky and we empty out each list at the same time, ends Mr. 
        #     Bones's Wild Ride TM
        if sum(listonums) == 0:
            entriesleft = 0

    # This is used for displaying our results in an ordered list
    ind = 1
    
    # Loops until the user inputs <Ctrl-C> or <Enter>
    # TODO: Check if the above is true
    while True:
        listnum = 0

        # Sets the number of displayed results to 10 if the length of the 
        #     remaining results list is >= 10
        # TODO: This is hardcoded and should be changeable :P
        if len(top) >= 10:
            listnum = 10

        # Sets the number of displayed results to the length of the remaining 
        #     results list if its length is < 10 but > 0
        # TODO: Ditto
        elif len(top) < 10 and len(top) > 10:
            listnum = len(top)

        # Runs if there are no results left and displays a different message 
        #     based on if NO results were returned or if there WERE results, 
        #     but we've displayed them all
        # TODO: TBF check if this all works and make <Ctrl-C> not completely 
        #       quit out
        else:
            if ind == 1: 
                input("No results found. Press <Enter> or <Ctrl-C> to restart search.\n")
            else:
                input("End of results. Press <Enter> or <Ctrl-C> to restart search.\n")
            break

        # Prints our pretty results 
        for i in range(0, listnum):
            # Gets the info to display and removes it from the remaining reults 
            #     before displaying, incrementing the ordered list variable, 
            entry = top.pop(0)
            print("#{0:<3} {1}".format(str(ind)+":".strip(), entry[0]).strip())
            #print("#{0:<3} {1}\n\t{2} score: {3}".format(str(ind)+":", entry[0], entry[2], entry[1]))
            ind += 1

        # Displays the: "Or are you thirsty for more?" message
        input("Press <Enter> to see more results. Press <Ctrl-C> to restart search.\n\n")
