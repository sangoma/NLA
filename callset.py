# interface for a call set
# Python3 implementation
import time
import datetime
import csv
import subprocess

class CallSet(object):
    def __init__(self, csv_file, callset_id):
        self._id = callset_id
        # self.length = 0

        # try to open csv file and return a reader/iterator
        try:
            print("opening csv file: '" + csv_file + "'")
            print("assigning callset id: '" + str(callset_id) + "'")

            csv_buffer = open(csv_file)#, newline='')

            # TODO: add a csv sniffer here to determine a dialect
            # NOTE: default delimiter = ','
            self._reader = csv.reader(csv_buffer)

            self._title = next(self._reader)    # first line should be the title
            self._fields = next(self._reader)   # second line should be the field names

            # create a list of indices
            self._indices = [i for i in range(len(self._fields))]
            self.width = len(self._indices)

            # compile call list entries
            # self._entries = [row for row in self._reader]
            self._buildlist()
            self.length = len(self._entries)

            print("creating call set...")
            print ("'" + self.__class__.__name__ + "' object:  created!")

        except csv.Error as err:
            print('file %s, line %d: %s' % (csv_buffer, self._reader.line_num, err))
            print("Error:", exc)
            sys.exit(1)

    def _buildlist(self):
        """csv.reader, list of fields -> list of dicts = csv rows"""
        self._entries = []
        self._destinations = set()     # set of phone numbers
        self.num_dup_dest = 0
        phone_index = self._fields.index('Phone Number')

        # build a list of csv/call entries
        print("compiling logs index...")
        for entry in self._reader:

            self._line_num = self._reader.line_num

            # if we've already seen this phone number then skip the entry
            if entry[phone_index] in self._destinations:
                self.num_dup_dest += 1
                next
            else:
                # add destination phone number to our set
                self._destinations.add(entry[phone_index])

                try:
                    # search for log files using call-id field
                    logs = subprocess.check_output(["find", "./", "-regex", "^.*" + entry[0] + ".*"])
                    # entry.append(tuple(list(logs)))
                except subprocess.CalledProcessError as e:
                    print("find failed with output: " + e.output)

                self._entries.append(entry)

                del entry

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


    def _scan_logs(self, logdir='./'):
    #TODO: 
    # check for logs for each entry report errors if logs not found etc.
    # search in pwd and/or pointed dir
        return None

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

