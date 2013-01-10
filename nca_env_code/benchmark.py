#!/usr/bin/python
# -*- coding: utf-8 -*-
# front end script for the benchmark tool
import getopt
import sys
from subprocess import *

benchmark_tool = "/mnt/iscsi/wc/nca-2.0-maint/bin/netborder_x86_64-linux_gcc34/netborder-benchmark-cpaengine"

config = "./Benchmark.properties"
test_list = "test.audioset"
output_file = "results.txt"

human_th_range = "[0.74,0.78]"
machine_th_range = "[0.50,0.82]"
step_th = "0.01"
global_th = "0.85"

argv = sys.argv
if len(argv) == 0:
    sys.exit()

elif len(argv) > 2:
    print("Error: excess args '%s ...'" % argv[2])
    sys.exit()

else:
	package_dir = argv[1]

print("beggining benchmark of data in '" + package_dir + "'")

#command = [benchmark_tool]
#command.append(options[:])
#options.insert(0, benchmark_tool)

test_list = ''.join([package_dir, test_list])
print("parsing benchmarking data set listed in '" + test_list + "'")

# use the default options list
command = 	[benchmark_tool,
			"--global-config", 
			config, 
			"--input-filename",
			test_list,
			"--human-threshold-range", 
			human_th_range, 
			"--machine-threshold-range",
			machine_th_range,
			"--step-threshold", 
			step_th, 
			"--global-threshold", 
			global_th,
			"--delay-type",
			"START_OF_FILE", 
			"--print"]

print("benchmarking...")
output = Popen(command, stdout=PIPE).communicate()[0]
print("finished benchmark processing.")

print("writing results to => " + output_file)
f = open(output_file, 'w')
f.write(output)
f.close
