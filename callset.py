# interface for a call set
# Python3 implementation
import time
import datetime
import csv
import subprocess

class CallSet(object):

    def __init__(self, csv_file, callset_id):

        self._id = callset_id
        self.num_dup_dest = 0
        self._destinations = set()

        print("assigning callset id: '" + str(callset_id) + "'")

        # try to open csv file and return a reader/iterator
        print("opening csv file: '" + csv_file + "'")
        try:
            with open(csv_file) as csv_buffer:

                # TODO: add a csv sniffer here to determine a dialect
                # NOTE: default delimiter = ','
                self._reader = csv.reader(csv_buffer)

                # compile call list entries
                print("compiling logs index...")
                self._buildset(self._reader)
                # self._entries = [row for row in self._reader]
                self.length = len(self._entries)

            # notify the number of duplicate calls to a single callee
            print("number of duplicate destinations = " + str(self.num_dup_dest))

            print("creating call set...")
            print ("" + self.__class__.__name__ + " object:  created!")

        except csv.Error as err:
            print('file %s, line %d: %s' % (csv_buffer, self._reader.line_num, err))
            print("Error:", exc)
            sys.exit(1)

    def _buildset(self, csv_reader):
        """iterate the csv.reader iterable to build a set of call entries"""

        self._title = next(csv_reader)    # first line should be the title
        self._fields = next(csv_reader)   # second line should be the field names
        self._entries = []

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
                    if logs is None:
                        print("WARNING: no log files found!?")

                except subprocess.CalledProcessError as e:
                    print("'find' failed with output: " + e.output)

                self._entries.append(entry)

                # d = list(zip(self._fields, entry))
                # e = entry
                # lf = len(self.fields)
                # le = len(entry)
                # if lf < le:
                #     # store overloaded fields in CallSet.restkey
                #     d[self.restkey] = entry[lf:]
                # elif lf > le:
                #     for key in self.fields[le:]:
                #         d[key] = None


    def _scan_logs(self, re_literal, logdir='./'):
    # check for logs for each entry report errors if logs not found etc.
        # TODO: use os.walk here instead of subprocess
        logs = subprocess.check_output(["find", logdir, "-regex", "^.*" + re_literal + ".*"])
        return logs

    def _compute_stats(self):
        return None

    # @property
    # def dict_reader(self):
    #     """Access to the csv reader"""
    #     return self._reader

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

    def row(self, row_number):
        """Access a row in readable form"""
        # TODO: eventually make this print pretty in ipython
        # e = entry
        # lf = len(self.fields)
        # le = len(entry)
        # if lf < le:
        #     # store overloaded fields in CallSet.restkey
        #     d[self.restkey] = entry[lf:]
        # elif lf > le:
        #     for key in self.fields[le:]:
        #         d[key] = None
        # self._row.append(d)
        readable_row = list(zip(self._indices, self._fields, self._entries[row_number]))
        return readable_row

    def write(self):
        """Access to the csv writer"""
        #ex. cs.write("dirname/here")
        print("this would write your new logs package")
        return None

    # filter generator?
    # def filter(self, predicate=lambda ls: ls[11].next() ==  value: return ls.next()  ):
    #     return filter(predicate, self._rows)

    # if not cpaVersionManager.isSupported(self.__cpaVersion):
      # raise cpaVersionManager.VersionNotSupported(self.__cpaVersion)

     #if the version is different of 1.x, skip the second line of the csv
    # if(self.__cpaVersion != cpaVersionManager.SUPPORTED_VERSION[0]):
      # self.__listRows.pop(0)

    def get_call(self, pos):
        row = self.row[pos]
        return self.__build_call(row)

    def getCpaVersion(self):
        return self.__cpaVersion

    def numberofcalls(self):
        return len(self.__listRows)

    # build a call from a csv row
      #@param csvRow: csv row that represent the call
    # def __build_call(self,csvRow):

    #       #parse csv
    #     try:
    #       paraxipCallid = csvRow[0]
    #       callDate = csvRow[1]
    #       referenceID = csvRow[2]
    #       campaignName = csvRow[3]
    #       phoneNumber = csvRow[4]
    #       cpaResult = csvRow[5]
    #       timeDialing = csvRow[6]
    #       timeConnected = csvRow[7]
    #       timeCpaCompleted = csvRow[8]
    #       timeQueued = csvRow[9]
    #       timeConnectedToAgent = csvRow[10]

    #       if(self.__cpaVersion == cpaVersionManager.SUPPORTED_VERSION[0]):
    #           detailedCpaResult = ""
    #       else:
    #           detailedCpaResult = csvRow[11]
    #     except IndexError:
    #         PyLoggingFunctions.log_error(fileLogger, "Unable to parse the csvRow: " + str(csvRow)+ " (IndexError)")
    #         raise Exception("Invalid row")

    #     #correction
    #     if cpaResult == 'Voice':
    #        cpaResult = 'Human'

    #     #get foreignKeys
    #     cpaResultKey = self.__callset.cpaResults[cpaResult]
    #     detailedCpaResultKey = self.__callset.detailedCpaResults[detailedCpaResult]

    #     #process 1 (string to timeObject)
    #     callDate = cpaOMExtended.processDate(callDate)
    #     timeDialing = cpaOMExtended.processTime(timeDialing)
    #     timeConnected = cpaOMExtended.processTime(timeConnected)
    #     timeCpaCompleted = cpaOMExtended.processTime(timeCpaCompleted)
    #     timeQueued = cpaOMExtended.processTime(timeQueued)
    #     timeConnectedToAgent = cpaOMExtended.processTime(timeConnectedToAgent)

    #     #process 2 (combine the calldate and the time)
    #     timeDialing = cpaOMExtended.processDateTimeFromDateObjects(callDate, timeDialing)
    #     timeConnected = \
    #             cpaOMExtended.processDateTimeFromDateObjects(callDate, timeConnected)
    #     timeCpaCompleted = \
    #             cpaOMExtended.processDateTimeFromDateObjects(callDate, timeCpaCompleted)
    #     timeQueued = cpaOMExtended.processDateTimeFromDateObjects(callDate, timeQueued)
    #     timeConnectedToAgent = \
    #             cpaOMExtended.processDateTimeFromDateObjects(callDate, timeConnectedToAgent)

    #     #intantiate
    #     return Call(paraxipCallid,
    #             callDate,
    #             referenceID,
    #             campaignName,
    #             phoneNumber,
    #             cpaResultKey,
    #             detailedCpaResultKey,
    #             timeDialing,
    #             timeConnected,
    #             timeCpaCompleted,
    #             timeQueued,
    #             timeConnectedToAgent)

