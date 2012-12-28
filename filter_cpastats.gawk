#!/bin/gawk -f

# Default fields of the csv in order are:
# Netborder Call-id,Call Date,Reference ID,Campaign Name,Phone Number,
# NCA Engine Result,Time Dialing,Time Connected,Time NCA Engine Completed,
# Time Queued,Time Connected to Agent,Detailed Cpd Result
BEGIN { 

	# configure output options
	stats  = 1
	filter = 1
	rando  = 0

	output = 0
	output_file = "results.txt"

	FS="," 

	# hard code the fields of interest (see ordering above)
	nbe_cid       = 1 #Netborder Call-id
	call_date     = 2
	number        = 5
	cpe_result    = 6
	detail_result = 12
	random_field  = 15
}
# only comma delimited lines
FNR==NR {

	if( filter = 1) {

		# print the title line
		if (NR == 1) { title = $0; print; next }

		# print the second line
		if (NR == 2) { field_record = $0; print; next }

		# skip all lines with results we don't need
		if( $cpe_result ~ /No-/ || $cpe_result ~ /Service-Unavailable/ || $cpe_result ~ /Invalid-Number/) {
			next
			# do other shit like log call id and move files to a new dir for later processing
		}

		# remove calls marked as rejects
		#if( $detail_result ~ /Reject/) {
			#next
			# do other shit like log call id and move files to a new dir for later processing
		#}

		if($number in phonenum) {
			if (stats == 1) {
				print "CALL TO DUPLICATE NUMBER : " $number 
				print " ...skipping record: " NR "\n"
			}

			# update entry count in our database
			phonenum[$number]++

			# skip this call since we've already called it
			next

		}else{

			# add entries which have not been added yet (only works if output flag is on)
			lastcall[$number] = $0

			# insert entry to our database
			phonenum[$number]++

			# output all allowed records
			print
		}
	}

	#check formatting (put in own routine?)
	#if (NF != 12) {
		# ignore
	#	print "detected non-formatted line!"
	#}else{

	# stats arrays
		# NOTE: all gawk arrays are associative
		cpe_res_count[$cpe_result]++
		detail-res_count[$detail_result]++

	# assuming random field points to marking of correct vs. incorrect dispositions
		mark = $random_field
		correct_result[mark]++

		# sum up all dispositions
		dispsum++
	#}
}


END { 

	# random info
	if( rando == 1 ) {
		for( i in phonenum) { 
			print(i " has been called " phonenum[i] " times")
			print("last line is : " lastcall[i])
		}
	}

	# output to file?
	if( output == 1) {
		# print preferred output to a file
		print title > output_file
		print field_record > output_file
		for( i in lastcall) {
			print(lastcall[i]) > output_file
		}
	}
	
	#n = asort(cpe_res_count, sorted_cpe_res, "@val_num_desc")

	# print stats?
	if( stats == 1) {
		# print the results
		print "\n"
		print "Redundancy:"
		for(num in phonenum) {
			if( phonenum[num] > 1) {
				print "number: " num " was called " phonenum[num] " times"
			}
		}

		print "\n"
		print "Summary:"
		for(i in cpe_res_count) {
			percent[i] = 100 * cpe_res_count[i] / dispsum

			# printf fields format: %<sign><zero><width>.<precision>format
			printf("%-6d %-20s  %-5.1f (%)\n", cpe_res_count[i], i, percent[i])
		}
		print "---"
		printf("%-6d total\n", dispsum)

		print "\n"
		print "Performance:"
		for(i in correct_result) {
			print i " marked " correct_result[i] " times"
		}
	}
}
