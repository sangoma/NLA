# call set interface
# Python3 implementation

import itertools
import grapher

# higher order, value comparison/filtering functions
def eq(subscript, value):
    return lambda container: container[subscript] == value
def neq(subscript, value):
    return lambda container: container[subscript] != value
def gt(subscript, value):
    return lambda container: container[subscript] > value

# filter a callset._entries by a field entry value (generally uses above functions)
def filter_by_field(field_index, filter_func, value):
    '''create a filtered iterable of entries by field'''
    return lambda lst: filter(filter_func(field_index, value), lst)

'''example filters which can be applied to a callset._entries :
    am_f    = filter_by_field(5, eq, "Answering-Machine")
    human_f = filter_by_field(5, eq, "Human")'''

# select specific fields from a subscriptable container
# this function will usually be applied over the 'parent' container/iterable
def field_select(index_itr):
    return lambda container: (container[index] for index in index_itr)
    # return lambda container: [container[index] for index in index_itr]

# equivalent of the above function but uses generic iterables as i/o
# (which was the whole point of all this abstract fp nonsense in the first place!)
# WARNING this yield items in order which they arrive not the order requested
def iter_select(indices, itr):
    ind = [i for i in indices]
    for i, e in enumerate(itr):
        if i in ind:
            yield e
        else:
            continue

# generate a column iterator
def field_iter(field_index, lst_of_entries):
    for entry in lst_of_entries:
        yield entry[field_index]

# factory interface for the command-line client
def new_callset(log_package, disjoin_field):
    factory = CallSetFactory()

    # partition using field index 5
    return factory.new_super(log_package, disjoin_field)

# use a factory design pattern you fool!
class CallSetFactory(object):

    def new_super(self, log_package, subset_field_tag):
        cs = CallSet("superset", subset_field_tag)
    #TODO: consider attaching the factory to the callset itself?
        cs.factory = self
        add_package_to_callset(cs, log_package)

        # allocate subsets and attach as attributes of the callset
        for s in cs._subset_tags.keys():
            subset = self.new_subset(str(s), cs, filter_by_field(cs._subset_field_index, eq, str(s)))
            self.attach_prop(cs, s, subset)
        return cs

    def attach_prop(self, parent, name, prop):
        # remove spaces and dashes
        name = name.replace('-', '')
        name = name.replace(' ', '')
        setattr(parent, name, prop)

    # gen a new subset to wrap the superset as an attribute
    def new_subset(self, name_tag, super_set, filter_f):

            # using "containment and delegation"
            class SubSet(CallSet):
                def __init__(self, super_set, filter_func):
                    self._id = name_tag # seems like a hack (see CallSet.stats)-> polymorphic approach?
                    self._parent = super_set
                    self._filter = filter_func

                def __getattr__(self, attr):
                   return getattr(self._parent, attr)

                # filter the parent set using the filtering function
                @property
                def _entries(self):
                    return self._filter(self._parent._entries)

            return SubSet(super_set, filter_f)

