#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: tabstop=4 softtabstop=4 shiftwidth=4 textwidth=80 smarttab expandtab
#
# Tyler Goodlet tgoodlet@sangoma.com -- initial version
# scrape out the results from the stats-analyzer hack fest,
# annotate the log files (now with the tool on the nca build machine)
# and then finally build a list of logs for the benchmarking tool to process

# Files required by this script
# - a filtered logs set
# - a set of sqlite database files from the stats-analyzer (*.s3db, *.callset)

# Comments:
# welcome to bs castle where we break up a simple process into as
# many scripts as possible because for some reason "people" think it's
# a good idea to build software on CentOS 5.7 where sox does not yet
# have the 'pad' option thus causing me to go nearly insane as I get 
# closer and closer to the cliff's edge...

import os
import sys
import getopt
import shutil
from subprocess import *
import sqlite3 as lite

def usage():
    """help function"""
    print("\nUsage:" + sys.argv[0] + " <sqlite3 db file (*.callset)> <logs dir to find wav and xml files>\n\n"
         "This tool scrapes the Stats-analyzer sqlite3 database for calls marked as HUMAN, MACHINE and FAX.\n"
         "It prints the call-ids in text files for later processing by the nca annotation tool.\n")

# recursively remove a dir tree
def remove_dir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)

# write the '.audioset' files for parsing by audio annotator
def gen_annotate_package(filename, result_class, query_list):
#TODO: change opens to use 'with' statements

    print("writing " + filename)
    try:
        # f = open('/'.join([search_dir, human_file]), 'w')
        f = open(filename, 'w')
        for entry in query_list:

            # search logs for files corresponding to cid scraped from db
            found = Popen(["find", search_dir, "-regex", "^.*" + entry[0] + ".*"], stdout=PIPE).communicate()[0]

            # split into a list
            logs = found.split('\n')

            # loop through the files found from the logs with that cid
            for entry in logs:

                filename, extension = os.path.splitext(entry)
                name = os.path.basename(entry)

                if result_class == "human":
                    # flag the padded files
                    name = "zeropad-" + name

                path_to_file = os.path.join(package_dir, name)

                # if it's a wave file
                if extension == ".wav" :

                    if result_class == "human":
                        # pad the human wave files with 3 seconds of silence
                        # and output to package dir
                        # print("padding : " + name)
                        retcode = call(["sox", entry, path_to_file, "pad", "0", "3"]) 

                    else:

                        shutil.copyfile(entry, path_to_file) 

                    # write the xargs parsible file
                    f.write(path_to_file + "\n")

                # if it's a log file
                elif extension:

                    shutil.copyfile(entry, path_to_file) 

                else:
                    # skip the weird blank entry in list 'logs' TODO: fix this
                    next

    finally:
        f.close()

# Start Of Script #
##################

# get sys args
argv = sys.argv

# parse options
try:
    (optlist, args) = getopt.gnu_getopt(argv[1:], "h:s:", ("help","stats"))

except getopt.GetoptError, exc:
    print("Error:" +  str(exc))
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

elif len(args) < 2:
    sys.exit(usage())

elif len(args) > 2:
    print("Error: excess args '%s ...'" % args[0])
    sys.exit(usage())

# query for package name
print("Enter the name of the new package you'd like to generate (HINT: it's the dir name)")
package_dir = raw_input()

# output files
bm_test_list = "test.audioset"
human_file = os.path.join(package_dir, 'human.audioset')
machine_file = os.path.join(package_dir,"machine.audioset")
fax_file = os.path.join(package_dir, "fax.audioset")

# get the db and package directory
db = args[0]
search_dir = args[1]

# setup db connection
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

    cur.execute('SELECT paraxipcallId FROM processedCpaCall where expectedResults = 2')
    machines = cur.fetchall()

    #TODO: should really be 'where name = FAX'
    cur.execute('SELECT paraxipcallId FROM processedCpaCall where expectedResults = 4')
    fax = cur.fetchall()

except lite.Error, e:
    print "Error %s:" % e.args[0]
    sys.exit(1)

if con:
    con.close()


# make sure output package dir exists
if not os.path.exists(package_dir):
    print("creating output package dir: " + package_dir)
    os.makedirs(package_dir)

gen_annotate_package(human_file, "human", humans)
gen_annotate_package(machine_file, "machine", machines)
gen_annotate_package(fax_file, "fax", fax)

print("\nall listing files are located in new package prepped for auto-annotation -> '" + package_dir + "'")

sys.exit()

# # annotate files using 1000 second start/end regions
# print("start annotating " + human_file + "...")
# retcode = call(["xargs", "--replace", "-a", human_file, annotator, "{}", "CPA_HUMAN", "1000", "1000"])

# print("start annotating " + machine_file + "...")
# retcode = call(["xargs", "--replace", "-a", machine_file, annotator, "{}", "CPA_MACHINE", "1000", "1000"])

# sys.exit()

# # parse the csv file and generate the test.audioset file
# csv_file = args[1]
# csv_buffer = open(csv_file)
# reader = csv.reader(csv_buffer) # default delimiter=','

# # first line should be the title
# title = reader.next()
# # second line should be the field names
# fields = reader.next()

# f = open(bm_test_list, 'w')
# for row in reader:
# 	output = Popen(["find", "./", "-regex", "^.*" + row[0] + ".*wav.*"], stdout=PIPE).communicate()[0]
# 	f.write(output)
