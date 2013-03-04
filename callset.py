# interface for a call set
# Python3 implementation

# IDEAS:
# done - compose methods dynamically depending on results acquired
# done - create a seperate class LogsPackage
# - os.walk and build a dict of logs for each entry

from imp import reload
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
# column used to 'segment' sub-callsets by value
disjoin_field  = nca_result

# higher order comparison/filtering functions
def eq(field_index, value):
    return lambda container: container[field_index] == value
def neq(field_index, value):
    return lambda container: container[field_index] != value

# filter a callset by a field entry value (uses above filters)
def filter_by_field(field_index, filter_func, value):
    '''create a filtered iterable of entries by field'''
    return lambda lst: filter(filter_func(field_index, value), lst)

# example filters which can be applied to a callset._entries
# am_f = filter_by_field(5, eq, "Answering-Machine")
# human_f = filter_by_field(5, eq, "Human")

# select specific fields from an iterable
# this function will usually be applied over the 'parent' container/iterable
def field_select(index_lst):
    return lambda container: (container[index] for index in index_lst)

def strain(iterable):
    '''compile the values from this iterable into a list'''
    return [i for i in iterable]

# generate a column iterator
def field_iter(field_index, lst_of_entries):
    for entry in lst_of_entries:
        yield entry[field_index]

# def stats_f(self, iterable, filter_f=None ):
#     def comp(field_index):

#     return None

# instantiate interface for the command-line client
def new_callset(csv_file, logs_dir):
    # cs = CallSet("super", nca_result)
    factory = SetFactory()
    # partition using field index 5
    cs = factory.new_super(disjoin_field, csv_file, logs_dir)
    return cs

# use a factory design pattern you fool!
class SetFactory(object):

    #TODO: consider attaching the factory to the callset itself?
    def new_super(self, subset_field_tag, csv_file, logs_dir):
        cs = CallSet("stats_csv", subset_field_tag)
        add_package(cs, csv_file, logs_dir)

        # allocate subsets and attach as attributes of the callset
        for s in cs._subset_tags.keys():
            subset = self.new_subset(cs, filter_by_field(cs._subset_field_index, eq, str(s)))
            self.attach_prop(cs, s, subset)
        return cs

    # def gen_props(self,

    def attach_prop(self, parent, name, prop):
        # remove spaces and dashes
        name = name.replace('-', '')
        name = name.replace(' ', '')
        setattr(parent, name, prop)

    # gen a new subset and attach to the superset as an attribute
    def new_subset(self, super_set, filter_f):

            # using "containment and delegation"
            class SubSet(CallSet):
                def __init__(self, super_set, filter_func):
                    self._parent = super_set
                    self._filter = filter_func
                    # self._stats_comp = 

                def __getattr__(self, attr):
                   return getattr(self._parent, attr)

                @property
                def show(self):
                    self.print_spaced(map(self._field_mask, self._filter(self._entries)))

                @property
                def length(self):
                    return len(list(self._filter(self._entries)))

            return SubSet(super_set, filter_f)

# class to package on and describe a callset
class CallSet(object):

    def __init__(self, callset_id, subset_field_tag):

        print("assigning callset id: '" + str(callset_id) + "'")
        self._id = callset_id
        self.subset_field_tag = subset_field_tag
        self._subset_field_index = int()
        # self.subset_field_index
        self._subset_tags = {}
        self._field_mask = []

        # counters
        # self.length = 0
        self.num_dup_dest = 0
        self.num_cid_unfound = 0
        # "members" of this call set
        self._fields = {}
        self._entries = []
        self._destinations = set()
        self._log_paths = {}


    def row(self, row_indices):
        """Access a row in readable form"""
        # TODO: eventually make this print pretty in ipython
        readable_row = list(zip(self._indices, self._fields, self._entries[row_indices]))
        return readable_row

    def stats(self):
        return None

    # search for a call based on field, string pair
    def find(self, pos):
        return None

    @property
    def show(self):
        self.print_spaced(map(self._field_mask, self._entries))

    @property
    def fields(self):
        # create list of tuples : ( index, field element)
        fields = list(zip(self._indices, self._fields))
        # print_all([self._fields])
        return fields

    @property
    # consider making the filter_f empty for the super and then this
    # function is defined only once
    def length(self):
        # if filter_f is None:
        return len(self._entries)


    # this should be dynamically allocated based on results in the csv
    # @property
    # def AM(self):
    #     ams = am_f(self._entries)
    #     return self.print_spaced(ams)

def add_package(callset, csv_file, logs_dir):
    """ add a new logs package to a callset """

    # open csv file and return a reader/iterator
    try:
        print("opening csv file: '" + csv_file + "'")
        with open(csv_file) as csv_buffer:

            # TODO: add a csv sniffer here to determine a dialect?
            csv_reader = csv.reader(csv_buffer)

            # if callset is not populated with datak, gather template info
            if len(callset._entries) == 0:
                callset._title = next(csv_reader)    # first line should be the title
                callset._fields = next(csv_reader)   # second line should be the field names
                callset._field_widths = [0 for i in callset._fields]

                # gather user friendly fields (i.e. fields worth reading on the CLI)
                callset._cid_index = callset._fields.index(cid)
                callset._phone_index = callset._fields.index(phone_num)
                callset._result_index = callset._fields.index(nca_result)
                callset._detail_result_index = callset._fields.index(det_nca_result)

                # make a field mask
                mask_indices = [callset._cid_index, callset._result_index, callset._detail_result_index]
                callset._field_mask = field_select(mask_indices)

                # find the index of the field to use as the disjoint union tag
                callset._subset_field_index = callset._fields.index(callset.subset_field_tag)

                # filter for fields of interest
                callset.print_spaced = printer()

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
                            next
                        else:
                            callset._log_paths[entry[callset._cid_index]] = LogPaths(logs)

                    except subprocess.CalledProcessError as e:
                        print("scanning logs failed with output: " + e.output)

                    # keep track of max str lengths for each field
                    i = 0
                    for column in entry:
                        if len(column) > callset._field_widths[i]:
                            callset._field_widths[i] = len(column)
                        i += 1

                    # if all else is good add the entry to our db
                    callset._entries.append(entry)

                    # update the subset tags
                    val = entry[callset._subset_field_index]
                    if val not in callset._subset_tags.keys():
                        callset._subset_tags[val] = 1
                    # count up the number of entries with this tag
                    elif val in callset._subset_tags.keys():
                        callset._subset_tags[val] += 1

            # assign summary properties
            # callset.length = len(callset._entries)

            print(str(callset.num_dup_dest), "duplicate phone number destinations found!"
                 "\n\n", callset.__class__.__name__, " instance created!\n"
                 "type: cs.<tab> to see available properties")

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
def printer(field_widths=None):

    # TODO: this should take in a callset with a dict of field:<largest-size-entry> and dynamically adjust column widths
    def printer_function(table):
        # if field_selection is None:
        #     fs_table = table
        # else:
        #     fs_table = map(field_selection, table)

        index = 0  # for looks
        for row in table:  # here a table is normally a list of lists
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

def ring_in_precon(audiofile):
    return None