class CallSet(object):

    def __init__(self, callset_id, subset_field_tag):

        print("assigning callset id: '" + str(callset_id) + "'")
        self._id = callset_id
        self.subset_field_tag = subset_field_tag
        self._subset_field_index = int()
        self._subset_tags = {}
        self._field_mask = []   # map this over the entries for printing
        self._mask_indices = []

        # counters
        self._dup_dest = 0
        self._cid_unfound = {}

        # "members" of this call set
        self._logs_pack = None
        self._fields = []
        self._entries = []
        self._destinations = set()
        self.grapher = grapher.WavPack([])

    def _reload(self):
        self._dup_dest = 0
        self._entries.clear()
        self._destinations.clear()
        add_package_to_callset(self, self._logs_pack)
        self.grapher.reset_cache()

    def select(self, index_itr):
        '''takes in an iterable of indices to select entries from the callset and
        returns a list of the requested entries'''
        return iter_select(index_itr, self._entries)

    def islice(self, start, *stop_step):
        """Access a range of callset entries"""
        # TODO: eventually make this print pretty?
        # print('start = ', start)
        stop = start + 1
        step = None
        if len(stop_step) >= 1:
            stop = stop_step[0]
            if len(stop_step) == 2:
                step = stop_step[1]

        return itertools.islice(self._entries, start, stop, step)

    def write(self):
        '''write out current data objects as to a CPA package'''
        write_package()

    # search for a call based on field, string pair
    def find(self, pos):
        pass

    def filter(self, field, filter_f, value):
        # subset = factory.subset(self, 
        pass

    def summary(self, field=None):
        if field == None and type(self) == CallSet:

            #TODO: abstract this such that we cycle through all the subsets of this callset instead of a silly dict?
            table = [[field, count, '{0:.4f}'.format(float(count/self.length))] for field, count in self._subset_tags.items()]
            table.sort(key=lambda lst: lst[1], reverse=True)
            print_stats_w20(table)
        else:
            # TODO: use the "collections" module here!?!?
            pass
            # do crazy iterable summing stuff...

        return None

    def plot(self, *indices):

        sip_log_list = []
        cls          = {}
        indices      = list(indices)
        indices.sort()

        # TODO: allow for plotting 'ranges' of calls (i.e. 1 to 4 in steps of 1...etc)
        for index, entry in zip(indices, self.select(indices)):
            cid = entry[self._cid_index]
            # TODO: make sure that wavs is only a single file?
            cl = self._logs_pack.call_logs[cid]
            if cl.wav == None:
                print("WARNING : no wave files were found for cid '",cid,"'")
            else:
                cls[index] = cl
                print(cl.cid, 'has index', index)

        if cls:
            for ax, cs_index, cl in zip(self.grapher.itr_plot([cl.wav for cl in cls.values()]), cls.keys(), cls.values()):
                ax.set_ylabel(str(self._id + " - " + str(cs_index)))
                grapher.vline(ax, cl.audio_connect_time, label='200 OK')
                # parse .log files for prob computations

            # pretty it up
            self.grapher.prettify()
        else:
            print("\nsorry no calls were found in subset '" + self._id + "' for indices:", indices)
            print("-> see cs."+self._id+".show")

    def close_figure(self):
        self.grapher.close_all_figs

    @property
    def _display_fields(self):
        return [name for name in self._field_mask(self._fields)]

    @property
    def fields(self):
        return self._fields
        # print_all([self._fields])

    @property
    def column_widths(self):
        return [i for i in self._field_mask(self._field_widths)]

    @property
    def show(self):
        self.print_table(map(self._field_mask, self._entries))

    @property
    def length(self):
        return len([i for i in self._entries])
        #consider?
        # return sum(itertools.count() for i in self._entries)

def add_package_to_callset(callset, logs_package):
    '''populate a callset from a logs package'''

    # if callset is not populated with data, gather template info
    if len(callset._entries) == 0:

        callset._logs_pack    = logs_package
        callset._fields       = logs_package.fields
        callset._field_widths = logs_package.field_widths
        callset.width         = logs_package.width

        # copy useful indices
        callset._cid_index    = logs_package.cid_index
        callset._phone_index  = logs_package.phone_index

        # make a field mask
        callset._mask_indices = logs_package.mask_indices
        callset._field_mask   = field_select(callset._mask_indices)

        # find the index of the field to use as the 'disjoint union tag'
        callset._subset_field_index = callset._fields.index(callset.subset_field_tag)

    # compile a list of unique call entries
    print("processing logs package into a callset...")
    for entry in logs_package.entries:
        phone_num = entry[callset._phone_index]

        # if we've already seen this phone number then remove the entry
        if phone_num in callset._destinations:
            callset._dup_dest += 1
            # callset._entries.remove(entry)
            next
        else:
            # add destination phone number to our set
            callset._destinations.add(phone_num)
            callset._entries.append(entry)
            # callset._dup_dest[phone_num] = 1

            # update the subset tags and compile proportions
            # TODO: use the "collections" module here!?!?
            val = entry[callset._subset_field_index]
            if val not in callset._subset_tags.keys():
                callset._subset_tags[val] = 1
            # count up the number of entries with this tag
            elif val in callset._subset_tags.keys():
                callset._subset_tags[val] += 1

    # create a printer function for this set
    callset.print_table = printer(obj=callset)

    print(str(callset._dup_dest), "duplicate phone number destinations found!")
    print("\n->",callset.__class__.__name__, "instance created!\n"
          "type: cs.<tab> to see available properties")

