#!/bin/bash
source common
echo "Stopping the slice"
ExecEach sudo systemctl stop vula.slice
ExecEach sudo systemctl stop vula-organize-monolithic.service
echo "Starting everything"
ExecEach vula start

# FIXME: this script exists because of a race condition, which causes peers to
# not be discovered if all of the services are restarted rapidly one host at a
# time (as opposed to restarting publish after all hosts have restarted their
# discovers already, as is done above). To see if the race still exists, run
# retest.sh after uncommenting these two lines and commenting out the lines
# above:
#echo "Restarting everything together... does this work?"
#ExecEach sudo systemctl restart vula-{publish,discover,organize,petname}


