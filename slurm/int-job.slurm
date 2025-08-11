#!/bin/bash


mem_request="1G"
partition="cs05r"
logDir="~/MyDB/logs"
logFile="int-job_%j.log"
interactive=false
Help=false

echo $logDir/$logFile 

if [[ "$#" -eq 0 ]]; then
	cat << EOF
-d (default - run default settings)
--mem (memory i.e. 1G)
--part (partition i.e. cs05r)
--logD (log directory - default = ~/MyDB/logs)
--logF (log file name - default = int-job_%j.job)
--int (interactive bool - default false > save in log file )
--help (bool)
EOF

exit 0
fi

# Use a while loop to iterate through all command-line arguments
# The loop continues as long as there are arguments to process ($# - number of arguments)
while [[ "$#" -gt 0 ]]; do
    case "$1" in
	-d)
	break
	;;
        # Check for the --mem flag
        --mem)
            # The next argument ($2) is the value for --output
            mem_request="$2"
            # Shift twice to move past the flag and its value
            shift
            shift
            ;;
        # Check for the --partition flag
        --part)
            # The next argument ($2) is the value for --name
            partition="$2"
            shift
            shift
            ;;
	--logD)
	   logDir="$2"
	   shift
	   shift
	   ;;
	--logF)
	   logFile="$2"
	   shift
	   shift
	   ;;
	--int)
	   interactive=true
	   shift
	   ;;
        # Check for the --verbose flag (which doesn't have a value)
        --verbose)
            verbose=true
            # Shift once to move past the flag
            shift
            ;;
	--help)
	   Help=true
	   shift
	   ;;
	# Handle any other unrecognized arguments
        *)
            echo "Error: Unrecognized argument '$1'"
            exit 1
            ;;
    esac
done

if [[ $Help == "true" ]]; then
	cat << EOF
--mem (memory i.e. 1G)
--part (partition)
--logD (log directory)
--logF (log file name)
--int (interactive bool)
--help (bool)
EOF

exit 0
fi


if [[ $interactive == true ]]; then
	srun -p $partition --mem $mem_request --pty bash
else
	srun -p $partition -o ./logs/int-job_%j.out --mem $mem_request -u bash ./run-codeserver.sh #. /test.sh

	#./run-codeserver.sh 
fi

# bash run-codeserver.sh