# CallSet utils

#TODO: consider making this a direct function instead of a closure
def printer(obj=None, fields=[], field_width=20, delim='|'):
    '''printing closure: use for printing tables (list of lists).
    Use this to create a printer for displaying CallSet content
    NOTE: should only be passed a callset AFTER the callset set has been populated
    with data (run callset.add_package_to_callset first)'''

    if type(obj) == CallSet:
        #TODO: but how will these update dynamically???
        callset = obj
        widths = callset.column_widths
        fields = callset._display_fields
        for w, l in zip(widths,fields):
            lg = len(l)
            if lg > w:
                widths[widths.index(w)] = lg
    else:
        # use an infinite width generator
        widths = iter(lambda:field_width, 1)

    # here a table is normally a list of lists or an iterable over one
    def printer_function(table):

        # mark as from parent scope
        nonlocal widths
        nonlocal fields

        # print a field title header
        print('')
        print('index', delim, '',  end='')
        for f, w in zip(fields, widths):
            print('{field:<{width}}'.format(field=f, width=w), delim, '', end='')
        print('\n')

        # print rows
        for row_index, row in enumerate(table):
            print('{0:5}'.format(str(row_index)), delim, '', end='')
            # print columns
            for col, w in zip(row, widths):
                print('{column:<{width}}'.format(column=col, width=w), delim, '', end='')
            print()
            # row_index += 1

    return printer_function

# default printers which prints all columns
print_all = printer(field_width=10)
print_stats_w20 = printer(field_width=20, fields=['Disposition', 'Sum', 'Proportion'], delim='|')

def write_package(callset):
    """Access to a csv writer for writing a new package"""

    # query for package name
    print("Please enter the package name (<Enter> to use subset name) : ")
    package_name = raw_input()

    print("this would write your new logs package with name ", package_name, "...")
    return None

# routines to be implemented
def parse_log_file(logpaths_obj):
    return None
def ring_in_precon(audiofile):
    return None

# #######################
# this WAS the nla.py stuff #
# #######################

# TODO:
# -implement stats computation -> should make this the 'summary' property
# -implement xml writer for lin_log_set
# -create a path index to quickly parse once nla front end has converted a package
# -implement signalling parser -> check travis' code
# DONE - implement wav file plotter
# -check for ipython and boot if available, else print stats and gen packages?
# -ask user if they would like to verify path index
# - front end script to parse xmls and just spit out the disposition
#   values (load into db?) if there is no csv to reference
# - func which takes in a text file listing cids -> creates a subset

# Ideas
# done - create a seperate class CallLogs package
# - os.walk instead of 'find' utility

import sys, os, getopt, subprocess
import xml.etree.ElementTree as ET
import csv
import shutil
import os.path as path

# important field strings
cid_f          = 'Netborder Call-id'
phone_num      = 'Phone Number'
nca_result     = 'NCA Engine Result'
det_nca_result = 'Detailed Cpd Result'

# to remove in the wav files for sa package
troublesome_suffix = '.analyzer-engine.0.0'

# 'prepared' log package names
stats_anal_package = "./sa_package"
tuning_dir         = "./tuning_logs_package"

# if this file exists the audio data has already been prepped
# this index allows for fast file path loading without having to re-scan for files
log_index_f_name = "log-index.xml"


# create a dir if it doesn't already exist
def verbose_make_dir(d):
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

            # if the returned values are 'bytes' then convert to strings ie utf-8
            str_paths = [b.decode() for b in paths]
            return str_paths

        except subprocess.CalledProcessError as e:
            print("scanning logs failed with output: " + e.output)

    elif method == 'walk':
        #TODO: os.walk method
        print("this should normally do an os.walk")
    else:
        print("no other logs scanning method currentlyl exists...sorry")

def write_log_index_f_name(cid, logs_list):
    # TODO: write a log-index xml file into the lin_log_set dir for
    # quick parsing on reload???
    pass

