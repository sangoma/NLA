#!/usr/bin/python
# -*- coding: utf-8 -*-
# scrape out the results from the stats-analyzer hack fest!
import sqlite3 as lite
import getopt
import sys

# get sys args
argv = sys.argv

def usage():
    """help function"""
    explanation = "This tool scrapes the Stats-analyzer squlite3 database for calls marked as HUMAN and MACHINE and prints the call-ids in text files for later processing\n"
    print("Usage: db_scrape.py <sqlite3 db file>\n" + explanation)

# parse options
try:
    (optlist, args) = getopt.gnu_getopt(argv[1:], "h:s:", ("help","stats"))

except getopt.GetoptError as exc:
    print("Error:" +  exc)
    sys.exit(usage())

for opt in optlist:

    if opt[0] == "-h" or opt[0] == "--help":
        print("currently no help function!")
        usage()
        sys.exit(0)

    if opt[0] == "-s" or opt[0] == "--stats":
        showstats = True
        print("currently no statistics!")
        usage()
        continue

if len(args) == 0:
    sys.exit("Error: You must specify a sqlite3 database file as your first argument!")

elif len(args) > 2:
    print("Error: excess args '%s ...'" % args[0])
    sys.exit(usage())

db = args[0]
con = lite.connect(db)

# open database connection
with con:
    cur = con.cursor()    
    cur.execute('SELECT SQLITE_VERSION()')

    data = cur.fetchone()
    print "SQLite version: %s" % data                
    print("scraping db entries...")

    cur.execute('SELECT paraxipcallId FROM processedCpaCall where expectedResults = 1')
    humans = cur.fetchall()

    # print "humans are:\n %s" % humans

    cur.execute('SELECT paraxipcallId FROM processedCpaCall where expectedResults = 2')
    machines = cur.fetchall()

with open("human.txt", "w") as f:
    for entry in humans:
        data = f.write()
    # cur.execute('SELECT * FROM processedCpaCall')
    # a = cur.fetchall()
    # print "all are:\n %s" % a
    
# except lite.Error, e:

#     print "Error %s:" % e.args[0]
#     sys.exit(1)

# finally:
    # if con:
    #     con.close()
