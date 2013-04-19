#!/usr/bin/python
# -*- coding: utf-8 -*-

# Tyler Goodlet tgoodlet@sangoma.com -- initial version
# scrape out the results from the stats-analyzer hack fest,
# annotate the log files, and then finally build a list of logs 
# for the benchmarking tool to process

# Files required by this script
# - a filtered logs set
# - a set of sqlite database files from the stats-analyzer (*.s3db, *.callset)

import getopt
import sys
from subprocess import *
import os, glob

# input files
human_file = "human.audioset"
machine_file = "machine.audioset"
fax_file = "fax.audioset"

# output concatenated list
bm_test_list = "test.audioset"

# tool paths
annotator = os.path.expandvars("$PARAXIP/bin/netborder_x86_64-linux_gcc34/netborder-add-audio-annotation")
deannotator = os.path.expandvars("$PARAXIP/bin/netborder_x86_64-linux_gcc34/netborder-clear-audio-annotation")

def usage():
    """help function"""
# TODO: make this not shit!
    print("\nUsage: cd <directory with audioset files and logs>; /path/to/annotate.py ./\n"
    "This tool annotates wave files as HUMAN and MACHINE as instructed in human.audioset type files\n")

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

elif len(args) > 1:
    print("Error: excess args '%s ...'" % args[0])
    sys.exit(usage())
else:
	package_dir = os.path.abspath(args[0])

human_file = os.path.join(package_dir, human_file)
machine_file = os.path.join(package_dir, machine_file)
fax_file = os.path.join(package_dir, fax_file)

output_list = os.path.join(package_dir, bm_test_list)

bash_command = "cat " + human_file + " " + machine_file + " " + fax_file + " > " +  output_list
print("generating output file -> " + output_list)
os.system(bash_command)
#output = Popen(["cat", human_file, machine_file, fax_file, '>', output_list], stdout=PIPE).communicate()[0]

# TODO: use the annotation detection tool to check if the files have
# already been annotated first so that we don't do it twice!
h_annon_tag = "CPA_HUMAN"
m_annon_tag = "CPA_MACHINE"
f_annon_tag = "CPA_FAX"

#retcode = call(["xargs", "--replace", "-a", human_file, de-annotator, 

# remove annotations on all wav files (THIS TOOL DOESN'T WORK!?)
print("\nremoving existing annontations in all wav files")
retcode = call([deannotator,
                "--regex", 
                h_annon_tag + ".*" + m_annon_tag + ".*" + f_annon_tag]
                + glob.glob(os.path.join(package_dir, '*wav')))

#./bin/netborder_x86_64-linux_gcc34/netborder-clear-audio-annotation --regex 'HUMAN' ~/nca_tuning_workspace/auto_tuning/example_callset_to_annotate/*wav

# annotate files using 1000 second start/end regions
print("\nstart annotating " + human_file + "...")
retcode = call(["xargs", "--replace", "-a", human_file, annotator, "{}", "CPA_HUMAN", "1000", "1000"])

print("\nstart annotating " + machine_file + "...")
retcode = call(["xargs", "--replace", "-a", machine_file, annotator, "{}", "CPA_MACHINE", "1000", "1000"])

print("\nstart annotating " + fax_file + "...")
retcode = call(["xargs", "--replace", "-a", fax_file, annotator, "{}", "CPA_FAX", "1000", "1000"])

sys.exit()
