# interface for a call set
# Python3 implementation

# IDEAS:
# - compose methods dynamically depending on results acquired
# DONE - create a seperate class LogsPackage
# - os.walk and build a dict of logs for each entry

import time
import datetime
import csv
import subprocess
import matplotlib as mpl
import os
import sys

# some important field strings
cid            = 'Netborder Call-id'
phone_num      = 'Phone Number'
nca_result     = 'NCA Engine Result'
det_nca_result = 'Detailed Cpd Result'

# higher order comparison/filtering functions
def eq(field_index, value):
    return lambda container: container[field_index] == value

def neq(field_index, value):
    return lambda container: container[field_index] != value

# filter a callset by a field entry value (uses above filters)
def filter_by_field(field_index, filter_func, value):
    '''create a filtered iterable of entries by field'''
    return lambda lst: filter(filter_func(field_index, value), lst)

# TODO: re-implement as this seems clunky
# select specific fields from an iterable
# this function will usually be mapped over the 'parent' container/iterable
def field_select(index_lst):
    return lambda lst: [lst[index] for index in index_lst]

# example filters
am_f = filter_by_field(5, eq, "Answering-Machine")
human_f = filter_by_field(5, eq, "Human")

def strain(iterable):
    '''compile the values from this iterable into a list'''
    return [i for i in iterable]

# generate a column iterator
def field_iter(field_index, lst_of_entries):
    for entry in lst_of_entries:
        yield entry[field_index]

# instantiate interface for the command-line client
def make_callset(csv_file, logs_dir):
    # cs = CallSet("super", nca_result)
    factory = SetFactory()
    # partition using field 5
    cs = factory.new_super(nca_result, csv_file, logs_dir)
    return cs

# use a factory design pattern you fool!
class SetFactory(object):

    #TODO: consider attaching the factory to the callset itself?
    def new_super(self, subset_field_tag, csv_file, logs_dir):
        cs = CallSet("super", subset_field_tag)
        parse_package(cs, csv_file, logs_dir)
        for s in cs._subset_tags.keys():
            subset = self.new_sub(cs, filter_by_field(cs._subset_field_index, eq, str(s)))
            self.attach_prop(cs, s, subset)
        return cs

    # def gen_props(self,

    def attach_prop(self, parent, name, prop):
        name = name.replace('-', '')
        setattr(parent, name, prop)

    # gen a new subset and attach to the superset as a property
    def new_sub(self, super_set, filter_f):

            # using "containment and delegation"
            class SubSet(CallSet):
                def __init__(self, super_set, filter_func):
                    self._obj = super_set
                    self._entries = filter_func(super_set._entries)

                def __getattr__(self, attr):
                   return getattr(self._obj, attr)

            return SubSet(super_set, filter_f)

            # generate filter func with field value
            # create object and provide filter
            # attach attribute to superset

# class to operate on and describe a callset
class CallSet(object):

    def __init__(self, callset_id, subset_field_tag):

        print("assigning callset id: '" + str(callset_id) + "'")
        self._id = callset_id
        self.subset_field_tag = subset_field_tag
        self._subset_field_index = int()
        # self.subset_field_index
        self._subset_tags = {}

        # counters
        self.num_dup_dest = 0
        self.num_cid_unfound = 0
        # "members" of this call set
        self._entries = []
        self._destinations = set()
        self._log_paths = {}

        #TODO: dynamically generate properties based on results content

        # note this will prevent dynamic property creation on recursive
        # calls to this class
        # if csv_file and logs_dir is not None:
        # add_package(self, csv_file, logs_dir)

    def _compute_stats(self, lst_of_entries):
        return None

    def _gen_subsets(self, subset_tag_field):
        return None

    def row(self, row_indices):
        """Access a row in readable form"""
        # TODO: eventually make this print pretty in ipython
        readable_row = list(zip(self._indices, self._fields, self._entries[row_number]))
        return readable_row

    def add_pkg(self, csv_file, logs_dir):
        add_package(self, csv_file, logs_dir)

    def stats(self):
        return None

    # search for a call based on field, string pair
    def find_call(self, pos):
        return None

    # @property
    # def id(self):
    #     """call id"""
    #     return self._id

    @property
    def show(self):
        self.print_spaced(self._entries)

    @property
    def fields(self):
        # create list of tuples : ( index, field element)
        fields = list(zip(self._indices, self._fields))
        # print_all([self._fields])
        return fields

    # this should be dynamically allocated based on results in the csv
    # @property
    # def AM(self):
    #     ams = am_f(self._entries)
    #     return self.print_spaced(ams)

