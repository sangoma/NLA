#!/usr/bin/env python3
# a tool for analyzing NCA logs - NCA Log Analyzer
# this is the front end script which should be run on a cpa-stats package

# TODO:
# -implement stats computation
# -implement xml writer for lin_log_set
# -implement signalling parser -> check travis' code
# -implement wav file plotter
# -check for ipython and boot if available, else print stats and gen packages?
# -create a path index to quickly parse once nla front end has converted a package
# -ask user if they would like to verify path index

# Ideas
# done - create a seperate class LogsPackage
# - os.walk and build a dict of logs for each entry

from imp import reload

import sys, os, getopt, subprocess
import xml.etree.ElementTree as ET
import csv
import shutil

# custom modules
import callset

# some important field strings
cid_f          = 'Netborder Call-id'
phone_num      = 'Phone Number'
nca_result     = 'NCA Engine Result'
det_nca_result = 'Detailed Cpd Result'

# to remove in the wav files for sa package
troublesome_suffix = '.analyzer-engine.0.0'

# 'prepped' package names
stats_anal_package = "./sa_package"
tuning_dir         = "./tuning_logs_package"

# if this file exists the audio data has already been prepped
# this index allows for fast file path loading
log_index = "log-index.xml"

def usage():
    """help function"""
    print("This tool parses an NCA log package, provides a disposition "
          "summary and conducts log segmentation by results classification.\n"
          "It relies heavily on ipython for practical use to "
          "efficiently analyze a log set\n\n"
          "Usage: ./nla.py <cpa-stats.csv> <call-logs directory name>\n")

# create a dir if it doesn't already exist
def make_dir(d):
    if not os.path.exists(d):
        print("-> creating package dir: " + d)
        os.makedirs(d)
        return True
    else:
        print("WARNING : ", d, " already exists...overwriting\n")
        return False

def scan_logs(re_literal, search_dir, method='find'):
    if method == 'find':
        try:
            found = subprocess.check_output(["find", search_dir, "-regex", "^.*" + re_literal + ".*"])
            paths = found.splitlines()

            # TODO: move this up to line 64
            # if the returned values are 'bytes' then convert to strings
            # if len(paths) > 0 and type(paths[0]) == 'bytes':
            str_paths = [b.decode() for b in paths]

            return str_paths

        except subprocess.CalledProcessError as e:
            print("scanning logs failed with output: " + e.output)

    elif method == 'walk':
        #TODO: os.walk method
        print("this should normally do an os.walk")
    else:
        print("no other logs scanning method currentlyl exists!")

def write_log_index(cid, logs_list):
    # TODO: write a log-index xml file into the lin_log_set dir for
    # quick parsing on reload???
    pass

def xml_log_update(log_obj):
    if log_obj.xml is None:
        print("WARNING: the log set for '", log_obj.cid, "' does not seem to contain an xml file\n"
              "WARNING: unable to parse XML file in logs!\n")
    else:
        f = log_obj.xml
        tree =  ET.parse(f)
        root = tree.getroot()

        # get the important children elements
        cdr = root.find("./CallDetailRecord")
        ci = cdr.find("./CallInfo")

        # parse the CallInfo
        log_obj.audio_time = ci.find("./TimeFirstAudioPushed").text
        log_obj.connect_time = ci.find("./TimeConnect").text
        log_obj.modechange_time = ci.find("./TimeModeChange").text

        # parse the rest of the CDR
        log_obj.cpa_result = cdr.find("./CPAResult").text
        log_obj.final_prob = cdr.find("./CPAResultProbability").text

