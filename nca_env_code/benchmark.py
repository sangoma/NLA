#!/usr/bin/python
# -*- coding: utf-8 -*-
# front end script for the benchmark tool
import getopt
import sys
from subprocess import *
import os

benchmark_tool = os.path.expandvars("$PARAXIP/bin/netborder_x86_64-linux_gcc34/netborder-benchmark-cpaengine")

config = "./Benchmark.properties"
test_list = "test.audioset"

output_file = "results.txt"
op_csv_file = "results.csv"

# choose which option : csv or text file output
options = ['--output-csv', op_csv_file]
#options = ['--print']

if not os.path.exists(config):
	print("E: no configuration file detected!?" + config)
	sys.exit(1)

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
	package_dir = os.path.abspath(argv[1])

	print("re-writing" + test_list + " with absolute paths...\n")
	paths = []
	t = open(os.path.join(package_dir, test_list), 'r+')
	paths = map(os.path.abspath, t.readlines())
	t.close()

	t = open(os.path.join(package_dir, test_list), 'w+')
	t.writelines(paths)
	t.close()

	print("beggining benchmark of data in '" + package_dir + "'")

#command = [benchmark_tool]
#command.append(options[:])
#options.insert(0, benchmark_tool)

	test_list = os.path.join(package_dir, test_list)
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
				"START_OF_FILE"]

	print("benchmarking...")
	output = Popen(command + options, stdout=PIPE).communicate()[0]
	print("finished benchmark processing.")

	print("writing results to => " + output_file)
	f = open(output_file, 'w')
	f.write(output)
	f.close
