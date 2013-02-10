# interface for a call set
# Python3 implementation

# IDEAS:
# - compose methods dynamically depending on results acquired
# - create a seperate class LogsPackage
# - os.walk and build a dict of logs for each entry

import time
import datetime
import csv
import subprocess
import matplotlib as mpl

# important field strings
cid            = 'Netborder Call-id'
phone_num      = 'Phone Number'
nca_result     = 'NCA Engine Result'
det_nca_result = 'Detailed Cpd Result'

# higher order comparison/filtering functions
def eq(field_index, value):
    return lambda container: container[field_index] == value

def neq(field_index, value):
    return lambda container: container[field_index] != value

# slice closure (for slicing entries)
def slice(start, stop):
    return lambda lst: lst[start:stop]

# select specific fields from an iterable
# this function will usually be mapped over the parent container/iterable
def field_select(index_lst):
    return lambda lst: [lst[index] for index in index_lst]

def filter_by_field(field_index, filter_func, value):
    '''create a filtered iterable of entries by field'''
    return lambda lst: filter(filter_func(field_index, value), lst)

# filters
am_f = filter_by_field(5, eq, "Answering-Machine")
human_f = filter_by_field(5, eq, "Human")

def strain(iterable):
    '''compile the values from this iterable into a list'''
    return [i for i in iterable]

# generate a column iterator
def field_iter(field_index, lst_of_entries):
    for entry in lst_of_entries:
        yield entry[field_index]

def index_iter(length):
    for i in range(length):
        yield i

def add_package(callset, csv_file, logs_dir):
    """ add a new package to a callset """
    # try to open csv file and return a reader/iterator
    print("opening csv file: '" + csv_file + "'")
    try:
        with open(csv_file) as csv_buffer:

            # TODO: add a csv sniffer here to determine a dialect?
            # default delimiter for nca = ','
            csv_reader = csv.reader(csv_buffer)

            callset._title = next(csv_reader)    # first line should be the title
            callset._fields = next(csv_reader)   # second line should be the field names

            # get special indices
            cid_index = callset._fields.index(cid)
            phone_index = callset._fields.index(phone_num)

            # create a destination db?
            # (the new set of phone numbers / destinations)
            if callset._destinations is None:
                callset._destinations = set()

            # create a list of indices
            callset._indices = [i for i in range(len(callset._fields))]
            callset.width = len(callset._indices)

            # compile a list of csv/call entries
            print("compiling logs index...")
            for entry in csv_reader:
                callset._line_num = csv_reader.line_num

                # if we've already seen this phone number then skip the entry
                if entry[phone_index] in callset._destinations:
                    callset.num_dup_dest += 1
                    next
                else:
                    # add destination phone number to our set
                    callset._destinations.add(entry[phone_index])

                    try:
                        # search for log files using call-id field
                        logs = scan_logs(entry[cid_index])

                        if len(logs) == 0:
                            print("WARNING no log files found for cid :",entry[cid_index])
                            callset.num_cid_unfound += 1

                    except subprocess.CalledProcessError as e:
                        print("scanning logs failed with output: " + e.output)

                    callset._entries.append(entry)

    except csv.Error as err:
        print('file %s, line %d: %s' % (csv_buffer, callset._reader.line_num, err))
        print("Error:", exc)
        sys.exit(1)

# class to operate on and describe a callset
class CallSet(object):

    def __init__(self, csv_file, logs_dir, callset_id):

        print("assigning callset id: '" + str(callset_id) + "'")
        self._id = callset_id
        self.num_dup_dest = 0
        self.num_cid_unfound = 0

        self._entries = []
        self._destinations = set()

        #TODO: dynamically generate properties based on results content
        self._results = {}                # dict of results

        add_package(self, csv_file, logs_dir)
        self.length = len(self._entries)

        # get user friendly fields (i.e. fields worth reading on the CLI)
        self._cid_index = self._fields.index(cid)
        self._phone_index = self._fields.index(phone_num)
        self._result_index = self._fields.index(nca_result)
        self._detail_result_index = self._fields.index(det_nca_result)
        # self._human_readable_fields = [self._cid_index, self._result_index, self._detail_result_index]

        # filter for fields of interest
        # self._ffoi = field_select(self._human_readable_fields)
        self.print_pretty = printer(field_select([self._cid_index, self._result_index, self._detail_result_index]))

        # note the number of duplicate calls to a single callee
        print("number of duplicate destinations = " + str(self.num_dup_dest))
        print(self.__class__.__name__ + " instance created!")

    def _compute_stats(self, lst_of_entries):
        return None

    def row(self, row_number):
        """Access a row in readable form"""
        # TODO: eventually make this print pretty in ipython
        readable_row = list(zip(self._indices, self._fields, self._entries[row_number]))
        return readable_row

    def stats(self):
        return None

    def write(self):
        """Access to a csv writer for writing a new package"""
        #ex. cs.write("dirname/here")
        print("this would write your new logs package...")
        return None

    # search for a call based on field, string pair
    def get_call(self, pos):
        return None

    @property
    def id(self):
        """call id"""
        return self._id

    @property
    def title(self):
        # save the first row as the title
        return self._title

    @property
    def fields(self):
        # create list of tuples : ( index, field element)
        # fields = list(zip(self._indices, self._fields))
        print_table(list(zip(index_iter(len(self._fields)),self._fields)))
        # return fields

    # this should be dynamically allocated based on results in the csv
    @property
    def AM(self):
        ams = am_f(self._entries)
        # am_readable = map(self._ffoi, ams)
        # for entry in am_readable:
        self.print_pretty(ams)
        # for entry in iterable:
        #     print(entry)
        # return strain(iterable)

# Utility functions
def printer(field_selection):
    def printer_function(table):
        fs_table = map(field_selection, table)
        index = 0
        for row in fs_table:  # here a table is normally a list of lists
            print('{0:5}'.format(str(index)), '|', end='')
            print('|'.join('{col:^{l}}'.format(col=column, l=len(str(column)) + 4) for column in row))
            # print('|'.join('{col:^30}'.format(col=column) for column in row))
            index += 1
    return printer_function

def print_table(table, field_selection=None):
    index = 0
    for row in table:  # here a table is normally a list of lists
        print('{0:5}'.format(str(index)), '|', end='')
        print('|'.join('{col:^{l}}'.format(col=column, l=len(str(column)) + 4) for column in row))
        # print('|'.join('{col:^30}'.format(col=column) for column in row))
        index += 1

def scan_logs(re_literal, logdir='./', method='find'):
    # TODO: use os.walk here instead of subprocess
    if method == 'find':
        logs = subprocess.check_output(["find", logdir, "-regex", "^.*" + re_literal + ".*"])
        return logs
    else:
        raise "no other logs scanning method currentlyl exists!"