def parse_package(callset, csv_file, logs_dir):
    """ add a new package to a callset """

    # open csv file and return a reader/iterator
    try:
        print("opening csv file: '" + csv_file + "'")
        with open(csv_file) as csv_buffer:

            # TODO: add a csv sniffer here to determine a dialect?
            csv_reader = csv.reader(csv_buffer)

            callset._title = next(csv_reader)    # first line should be the title
            callset._fields = next(csv_reader)   # second line should be the field names

            # get user friendly fields (i.e. fields worth reading on the CLI)
            callset._cid_index = callset._fields.index(cid)
            callset._phone_index = callset._fields.index(phone_num)
            callset._result_index = callset._fields.index(nca_result)
            callset._detail_result_index = callset._fields.index(det_nca_result)

            callset._subset_field_index = callset._fields.index(callset.subset_field_tag)
            # self._human_readable_fields = [self._cid_index, self._result_index, self._detail_result_index]

            # filter for fields of interest
            # self._ffoi = field_select(self._human_readable_fields)
            callset.print_spaced = printer(field_select([callset._cid_index, callset._result_index, callset._detail_result_index]))

            # create a destination db?
            # (the new set of phone numbers / destinations)
            if callset._destinations is None:
                callset._destinations = set()

            # create a list of indices
            callset._indices = [i for i in range(len(callset._fields))]
            callset.width = len(callset._fields)

            # compile a list of csv/call entries
            print("compiling logs index...")
            for entry in csv_reader:
                # callset._line_num = csv_reader.line_num

                # if we've already seen this phone number then skip the entry
                if entry[callset._phone_index] in callset._destinations:
                    callset.num_dup_dest += 1
                    next
                else:
                    # add destination phone number to our set
                    callset._destinations.add(entry[callset._phone_index])

                    try:
                        # search for log files using call-id field
                        logs = scan_logs(entry[callset._cid_index])

                        if len(logs) == 0:
                            print("WARNING no log files found for cid :",entry[callset._cid_index])
                            callset.num_cid_unfound += 1
                        else:
                            callset._log_paths[entry[callset._cid_index]] = LogPaths(logs)

                    except subprocess.CalledProcessError as e:
                        print("scanning logs failed with output: " + e.output)

                    callset._entries.append(entry)

                    # update the subset tags
                    val = entry[callset._subset_field_index]
                    if val not in callset._subset_tags.keys():
                        callset._subset_tags[val] = val

            # assign summary properties
            callset.length = len(callset._entries)

            print(str(callset.num_dup_dest), "duplicate phone number destinations found!")
            print(callset.__class__.__name__ + " instance created!")

    except csv.Error as err:
        print('file %s, line %d: %s' % (csv_buffer, callset._reader.line_num, err))
        print("Error:", exc)
        sys.exit(1)

def write_csv(self):
    """Access to a csv writer for writing a new package"""
    #ex. cs.write("dirname/here")
    print("this would write your new logs package...")
    return None

def gen_subset_prop(callset, field_index, name):
    setattr(callset, name, SubSet(callset))
    # add proptery to callset
    return None

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


# Utilities
def printer(field_selection=None):

    # TODO: this should take in a callset with a dict of
    # field:largest-size-entry and dynamically adjust column widths
    def printer_function(table):
        if field_selection is None:
            fs_table = table
        else:
            fs_table = map(field_selection, table)

        index = 0
        for row in fs_table:  # here a table is normally a list of lists
            print('{0:5}'.format(str(index)), '|', end='')
            # print('|'.join('{col:^{l}}'.format(col=column, l=len(str(column)) + 4) for column in row))
            print('| '.join('{col:<35}'.format(col=column) for column in row))
            index += 1

    return printer_function

# default printer which prints all columns
print_all = printer()

# def print_table(table, field_selection=None):
#     index = 0
#     for row in table:  # here a table is normally a list of lists
#         print('{0:5}'.format(str(index)), '|', end='')
#         print('|'.join('{col:^{l}}'.format(col=column, l=len(str(column)) + 4) for column in row))
#         # print('|'.join('{col:^30}'.format(col=column) for column in row))
#         index += 1

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

# routines to be implemented
def parse_xml(logpaths_obj):
    return None
def parse_log_file(logpaths_obj):
    return None
def plot_graph(callset, entry_ranger):
    return None
