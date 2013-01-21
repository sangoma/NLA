#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# vim: tabstop=4 softtabstop=4 shiftwidth=4 textwidth=80 smarttab expandtab
import sys, os, shutil, subprocess
import getopt
import csv

# package names
stats_anal_package = "./sa_package"
filtered_logs_package = "./filtered_logs_set"
zipfile = "stats_analyzer_package.zip"

# to remove in the wav files for sa package
suffix = '.analyzer-engine.0.0'

# make sure output package dir exists
def check_dir(d):
    if not os.path.exists(d):
        print("creating output package dir: " + d)
        os.makedirs(d)
    else:
        print("WARNING " + d + " exists....overwriting")

check_dir(filtered_logs_package)
check_dir(stats_anal_package)

# Start Of Script #
##################

# get sys args
argv = sys.argv

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
    sys.exit(usage())

elif len(args) < 2:
    sys.exit(usage())

elif len(args) > 2:
    print("Error: excess args '%s ...'" % args[0])
    sys.exit(usage())

# get the csv and package directory
csv_file = args[0]
search_dir = args[1]

# open csv and start gathering logs
print("opening csv file: '" + csv_file + "'\n")

with open(csv_file) as csv_buffer:

    reader = csv.reader(csv_buffer)
    title = next(reader)
    fields = next(reader)
    length = 0
    wavcount = 0

    # each row in the csv
    for row in reader:
        length += 1
        # TODO: replace this with os.walk
        # search logs for files corresponding to cid scraped from db
        found = subprocess.Popen(["find", search_dir, "-regex", "^.*" + row[0] + ".*"], stdout=subprocess.PIPE).communicate()[0]

        # split into list of files
        files = found.split("\n")

        wavs = []
        logs = []

        # partition into wav files and logs
        for entry in files:

            filename, extension = os.path.splitext(entry)
            name = os.path.basename(entry)

            if extension == ".wav":
                wavs.append(entry)

            # if it's a log file
            elif extension:
                logs.append(entry)

            else:
                # skip the weird blank entry in list 'logs' TODO: fix this
                continue

        if len(wavs) == 0:
            print("NO WAV FILES FOUND!...skipping call: '" + row[0] +"'")
            continue
        else:
            wavcount += 1
            # sort in place
            wavs.sort()

            # remove stats analyzer troublesome suffix
            sa_wavname = os.path.basename(wavs[0].replace(suffix, ""))
            combine_flag = []

            if len(wavs) > 1:
                print("concatenating " + " ".join(wavs))
                combine_flag = ["--combine", "concatenate"]

            sa_path_to_file = '/'.join([stats_anal_package, sa_wavname])
            retcode = subprocess.call(["sox"] + combine_flag + wavs + [sa_path_to_file])

            # convert to linear for regular log set
            path_to_file = '/'.join([filtered_logs_package, os.path.basename(wavs[0])])
            retcode = subprocess.call(["sox"] + combine_flag + wavs + ["-b", "16", "-e", "signed", path_to_file])


        for entry in logs:
            shutil.copy(entry, stats_anal_package)
            shutil.copy(entry, filtered_logs_package)

# copy csv to each package
shutil.copy(csv_file, stats_anal_package)
shutil.copy(csv_file, filtered_logs_package)

print("")
print(str(length) + " call ids were parsed from " + csv_file)
print(str(wavcount) + " wave files were actually found in '" + search_dir + "'")
print("")

print("zipping up " + stats_anal_package + "...")
# os.chdir(stats_anal_package)
with open(os.devnull, "w") as fnull:
        retcode = subprocess.call(["zip", "-r", "", stats_anal_package], stdout = fnull)

print("New stats-analyzer package is => " + stats_anal_package + " and " + zipfile)
print("New generic package is => " + filtered_logs_package)
print("done.")
