#!/usr/bin/env python3
# a tool for analyzing NCA logs - NCA Log Analyzer
# this is the front end script which should be run on a cpa-stats package

# TODO:
# -implement front end logfile segmenter
# -implement stats computation
# -implement xml parser
# -implement signalling parser
# -implement wav file plotter

import sys
import getopt
from callset import *

def usage():
    """help function"""
    print("This tool parses an NCA log package, provides a disposition "
          "summary and conducts log segmentation by classification.\n"
          "It relies heavily on ipython for practical use to "
          "efficiently analyze a log set\n\n"
          "Usage: ./nla.py <cpa-stats.csv> <call-logs directory name>\n")

# parse the cpa-stats.csv file
# def main(argv):
# main(sys.argv)
"""main entry point and options parsing"""
argv = sys.argv
try:
    (optlist, args) = getopt.gnu_getopt(argv[1:], "h:s:", ("help","stats"))
except getopt.GetoptError as exc:
    print("Error:" +  exc)
    sys.exit(usage())

for opt in optlist:
    if opt[0] == "-h" or opt[0] == "--help":
        usage()
        sys.exit(0)
    if opt[0] == "-s" or opt[0] == "--stats":
        showstats = True
        print("enabled statistics!")
        continue

if len(args) < 2:
    print("Error: not enough arguments!\n")
    sys.exit(usage())

elif len(args) > 2:
    print("Error: excess args '%s ...'" % args[0])
    sys.exit(usage())

# create a callset interface
cs = CallSet(args[0], args[1], "base")

# s = 0
# for row in cs.reader:
    # s += 1
# print("there are " + str(s) + " records in the stats file")
