#!/bin/bash
# Tyler Goodlet tgoodlet@sangoma.com -- initial version
# process audio files with cpe

usage () {
cat << HERE 

Usage:
This script expects a directory name as input.
The directory must contain .wav and corresponding .cdr.xml 
files to be processed by the offline cpe engine.

example: ./cpaengine.sh <dir full of wavs and xml files>

HERE
}

# Start of script
script_dir=$PWD
#mkdir "offline_engine_output_files"
if [[ $# < 1 ]]; then
	usage && exit 1
else
	dir="$1"
fi

# jump into the package dir and collect files
cd $dir
wavlist=(*.wav)
xmllist=(*.xml)

# move all the relevant files to PWD
echo
echo -e "wavlist is :"
for file in "${wavlist[@]}"; do
	# build arrays of wav and xml files from user specified dir
	echo "$file"
	cp $file $script_dir
done

echo
echo -e "xmllist is :"
for file in "${xmllist[@]}"; do
	echo "$file"
	cp $file $script_dir
done

# move back to our processing dir
echo
cd $script_dir

for wavfile in "${wavlist[@]}"; do
	echo "calling 'netborder-evaluate-with-cpaengine' on '$wavfile'"
	outfile="OUT-${wavfile}"

#netborder-evaluate-with-cpaengine --global-config CPAEngine.properties --input-filename $wavfile --output-filename out-${wavfile}.wav --include-probability CPA_HUMAN

# prob order is HUMAN, MACHINE, FAX
	netborder-evaluate-with-cpaengine --global-config CPAEngine.properties --input-filename $wavfile --output-filename $outfile --include-probability CPA_HUMAN --include-probability CPA_MACHINE --include-probability CPA_FAX
	echo "output file: $outfile"
	echo
done

# grab output files
outlist=(OUT-*)
echo "copying:"
for file in "${outlist[@]}"; do
	echo "$file -> $dir"
	cp $file $dir
done

#clean up
echo
echo "cleaning up!..."

for file in "*.wav"; do
	rm $file
done
 
for file in "*.xml"; do
	rm $file
done

echo "done!"
