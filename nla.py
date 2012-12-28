#!/usr/bin/python2
# a tool for analyzing NCA logs - NCA Log Analyzer
# this is the front end tool which should be run on a cpa-stats package

# TODO: 
# -implement front end logfile segmenter
# -implement stats computation
# -implement xml parser
# -implement signalling parser
# -implement wav file plotter

import sys
import getopt
from callset import CallSet

def usage():
    """help function"""
    explanation = "This tool parse the NCE stats file for and provides a disposition summary and conducts log segmentation by classification\n"
    print("Usage: ./nla.py <cpa-stats.csv>\n" + explanation)
      
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

if len(args) == 0:
    sys.exit("Error: You must specify a cpa-stats.csv file as your first argument!")

elif len(args) > 2:
    print("Error: excess args '%s ...'" % args[0])
    sys.exit(usage())

# create a callset interface
cs = CallSet(args[0], "bt")

# s = 0
# for row in cs.reader:
    # s += 1
# print("there are " + str(s) + " records in the stats file")