def add_to_package(log_list, dest_dir, output_format='same', remove_str=None):

    wavs         = []
    new_paths    = []
    combine_flag = []
    format_spec  = []

    # make_dir(dest_dir)

    for path in log_list:
        filename, extension = os.path.splitext(path)

        # if extension == b'.wav':
        if extension == '.wav':
            # wavs.append(path.decode())
            wavs.append(path)
        else:
            # new_paths.append(shutil.copy(path.decode(), dest_dir))
            new_paths.append(shutil.copy(path, dest_dir))

    # process the wave files
    if len(wavs) > 1:
        wavs.sort()         # sort in place
        print("INFO: concatenating ->", " + ".join(os.path.basename(w) for w in wavs))
        combine_flag = ["--combine", "concatenate"]

    elif not wavs:
        # if no wav file
        return new_paths

    wavname = os.path.basename(wavs[0])

    if remove_str is not None:
        # remove str part from file name
        wavname.replace(remove_str, "")

    wav_path = '/'.join([dest_dir, wavname])
    new_paths.append(wav_path)

    # call sox to do the conversion TODO: check this exists at the front end
    if output_format == 'linear':
        format_spec = ["-b", "16", "-e", "signed"]

    retcode = subprocess.call(["sox"] + combine_flag + wavs + format_spec + [wav_path])

    return new_paths

class Logs(object):
    def __init__(self, cid, logs_list):
        self.cid = cid
        self.logs = []
        self.xml = None

        # list of wavs
        wavs = []

        for path in logs_list:
            # assign properties by extension (note the 'byte' format)
            filename, extension = os.path.splitext(path)
            if extension == ".log":
                self.logs.append(path)

            elif extension == ".xml":
                self.xml = path

            elif extension == '.wav':
                wavs.append(path)

        if len(wavs) == 0:
            print("WARNING : no wave files found for cid '", self.cid, "'")
            self.wav = None

        elif len(wavs) > 1:
            print("Log instance was passed more then 1 wave file!\n"
                  "This probably means the wav files were not processed properly!")
            wavs.sort()
            self.wav = wavs[0]

        else:
            self.wav = wavs[0]

        xml_log_update(self)

class LogPackage(object):
    '''A LogPackage is the in-memory representation of a customer provided log set.
    More specifically, a LogSet represents the actual data provided by the customer after
    the call recording data has been converted to linear format. 

    A LogSet instance contains the following reference information:
    - file paths to log files which are copied to a new directory which of 'prepped' audio files in lpcm format
    - information parsed from the cdr/.xml
    - counters of indexing errors between the cpa-stats.csv summary and the actual log files provided'''

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

        # check if log directory contains a log-index.xml file
        if os.path.isfile(os.path.join(logs_dir, log_index)):
            print("detected log index file : '", log_index, "'")
            # TODO: parse some kind of xml db file
            print("CURRENTLY NOT IMPLEMENTED:\n"
                  "should parse xml file here and populate the instance that way!")
            # for list in xmlelement: (here xmelement is implemented by a generator)
            #     blah = Logs(list)
            pass

        else:
            print("no '", log_index, "' found!\n")
            make_dir(stats_anal_package)
            make_dir(tuning_dir)
            print("scanning for log files ...")
                  # "would you like to re-scan for log files on the system? [Y/n]")
            # answer = raw_input()
            # if answer == 'Y' or answer == '\n':
                # pass
            # else:
                # print("exiting...")
                # sys.exit(0)
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
                print("compiling log index...\n")
                for entry in csv_reader:

                    # search for log files using call-id field
                    cid = entry[self.cid_index]

                    # search for the log files in the file system
                    log_list = scan_logs(cid, logs_dir)

                    if len(log_list) == 0:
                        print("WARNING : no log files found for cid :", cid)
                        self.cid_unfound[cid] = 1
                        next

                    else:
                        # copy to the tuning package dir
                        tuning_list = add_to_package(log_list, tuning_dir, output_format='linear')
                        self.logs[cid] = Logs(cid, tuning_list)

                        # copy to the stats analyser package dir
                        add_to_package(log_list, stats_anal_package, remove_str=troublesome_suffix)


                    # TODO: use the "collections" module here!
                    # keep track of max str lengths for each field
                    # i = 0
                    for i, column in enumerate(entry):
                        if len(column) > self.field_widths[i]:
                            self.field_widths[i] = len(column)
                        # i += 1

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
        # TODO: actually call the gawk script from here...
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
