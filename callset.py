# interface for a call set
# Python3 implementation
import time
import datetime
import csv

class CallSet(object):
    def __init__(self, csv_file, callset_id):
        self._id = callset_id
        self.length = 0

        # try to open csv file and return a reader/iterator
        try:
            print("opening csv file: '" + csv_file + "'")
            print("assigning callset id: '" + str(callset_id) + "'")
            
            csv_buffer = open(csv_file, newline='')

            #TODO: add a csv sniffer here to determine a dialect
# default delimiter=','
            self._reader = csv.reader(csv_buffer) 

            # first line should be the title
            self._title = next(self._reader)
            # second line should be the field names
            fields = next(self._reader)

            indices = [i for i in range(len(fields))]

            # create list of tuples : ( index, field element)
            self._fields = list(zip(indices, fields))

            # build out data set
            # self._buildlist()
            self._rows = [row for row in self._reader]

            # self._buildset()

            # query user if they would like to scan the logs
            # self._scanlogs

        except csv.Error as err:
            print('file %s, line %d: %s' % (csv_buffer, self._reader.line_num, err))
            print("Error:", exc)
            sys.exit(1)

    # def _buildset(self):
    # """csv.reader, list of fields -> list of dicts = csv rows"""
        # use a list comprehension to generate our entries
            
    def _buildlist(self):
    # """csv.reader, list of fields -> list of dicts = csv rows"""
        self._row = []

        # build a list of csv/call entries
        for entry in self._reader:
            # self.line_num = self._reader.line_num

            # d = list(zip(self._fields, entry))
            e = entry
            lf = len(self.fields)
            le = len(entry)
            if lf < le:
                # store overloaded fields in CallSet.restkey
                d[self.restkey] = entry[lf:]
            elif lf > le:
                for key in self.fields[le:]:
                    d[key] = None
            self._row.append(d)
            # del d -> should this be here?

        # record the length of the set
        self.length = len(self._row)


    def _scan_logs(self, logdir):
    #TODO: 
    # check for logs for each entry
    # report errors if logs not found etc.
    # search for logs in pwd and/or pointed dir
        return None
        
    @property
    def row(self, row_number):
        """Access to the csv reader"""
        return self._rows[row_number]

    @property
    def dict_reader(self):
        """Access to the csv reader"""
        return self._reader

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
        # save the second row as the field names
        return self._fields

    def write(self):
        """Access to the csv writer"""
        #ex. cs.write("dirname/here")
        print("this would write your new logs package")
        return None

    # filter closure
    def filter(predicate):
    # """filter applied to a predicate and a list returns the list of those elements that satisfy the predicate"""
    # should work where you call filter(remove(key="result"))
        return None


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