def xml_log_update(log_obj):
    if log_obj.xml is None:
        print("WARNING: the log set for '", log_obj.cid, "' does not seem to contain an xml file\n"
              "WARNING: unable to parse XML file in logs!\n")
    else:
        f    = log_obj.xml
        tree = ET.parse(f)
        root = tree.getroot()

        # get the important children elements
        cdr = root.find("./CallDetailRecord")
        ci  = cdr.find("./CallInfo")

        # parse the numeric CallInfo
        log_obj.audio_time         = float(ci.find("./TimeFirstAudioPushed").text)
        log_obj.connect_time       = float(ci.find("./TimeConnect").text)
        log_obj.modechange_time    = float(ci.find("./TimeModeChange").text)
        log_obj.audio_connect_time = log_obj.connect_time - log_obj.audio_time

        # parse the rest of the CDR
        log_obj.cpa_result = cdr.find("./CPAResult").text
        log_obj.final_prob = cdr.find("./CPAResultProbability").text

def add_to_dir_package(log_list, dest_dir, output_format='same', remove_str=None):

    wavs         = []
    new_paths    = []
    combine_flag = []
    format_spec  = []

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

    # call sox to do the conversion TODO: check sox exists at the front end?
    if output_format == 'linear':
        format_spec = ["-b", "16", "-e", "signed"]

    retcode = subprocess.call(["sox"] + combine_flag + wavs + format_spec + [wav_path])
    return new_paths

class LogPackage(object):
    '''A LogPackage is the in-memory representation of a customer provided log set.
    More specifically, a LogSet references the actual data provided by the customer after
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
        self.call_logs      = {}
        self.entries        = []
        self.failed_entries = []

        # compile data
        self.load_logs(csv_file, logs_dir)

    @property
    def length(self):
        return len(self.entries)

    def load_logs(self, csv_file, logs_dir):
        """ load a new log package into memory """

        # which packages to create? (default=both)
        gen_lin = gen_sa = True

        # check if log directory contains a log-index.xml file
        index_file = os.path.join(logs_dir, log_index_f_name)
        if os.path.isfile(index_file):
            print("\ndetected log index file : '", index_file, "'")

            # a hack for now until I get time to pick a format for the index xml file
            with open(index_file) as f:
                if f.read() == '':
                    print(index_file, "contains nothing...so let's not generate new packages")
                    gen_lin = False
                    gen_sa = False

            # TODO: parse some kind of xml db file
            print("THIS IS CURRENTLY NOT IMPLEMENTED: should parse xml file here and populate an instance that way!\n")
            # for list in xmlelement: (here xmelement is implemented by a generator)
            #     blah = CallLogs(list)
            pass

        else:
            print("no '", log_index_f_name, "' found!\n")

            # create package dirs
            verbose_make_dir(stats_anal_package)
            verbose_make_dir(tuning_dir)

            # create a log index file
            print("creating a log index file...")
            with open(index_file, 'a') as xml:
                xml.write("")

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

                    # search for log files in the file system using call-id field
                    cid = entry[self.cid_index]
                    log_list = scan_logs(cid, logs_dir)
                    log_list = [path.abspath(l) for l in log_list]

                    if len(log_list) == 0:
                        print("WARNING : no log files found for cid :", cid)
                        self.cid_unfound[cid] = 1
                        next

                    else:
                        # copy to the stats analyser package dir
                        if gen_sa == True:
                            add_to_dir_package(log_list, stats_anal_package, remove_str=troublesome_suffix)

                        # copy to the tuning package dir
                        if gen_lin == True:
                            log_list = add_to_dir_package(log_list, tuning_dir, output_format='linear')

                        self.call_logs[cid] = CallLogs(cid, log_list)

                    # TODO: use the "collections" module here?!
                    # keep track of max str lengths for each field
                    # (used for pretty printing to the console)
                    for i, column in enumerate(entry):
                        if len(column) > self.field_widths[i]:
                            self.field_widths[i] = len(column)

                    # if all else is good add the entry to our db
                    self.entries.append(entry)

            print("->",str(sum(self.cid_unfound.values())), "cids which did not have logs in the provided package\n")

        except csv.Error as err:
            print('file %s, line %d: %s' % (csv_buffer, self._reader.line_num, err))
            print("Error:", exc)
            sys.exit(1)

class CallLogs(object):
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
                  "WARNING: This probably means the wav files were not processed properly!")
            wavs.sort()
            self.wav = wavs[0]
        else:
            self.wav = wavs[0]

        xml_log_update(self)
