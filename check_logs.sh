#!/bin/bash
# find files listed in the passed csv file
csvfile="$1"
[[ -z "$csvfile" ]] && { echo "ERROR: you must pass a csp-stats.csv file as input!"; exit 1; }

searchdir="$2"
[[ -z "$searchdir" ]] && { echo "ERROR: you must pass a directory to search as the 2nd argument"; exit 1; }

sa_package_dir="./sa_package"
if [[ -e $sa_package_dir ]]; then
    echo
    echo "WARNING $sa_package_dir exists!...overwriting" 
else
    mkdir $sa_package_dir
fi

new_dataset_dir="./filtered_logs_set"
if [[ -e $new_dataset_dir ]]; then 
    echo
    echo "WARNING $new_dataset_dir exists!...overwriting" 
    echo
else
    mkdir $new_dataset_dir
fi

# routines
have() { type -P "$1" > /dev/null; }

# an array of log files
declare -a loglist
row=0

# config
z=1
re='.analyzer-engine.0.?'      # to remove in wavs

# pre-detect tools
if have sox; then
    sox_exits=1
else
    echo "SOX is not installed!"
    echo "NOTE: all wav files must be converted to 16 bit LPCM prior to use with cpe offline tool"
    echo "This means all files in $new_dataset_dir will not be in the proper format!"
    sox_exits=0
    exit 1
fi

while read line; do

    # strip everything after the first delimiter (comma) 
    # and use for search pattern
    pat="${line%,2012*}"
    echo
    echo "looking for $pat ..."

    # create an array of the found log files
    loglist=("$(find ./$searchdir -regex "^.*${pat}.*")")

    if [[ -n "${loglist[*]}" ]]; then
        echo "found log files:"
        echo "${loglist[@]}"
        echo


        # keep track of number of wavs (i.e. if there are multiples for a given call log)
        # wavs=($(gawk 'BEGIN { ORS="\n"} /wav/ { print $0; printf("%c", "") }'| sort <<< "${loglist[@]}"))
        wavs=($(gawk '/wav/ { print $0 }' <<< "${loglist[@]}"))
        # echo "wavs @ 0 = ${wavs[0]}"
        # echo "wavs @ 1 = ${wavs[1]}"

        # if no wav files don't include
        if [[ -z "${wavs[*]}" ]]; then
            echo "NO WAV FILES FOUND!...skipping call!"
            continue
            exit
        else
            echo -e "\twavs are:"
            echo -e "\t${wavs[@]}"
            echo
            newname="${wavs[0]/$re/}"

            # keep track of the number of files
            ((count++))

        fi

        for file in ${loglist}; do

            # if file is a wav
            if [[ $file =~ $re ]]; then

                # skip wavs for now
                continue
            else
                # copy all other log files
                echo -e "\tcopying file: $file to $sa_package_dir"
                cp --parents $file $sa_package_dir

                echo -e "\tcopying file: $file to $new_dataset_dir"
                cp --parents $file $new_dataset_dir
            fi
        done
        echo

        # reset concat flag
        combine_flag=""


        # check for sox conversion tool
        if (($sox_exits)) && [[ -n "${wavs}" ]]; then

            # check if there is more then one wave file in this log set
            if (( ${#wavs[*]} > 1)); then
                echo "there is > 1 wav file!"

                # reverse order of wavs
                let length=${#wavs[@]}
                for file in "${wavs[@]}"; do
                    sorted_wavlist[length]=$file
                    # let "length -= 1"
                    (( length -= 1 ))
                done

                echo "will concatenate the following files:"
                echo "${sorted_wavlist[@]}"

                # if there are > 1 wav files : concatenate with sox
                combine_flag="--combine concatenate"
                # exit
            else
                echo -e "\tdid not get > 1 wavs!"
            fi

            # process the wav files
            echo -e "\tfor stats analyzer, should be renamed to:" 
            echo -e "\t${newname}"
            echo

            declare -a infile=${sorted_wavlist[@]:-${wavs[0]#./}}
            outfile=${sorted_wavlist[0]:-${wavs[0]#./}}
            echo "sorted_wavlist = ${sorted_wavlist[@]#./}"
            echo "wavs = ${wavs[0]#./}"
            echo "infile = $infile"

            # concat multiple files for stats analyzer
            echo "first sox"
            sox -S ${combine_flag} $infile ${sa_package_dir}/${newname#./}

            echo "2nd sox"
            # convert audio to linear for cpe offline tool
            sox -S ${combine_flag} ${infile/\.\//} -b 16 -e signed "${new_dataset_dir}/${outfile}"

        else
            # this probably doesn't work currently
            for file in ${wavs[@]}; do
                # if no sox (currently should never get here)
                cp --parents $file "$new_dataset_dir"
                # rename for stats analyzer tool
                cp --parents $file "$sa_package/$newname"
            done
        fi
    else
        echo "NO LOG FILES FOUND! with pattern: $pat"
        echo
    fi
    unset loglist
    unset wavs
    unset sorted_wavlist
    unset infile
done < $csvfile

# filter csv to skip title and field names
linecount="$(gawk '/\,/ { if(NR == 2){next}; count++ } END { print count}' $csvfile )"
echo
echo "number of files found with wavs = $count"
echo "line count in provided csv file '$csvfile' is $linecount"
echo
unset count

cp $csvfile "$sa_package_dir/cpa-stats.csv"
cp $csvfile "$new_dataset_dir/cpa-stats.csv"

cd $sa_package_dir
if (( z == 1 )); then
    echo "zipping up package..."
    zip -r package.zip ./* > /dev/null
fi
echo
echo "New stats-analyzer package is => $sa_package_dir"
echo "New generic package is => $new_dataset_dir"
echo "done."
