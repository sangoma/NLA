#!/usr/bin/python
# -*- coding: utf-8 -*-
# scrape out the results from the stats-analyzer hack fest!
import sqlite3 as lite
import getopt
import sys
import subprocess

# config
human_file = "human.txt"
machine_file = "machine.txt"

def usage():
    """help function"""
    explanation = "This tool scrapes the Stats-analyzer squlite3 database for\
    calls marked as HUMAN and MACHINE and prints the call-ids in text files for later processing\n"
    print("Usage: db_scrape.py <sqlite3 db file>\n" + explanation)

# get sys args
argv = sys.argv

# parse options
try:
    (optlist, args) = getopt.gnu_getopt(argv[1:], "h:s:", ("help","stats"))

except getopt.GetoptError, exc:
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
    sys.exit(usage())

elif len(args) > 2:
    print("Error: excess args '%s ...'" % args[0])
    sys.exit(usage())

# setup db connection
db = args[0]
con = None

# open database connection
try:
    con = lite.connect(db)

    cur = con.cursor()    
    cur.execute('SELECT SQLITE_VERSION()')

    data = cur.fetchone()
    print("using SQLite version: %s" % data)
    print("scraping db entries...")

    cur.execute('SELECT paraxipcallId FROM processedCpaCall where expectedResults = 1')
    humans = cur.fetchall()

    # print "humans are:\n %s" % humans

    cur.execute('SELECT paraxipcallId FROM processedCpaCall where expectedResults = 2')
    machines = cur.fetchall()

except lite.Error, e:
    print "Error %s:" % e.args[0]
    sys.exit(1)

finally :
    if con:
        con.close()

# write cid files for parsing by audio annotator
print("writing " + human_file + "...")
try:
    f = open(human_file, 'w')
    for entry in humans:
        data = f.write(entry[0] + "\n")
    print(str(data) + " written")
finally:
    f.close()
    del data

print("writing " + machine_file + "...")
try:
    f = open(machine_file, 'w')
    for entry in machines:
        data = f.write(entry[0] + "\n")
    print(str(data) + " written")
finally:
    f.close()
    del data

# subprocess.call("xargs <infile> blah blah blah")
