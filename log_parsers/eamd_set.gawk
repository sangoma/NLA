#!/bin/gawk -f

# usage:
#grep -ir '<EamdOn>1</EamdOn>' * | gawk 'BEGIN{FS="."} {cid[$1]++} END{for(i in cid)print i}'

# strings to 'grep' for
s1 = "<EamdOn>1</EamdOn>"
s2 = "CPA-IsEamdEnabled"

/s1/ & /s2/

#WORK IN PROGRESS!....
