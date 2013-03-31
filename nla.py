#!/usr/bin/env python3
# a tool for analyzing NCA logs - NCA Log Analyzer
# this is the front end script which should be run on a cpa-stats package

# TODO:
# -implement stats computation
# -implement xml parser
# -implement signalling parser
# -implement wav file plotter
# -check for ipython and boot if available, else print stats?
# -create a path index to quickly parse once nla front end has converted a package
# -ask user if they would like to verify path index

# Ideas
# done - create a seperate class LogsPackage
# - os.walk and build a dict of logs for each entry

from imp import reload

import sys, os, getopt, subprocess
import xml.etree.ElementTree as ET
import csv

# custom modules
import callset

# some important field strings
cid_f          = 'Netborder Call-id'
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
        try:
            found = subprocess.check_output(["find", logdir, "-regex", "^.*" + re_literal + ".*"])
            paths = found.splitlines()
            return paths

        except subprocess.CalledProcessError as e:
            print("scanning logs failed with output: " + e.output)

    elif method == 'walk':
        #TODO: os.walk method
        print("this would normally do an os.walk")
    else:
        print("no other logs scanning method currentlyl exists!")

def xml_update(logs_obj):
    f = logs_obj.xml
    if f is None:
        print("ERROR: the log set for '", loginfo_obj.cid, "' does not seem to contain an xml file\n"
              "ERROR: unable to parse XML file in logs!\n")
    else:
        tree =  ET.parse(f)
        root = tree.getroot()
        cdr = root.find("./CallDetailRecord")
        ci = cdr.find("./CallInfo")

        # parse the CallInfo
        logs_obj.audio_time = ci.find("./TimeFirstAudioPushed").text
        logs_obj.connect_time = ci.find("./TimeConnect").text
        logs_obj.modechange_time = ci.find("./TimeModeChange").text

        # parse the rest of the CDR
        logs_obj.cpa_result = cdr.find("./CPAResult").text
        logs_obj.final_prob = cdr.find("./CPAResultProbability").text

class Logs(object):
    def __init__(self, cid, logs_list):
        self.cid = cid
        self.logs = []
        self.wavs = []
        # self.paths = {'logs':[], 'xml':None, 'wav':[]}

        for path in logs_list:
            # assign properties by extension (note the 'byte' format)
            filename, extension = os.path.splitext(path)
            if extension == b".log":
                self.logs.append(path)

            elif extension == b".xml":
                self.xml = path

            elif extension == b'.wav':
                self.wavs.append(path)

        # sort the wave files
        self.wavs.sort()

        xml_update(self)

class LogPackage(object):
    def __init__(self, csv_file, logs_dir):

        print("creating new logs package in memory...")
        # self._id = callset_id
        self.fields         = {}
        self._field_mask    = []
        self.mask_indices   = []

        self.cid_unfound    = {}
        self.logs           = {}
        self.entries        = []
        self.failed_entries = []

        # compile data
        self.load_logs(csv_file, logs_dir)

    @property
    def length(self):
        return len(self.entries)

    def load_logs(self, csv_file, logs_dir):
        """ load a new log package into memory """
        try:
            # load csv file and populate useful properties
            print("opening csv file : '", csv_file, "'")
            with open(csv_file) as csv_buffer:

                # TODO: add a csv sniffer here to determine an excell dialect?
                csv_reader = csv.reader(csv_buffer)

                # if LogPackage is not populated with data, gather template info
                if len(self.entries) == 0:
                    self.title        = next(csv_reader)    # first line should be the title
                    self.fields       = next(csv_reader)   # second line should be the field names
                    self.field_widths = [0 for i in self.fields]

                    # gather user friendly fields (i.e. fields worth reading on the CLI)
                    self.cid_index           = self.fields.index(cid_f)
                    self.phone_index         = self.fields.index(phone_num)
                    self.result_index        = self.fields.index(nca_result)
                    self.detail_result_index = self.fields.index(det_nca_result)

                    # make a field mask for displaying a selection of fields
                    self.mask_indices = [self.cid_index, self.result_index, self.detail_result_index]

                    # create a list of indices
                    self.width = len(self.fields)

                # compile a list of csv/call entries
                print("compiling log index...")
                for entry in csv_reader:

                    # search for log files using call-id field
                    cid = entry[self.cid_index]
                    log_list = scan_logs(cid)

                    if len(log_list) == 0:
                        print("WARNING no log files found for cid :", cid)
                        self.cid_unfound[cid] = 1
                        next

                    else:
                        self.logs[cid] = Logs(cid, log_list)

                    # TODO: use the "collections" module here!
                    # keep track of max str lengths for each field
                    i = 0
                    for column in entry:
                        if len(column) > self.field_widths[i]:
                            self.field_widths[i] = len(column)
                        i += 1

                    # if all else is good add the entry to our db
                    self.entries.append(entry)

            print(str(sum(self.cid_unfound.values())), "cids which did not have logs in the provided package")

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
        print("requested csv statistics summary ONLY!\n"
              "calling handy gawk script...\n")
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

# handles
global factory, cs

# field value used to 'segment' sub-callsets in in the object interface
disjoin_field  = nca_result

# compile logs package into memory
logs = LogPackage(csv_file, logs_dir)
# build a callset interface
factory, cs = callset.new_callset(logs, disjoin_field)

def reset():
    factory, cs = callset.new_callset(logs, disjoin_field)
    return factory, cs


# HINT: to create a new subset try something like,
# subset = factory.new_subset(parent, filter_function)
# where the filter_function is something like -> filter_by_field(3, gt, 500)
# here 3 is field index, gt ('greater then') is a comparison function, 500 is a const to compare against
# see callset.py for more details
