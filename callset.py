# interface for a call set
# Python3 implementation

import itertools
import grapher

# higher order, value comparison/filtering functions
def eq(field_index, value):
    return lambda container: container[field_index] == value
def neq(field_index, value):
    return lambda container: container[field_index] != value
def gt(field_index, value):
    return lambda container: container[field_index] > value

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

def iter_select(index_lst):
    return lambda iterable: (itertools.islice(iterable, index, index + 1) for index in index_lst)

# def iter_select(index_lst):
#     return lambda iterable: (iter_select([index])(iterable) for index in index_lst)

# generate a column iterator
def field_iter(field_index, lst_of_entries):
    for entry in lst_of_entries:
        yield entry[field_index]

# instantiate interface for the command-line client
def new_callset(log_package, disjoin_field):
    factory = SetFactory()

    # partition using field index 5
    cs = factory.new_super(log_package, disjoin_field)
    return factory, cs

# use a factory design pattern you fool!
class SetFactory(object):

    #TODO: consider attaching the factory to the callset itself?
    def new_super(self, log_package, subset_field_tag):
        cs = CallSet("super", subset_field_tag)
        add_package(cs, log_package)

        # allocate subsets and attach as attributes of the callset
        for s in cs._subset_tags.keys():
            subset = self.new_subset(cs, filter_by_field(cs._subset_field_index, eq, str(s)))
            self.attach_prop(cs, s, subset)
        return cs

    def attach_prop(self, parent, name, prop):
        # remove spaces and dashes
        name = name.replace('-', '')
        name = name.replace(' ', '')
        setattr(parent, name, prop)

    # gen a new subset to wrap the superset as an attribute
    def new_subset(self, super_set, filter_f):

            # using "containment and delegation"
            class SubSet(CallSet):
                def __init__(self, super_set, filter_func):
                    self._id = 'sub'    # seems like a hack (see CallSet.stats)-> polymorphic approach?
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
        # self._log_paths = {}

    def _reload(self):
        self._dup_dest = 0
        self._entries.clear()
        self._destinations.clear()
        add_package(self, self._logs_pack)

    def islice(self, start, *stop_step):
        """Access a range of callset entries"""
        # TODO: eventually make this print pretty?
        # print('start = ', start)
        stop = 0
        step = None
        if len(stop_step) >= 1:
            stop = stop_step[0]
            if len(stop_step) == 2:
                step = stop_step[1]
        else:
            stop = start + 1

        return itertools.islice(self._entries, start, stop, step)

    def write(self):
        '''write out current data objects as to a CPA package'''
        write_package()

    # search for a call based on field, string pair
    def find(self, pos):
        return None

    def filter(self, field, filter_f, value):
        # subset = factory.subset(self, 
        return None

    def stats(self, field=None):
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

    def plot(self, start_index, *entries):

        # if given a number of indices create an index list
        if len(entries) > 1:
            indices = [start_index]
            for index in entries:
                indices.append(index)

        for entry in self.islice(start_index):
            # TODO: make sure that wavs is only a single file
            cid = entry[self._cid_index]
            wave_path = self._logs_pack.logs[cid].wavs[0]
            wavsig = grapher.WavSignal(wave_path)
            axes = wavsig.plot()
            wavsig.vline_annotate(axes, 5)
            # path = entry
            return wavsig

    def close(self):
        pass

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

def add_package(callset, logs_package):
    '''populate a callset from a logs package'''

    # if callset is not populated with data, gather template info
    if len(callset._entries) == 0:

        callset._logs_pack     = logs_package
        callset._fields       = logs_package.fields

    # if callset is not populated with data, gather template info
    if len(callset._entries) == 0:

        callset._logs_pack     = logs_package
        callset._fields       = logs_package.fields
        callset._field_widths = logs_package.field_widths
        callset.width         = logs_package.width

        # copy useful indexes
        callset._cid_index    = logs_package.cid_index
        callset._phone_index  = logs_package.phone_index

        # make a field mask
        callset._mask_indices = logs_package.mask_indices
        callset._field_mask   = field_select(callset._mask_indices)

        # find the index of the field to use as the disjoint union tag
        callset._subset_field_index = callset._fields.index(callset.subset_field_tag)

        # callset._log_paths    = logs_package.log_paths
        # callset._entries   = logs_package.entries

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
def printer(obj=None, fields=[], field_width=20, delim='|'):
    '''printing closure: use for printing tables (list of lists).
    Use this to create a printer for displaying CallSet content
    NOTE: should only be passed a callset AFTER the callset set has been populated
    with data (run callset.add_package first)'''

    if type(obj) == CallSet:
    # but how will these update dynamically???
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

        # here a table is normally a list of lists or an iterable over one
        # TODO: use enumerate(table) instead for index
        # row_index = 0  # for looks
        for row_index, row in enumerate(table):
            print('{0:5}'.format(str(row_index)), delim, '', end='')
            for col, w in zip(row, widths):
                print('{column:<{width}}'.format(column=col, width=w), delim, '', end='')
            print()
            # row_index += 1

    return printer_function

# default printer which prints all columns
print_all = printer(field_width=10)
print_stats_w20 = printer(field_width=20, fields=['Disposition', 'Sum', 'Proportion'], delim='|')

def write_package(callset):
    """Access to a csv writer for writing a new package"""

    # query for package name
    print("Please enter the package name (Enter will use subset name) : ")
    package_name = raw_input()

    print("this would write your new logs package with name ", package_name, "...")
    return None

# routines to be implemented
def parse_log_file(logpaths_obj):
    return None
def ring_in_precon(audiofile):
    return None
