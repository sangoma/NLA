#!/usr/bin/env python3
# a tool for analyzing NCA logs - NCA Log Analyzer
# front end script which should be run on a cpa-stats package

import sys, getopt
from imp import reload

# custom modules
import callset

def usage():
    """help function"""
    print('''This tool parses a customer provided NCA log package which should contain:
- cpa-stats.csv file
- call-logs/ directory

This tool will generate the following packages in new directories when provided an unprocessed call-log set:
- NCA stats analyser package (a web based windows tool used for annotation)
- logs package prepped for offline NCA benchmark tool with audio recordings converted to lpcm

Notes:
  This tool relies heavily on ipython in combination with the 'callset' module
  for practical use to efficiently analyze a log set.
  If you don't have ipython installed then get it installed!
  The tool was scratched together by Tyler Goodlet mostly in his free time while learning python3.

Usage: nla.py <cpa-stats.csv> <logs directory>\n''')

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
        print("requested csv statistics summary ONLY!\n"
              "calling handy gawk script...\n")
        # TODO: actually call the gawk script from here...
        continue
    if opt[0] == "--skip-package-gen":
        gen_lin = False
        gen_sa  = False
        continue

if len(args) < 2:
    print("E: not enough arguments!\n")
    sys.exit(usage())

elif len(args) > 2:
    print("Error: excess args '%s ...'" % args[0])
    sys.exit(usage())
else:
    csv_file = args[0]
    logs_dir = args[1]

# field VALUE used to 'segment' sub-callsets in in the object interface
disjoin_field  = 'NCA Engine Result'

# compile logs package into memory (WARNING this creates new packages with duplicate data)
logs = callset.LogPackage(csv_file, logs_dir)

cs = None
def reload_cs(cs=cs):
    # build a callset interface
    if cs is not None:
        del cs
    return callset.new_callset(logs, disjoin_field)

cs = reload_cs()

print("\nattempting to start ipython shell...\n")
try: from IPython import embed
except ImportError as imperr : print(imperr)
# this call anywhere in your program will start IPython
embed()

# HINT: to create a new subset try something like,
# subset = cs.factory.new_subset(parent, filter_function)
# where the filter_function is something like -> filter_by_field(3, gt, 500)
# here 3 is field index, gt ('greater then') is a comparison function, 500 is a const to compare against
# see callset.py for more details
