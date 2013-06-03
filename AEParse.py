#!/usr/bin/env python3
# Contains subroutines for parsing and storing probability results from the
# analyzer engine logs of Netborder Call Analyzer

import re
import mmap

# container for a probability time series parsed from an ae log
class ProbSequence(object):
    def __init__(self, name, colour):
        self.name = name
        self.colour = colour
        self.time = []
        self.prob = []

    def get_ts(self):
        return (self.time, self.prob)

# the parser class
class AEParser(object):

    def __init__(self, filepath):

        # color codes
        # 'b'         blue
        # 'g'         green
        # 'r'         red
        # 'c'         cyan
        # 'm'         magenta
        # 'y'         yellow
        # 'k'         black
        # 'w'         white

        # here we define the colours that should be used for plotting.
        # this way the palette remains consistent.
        self.p_machine       = ProbSequence('machine', 'r')
        self.p_human         = ProbSequence('human', 'g')
        self.p_fax           = ProbSequence('fax', 'm')
        self.p_busy          = ProbSequence('busy','y')
        self.p_reorder       = ProbSequence('sit_reorder','c')
        self.p_sit_permanent = ProbSequence('sit_permanent','k')
        self.p_sit_temp      = ProbSequence('sit_temporary','w')

        # we should dynamically create ProbSequences a a function of the
        # found patterns below...?
        # we'll need a colour look up table then i guess?
        audio_time    = re.compile(b'(audio.time.is:.(\d{1,3}\.\d{3}).+?CPA.session.time.is)',
                                   flags = re.DOTALL)
        machine       = re.compile(b'CPA_MACHINE=(0.\d+)')
        human         = re.compile(b'CPA_HUMAN=(0.\d+)')
        fax           = re.compile(b'CPA_FAX=(0.\d+)')
        busy          = re.compile(b'CPA_BUSY=(0.\d+)')
        reorder       = re.compile(b'CPA_REORDER=(0.\d+)')
        sit_permanent = re.compile(b'CPA_SIT_PERMANENT=(0.\d+)')
        sit_temporary = re.compile(b'CPA_SIT_TEMPORARY=(0.\d+)')

        with open(filepath, 'r') as log:

            # use mmap module so we can re through an in-memory copy
            data    = mmap.mmap(log.fileno(), 0, prot = mmap.PROT_READ)
            matches = audio_time.findall(data)

            for chunk in matches:
                time = float(chunk[1])

            # look for prob 'key=values' in each segment (chunk) between
            # 'audio time is' samples...
                am_match       = machine.findall(chunk[0])
                human_match    = human.findall(chunk[0])
                fax_match      = fax.findall(chunk[0])
                busy_match     = busy.findall(chunk[0])
                reorder_match  = reorder.findall(chunk[0])
                sit_perm_match = sit_permanent.findall(chunk[0])
                sit_temp_match = sit_temporary.findall(chunk[0])

                # fill the sequences with any samples which are found
                if (am_match):
                    # self.cpa_machine.append( (chunk[1], am_match[0]) )
                    self.p_machine.time.append(time)
                    self.p_machine.prob.append(float(am_match[0]))

                if (human_match):
                    self.p_human.time.append(time)
                    self.p_human.prob.append(float(human_match[0]))

                if (fax_match):
                    self.p_fax.time.append(time)
                    self.p_fax.prob.append(float(fax_match[0]))

                if (busy_match):
                    self.p_busy.time.append(time)
                    self.p_busy.prob.append(float(busy_match[0]))

                if (reorder_match):
                    self.p_reorder.time.append(time)
                    self.p_reorder.prob.append(float(reorder_match[0]))

                if (sit_perm_match):
                    self.p_sit_perm.time.append(time)
                    self.p_sit_perm(float(sit_perm_match[0]))

                if (sit_temp_match):
                    self.p_sit_temp.time.append(time)
                    self.p_sit_temp.prob.append(float(sit_temp_match[0]))

if __name__ == '__main__':
    # TODO: set this unit test to use a file local to the repo...
    unit_test = AEParse('/home/tsemczyszyn/WorkLogs/MagNorth/Sangoma_NCA_logs_16_04/tuning_logs_package/1366099479-28125-1934-5740.analyzer-engine.log')
