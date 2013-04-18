#!/bin/gawk -f

# usage:
#grep -ir '<number string>' * | unique_cids.gawk

BEGIN {
	FS="."
}

{
	# compile unique ids
	cid[$1]++
}

END {
	for(i in cid) {
		print i
	}
}
