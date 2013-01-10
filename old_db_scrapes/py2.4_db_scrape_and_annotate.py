#!/usr/bin/python
# -*- coding: utf-8 -*-

# Tyler Goodlet tgoodlet@sangoma.com -- initial version
# scrape out the results from the stats-analyzer hack fest,
# annotate the log files, and then finally build a list of logs 
# for the benchmarking tool to process

# Files required by this script
# - a filtered logs set
# - a set of sqlite database files from the stats-analyzer (*.s3db, *.callset)

import sqlite as lite
import getopt
import sys
from subprocess import *
import csv

# output files
human_file = "human.audioset"
machine_file = "machine.audioset"
bm_test_list = "test.audioset"

# annotator path
annotator = "/mnt/iscsi/wc/nca-2.0-maint/bin/netborder_x86_64-linux_gcc34/netborder-add-audio-annotation"

def usage():
    """help function"""
    explanation = "This tool scrapes the Stats-analyzer squlite3 database for \
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

if con:
	con.close()

# write cid files for parsing by audio annotator
print("writing " + human_file + "...")
try:
    f = open(human_file, 'w')
    for entry in humans:
		output = Popen(["find", "./", "-regex", "^.*" + entry[0] + ".*wav.*"], stdout=PIPE).communicate()[0]
		f.write(output)

finally:
    f.close()

print("writing " + machine_file + "...")
try:
    f = open(machine_file, 'w')
    for entry in machines:
		output = Popen(["find", "./", "-regex", "^.*" + entry[0] + ".*wav.*"], stdout=PIPE).communicate()[0]
		f.write(output)

finally:
    f.close()

# annotate files using 1000 second start/end regions
print("start annotating " + human_file + "...")
retcode = call(["xargs", "--replace", "-a", human_file, annotator, "{}", "CPA_HUMAN", "1000", "1000"])

print("start annotating " + machine_file + "...")
retcode = call(["xargs", "--replace", "-a", machine_file, annotator, "{}", "CPA_MACHINE", "1000", "1000"])

sys.exit()

# parse the csv file and generate the test.audioset file
csv_file = args[1]
csv_buffer = open(csv_file)
reader = csv.reader(csv_buffer) # default delimiter=','

# first line should be the title
title = reader.next()
# second line should be the field names
fields = reader.next()

f = open(bm_test_list, 'w')
for row in reader:
	output = Popen(["find", "./", "-regex", "^.*" + row[0] + ".*wav.*"], stdout=PIPE).communicate()[0]
	f.write(output)
