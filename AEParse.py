#!/usr/bin/env python3
#Contains subroutines for parsing and storing probability results from the
#analyzer engine logs of Netborder Call Analyzer

import re
import mmap

class AEParse(object):

    def __init__(self, filepath):

        self.cpa_machine = []
        self.cpa_human = []
        self.cpa_fax = []
        self.cpa_busy = []
        self.cpa_reorder = []
        self.cpa_sit_permanent = []
        self.cpa_sit_temporary = []
        
        audio_time = re.compile(b'(audio.time.is:.(\d{1,3}\.\d{3}).+?CPA.session.time.is)', flags=re.DOTALL)
        machine = re.compile(b'CPA_MACHINE=(0.\d+)')
        human = re.compile(b'CPA_HUMAN=(0.\d+)')
        fax = re.compile(b'CPA_FAX=(0.\d+)')
        cpa_busy = re.compile(b'CPA_BUSY=(0.\d+)')
        cpa_reorder = re.compile(b'CPA_REORDER=(0.\d+)')
        cpa_sit_permanent  = re.compile(b'CPA_SIT_PERMANENT=(0.\d+)')
        cpa_sit_temporary = re.compile(b'CPA_SIT_TEMPORARY=(0.\d+)')

        with open(filepath, 'r') as log:
            data = mmap.mmap(log.fileno(), 0, prot=mmap.PROT_READ)
            matches = audio_time.findall(data)

            for chunk in matches:
                
                mach_match = machine.findall(chunk[0])
                human_match = human.findall(chunk[0])
                fax_match = fax.findall(chunk[0])
                busy_match = cpa_busy.findall(chunk[0])
                reorder_match = cpa_reorder.findall(chunk[0])
                sit_perm_match = cpa_sit_permanent.findall(chunk[0])
                sit_temp_match = cpa_sit_temporary.findall(chunk[0])

                if (mach_match):
                    self.cpa_machine.append( (chunk[1], mach_match[0]) )

                if (human_match):
                    self.cpa_human.append( (chunk[1], human_match[0]) )

                if (fax_match):
                    self.cpa_fax.append( (chunk[1], fax_match[0]) )

if __name__ == '__main__':
    unit_test = AEParse('/home/tsemczyszyn/WorkLogs/MagNorth/Sangoma_NCA_logs_16_04/tuning_logs_package/1366099479-28125-1934-5740.analyzer-engine.log')










