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

# higher order comparison/filtering functions
def eq(field_index, value):
    return lambda container: container[field_index] == value

def neq(field_index, value):
    return lambda container: container[field_index] != value

# slice closure : use this to generate stateful slices
def slice(start, stop):
    return lambda lst: lst[start:stop]

# select specific fields from an iterable
# this function will usually be mapped over the parent
# container/iterable
def field_select(index_lst):
    return lambda lst: [lst[index] for index in index_lst]

# compile the values from this iterable
def strain(iterable):
    return [i for i in iterable]

# create a filtered iterable of entries by field
def filter_by_field(field_index, filter_func, value):
    return lambda lst: filter(filter_func(field_index, value), lst)

# applies a 'filter' on the given iterable (see filter functions above)
# NOTE: use recursively to cascade filters
def apply_filter(filter_func, iterable):
     return filter(filter_func, iterable)

# def select_entries(start, stop):
#     return filter(select(start, stop),

# generate a column iterator
def field_iter(field_index, lst_of_entries):
    for entry in lst_of_entries:
        yield entry[field_index]

# class to operate on and describe a callset
class CallSet(object):

    def __init__(self, csv_file, logs_dir, callset_id):

        print("assigning callset id: '" + str(callset_id) + "'")
        self._id = callset_id
        self.num_dup_dest = 0
        self.num_cid_unfound = 0
        self._destinations = set()

        self.add_package(csv_file, logs_dir)

        self.length = len(self._entries)
        # note the number of duplicate calls to a single callee
        print("number of duplicate destinations = " + str(self.num_dup_dest))
        print ("" + self.__class__.__name__ + " object:  created!")


    def _buildset(self, csv_reader):
        """iterate the csv.reader to build a set of call entries"""

        self._title = next(csv_reader)    # first line should be the title
        self._fields = next(csv_reader)   # second line should be the field names
        self._entries = []
        self._results = {}                # dict of results
#TODO: dynamically generate properties based on results content


        # get special indices
        cid_index = self._fields.index('Netborder Call-id')
        phone_index = self._fields.index('Phone Number')

        # create a destination db?
        # (the new set of phone numbers / destinations)
        if self._destinations is None:
            self._destinations = set()

        # create a list of indices
        self._indices = [i for i in range(len(self._fields))]
        self.width = len(self._indices)

        # build a list of csv/call entries
        for entry in csv_reader:
            self._line_num = csv_reader.line_num

            # if we've already seen this phone number then skip the entry
            if entry[phone_index] in self._destinations:
                self.num_dup_dest += 1
                next
            else:
                # add destination phone number to our set
                self._destinations.add(entry[phone_index])

                try:
                    # search for log files using call-id field
                    logs = self._scan_logs(entry[cid_index])

                    if len(logs) == 0:
                        print("WARNING: no log files found for cid '" + entry[cid_index] + "'")
                        self.num_cid_unfound += 1

                except subprocess.CalledProcessError as e:
                    print("'subprocess' failed with output: " + e.output)

                self._entries.append(entry)

    def _scan_logs(self, re_literal, logdir='./'):
    # check for logs for each entry report errors if logs not found etc.
        # TODO: use os.walk here instead of subprocess
        logs = subprocess.check_output(["find", logdir, "-regex", "^.*" + re_literal + ".*"])
        return logs

    def _compute_stats(self, lst_of_entries):
        return None

    # higher order function which generates a column filter
    def _gen_col_filter(self, field_index, operator_func):
        return lambda field_index, operator_func, value: operator_func(field_index, value)


    def _lst_slice(self, lst, start=0, stop=-1):
        return lst[start:stop]

    def add_package(self, csv_file, logs_dir):
        """ add a new package to the current callset """
        # try to open csv file and return a reader/iterator
        print("opening csv file: '" + csv_file + "'")
        try:
            with open(csv_file) as csv_buffer:

                # TODO: add a csv sniffer here to determine a dialect?
                # default delimiter for nca = ','
                self._reader = csv.reader(csv_buffer)

                # compile call list entries
                print("compiling logs index...")
                self._buildset(self._reader)

        except csv.Error as err:
            print('file %s, line %d: %s' % (csv_buffer, self._reader.line_num, err))
            print("Error:", exc)
            sys.exit(1)

    def row(self, row_number):
        """Access a row in readable form"""
        # TODO: eventually make this print pretty in ipython
        readable_row = list(zip(self._indices, self._fields, self._entries[row_number]))
        return readable_row

    def field_index(field_name_str):
        assert(type(field_name_str) == str)
        return self._fields.index(field_name_str)

    def stats(self):
        return None

    def write(self):
        """Access to the csv writer"""
        #ex. cs.write("dirname/here")
        print("this would write your new logs package")
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
        fields = list(zip(self._indices, self._fields))
        return fields

