#!/usr/bin/env python3
# a tool for analyzing NCA logs - NCA Log Analyzer
# this is the front end script which should be run on a cpa-stats package

# TODO:
# -implement stats computation
# -implement xml parser
# -implement signalling parser
# -implement wav file plotter
# -check for ipython and boot if available, else print stats?

# Ideas
# done - create a seperate class LogsPackage
# - os.walk and build a dict of logs for each entry

import sys
import os
import getopt
import callset
import grapher
import csv
import subprocess

# some important field strings
cid            = 'Netborder Call-id'
phone_num      = 'Phone Number'
nca_result     = 'NCA Engine Result'
det_nca_result = 'Detailed Cpd Result'

def usage():
    """help function"""
    print("This tool parses an NCA log package, provides a disposition "
          "summary and conducts log segmentation by results classification.\n"
          "It relies heavily on ipython for practical use to "
          "efficiently analyze a log set\n\n"
          "Usage: ./nla.py <cpa-stats.csv> <call-logs directory name>\n")

def scan_logs(re_literal, logdir='./', method='find'):
    if method == 'find':
        found = subprocess.check_output(["find", logdir, "-regex", "^.*" + re_literal + ".*"])
        paths = found.splitlines()
        return paths

    elif method == 'walk':
        #TODO: os.walk method
        print("this would normally do an os.walk")

    else:
        print("no other logs scanning method currentlyl exists!")

class LogPaths(object):

    def __init__(self, logs_list):
        self.wavs = []
        self.logs = []

        for path in logs_list:
            # assign properties by extension (note 'byte' format)
            filename, extension = os.path.splitext(path)
            if extension == b".log":
                self.logs.append(path)

            elif extension == b".xml":
                self.xml = path

            elif extension == b'.wav':
                self.wavs.append(path)

        self.wavs.sort()

class LogPackage(object):
    def __init__(self, csv_file, logs_dir):

        # print("assigning callset id: '" + str(callset_id) + "'")
        # self._id = callset_id
        self._field_mask = []   # normally map this over the 
        self.mask_indices = []

        # counters
        self.num_cid_unfound = 0

        # "members" of this call set
        self.fields = {}
        self.entries = []
        self.log_paths = {}
        self.entries = []
        self.failed_entries = []

        # compile data
        self.load_logs(csv_file, logs_dir)


    def load_logs(self, csv_file, logs_dir):
        """ load a new log package into memory """

        # load csv file and populate useful properties
        try:
            print("opening csv file: '", csv_file, "'")
            with open(csv_file) as csv_buffer:

                # TODO: add a csv sniffer here to determine an excell dialect?
                csv_reader = csv.reader(csv_buffer)

                # if LogPackage is not populated with data, gather template info
                if len(self.entries) == 0:
                    self.title = next(csv_reader)    # first line should be the title
                    self.fields = next(csv_reader)   # second line should be the field names
                    self.field_widths = [0 for i in self.fields]

                    # gather user friendly fields (i.e. fields worth reading on the CLI)
                    self.cid_index = self.fields.index(cid)
                    self.phone_index = self.fields.index(phone_num)
                    self.result_index = self.fields.index(nca_result)
                    self.detail_result_index = self.fields.index(det_nca_result)

                    # make a field mask
                    self.mask_indices = [self.cid_index, self.result_index, self.detail_result_index]
                    # self._field_mask = field_select(self.mask_indices)

                    # find the index of the field to use as the disjoint union tag
                    # self._subset_field_index = self.fields.index(self.subset_field_tag)

                    # create a list of indices
                    self.width = len(self.fields)

                # compile a list of csv/call entries
                print("compiling logs index...")
                for entry in csv_reader:
                    # self._line_num = csv_reader.line_num
                    try:
                        # search for log files using call-id field
                        logs = scan_logs(entry[self.cid_index])

                        if len(logs) == 0:
                            print("WARNING no log files found for cid :",entry[self.cid_index])
                            self.num_cid_unfound += 1
                            self.failed_entries.append(entry)

                        else:
                            self.log_paths[entry[self.cid_index]] = LogPaths(logs)

                    except subprocess.CalledProcessError as e:
                        print("scanning logs failed with output: " + e.output)

                    # if all else is good add the entry to our db
                    self.entries.append(entry)

        except csv.Error as err:
            print('file %s, line %d: %s' % (csv_buffer, self._reader.line_num, err))
            print("Error:", exc)
            sys.exit(1)

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

else:
    csv_file = args[0]
    logs_dir = args[1]

# compile logs package into memory
logs = LogPackage(csv_file, logs_dir)

# create a callset interface
fac, cs  = callset.new_callset(csv_file, logs_dir)
