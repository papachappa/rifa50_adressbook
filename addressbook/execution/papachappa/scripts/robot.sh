#!/bin/bash

#dt=`date+%Y_%m_%d`
#tm=`date +%H_%M`
#testnum="0"
##/"$dt"_"$tm"_"$testnum"\
path="/home/papachappa/sbc/robot/functional_tests/robot/implementation/testsuites/QA_testsuite/"
varfile="/home/papachappa/sbc/robot/functional_tests/robot/execution/papachappa/settings/env_settings.py"

pybot -d reports\
      -b debug.log \
      -L DEBUG:INFO \
      -x result \
      -W `tput cols` \
      -e inworkORdisable \
      --variablefile $varfile \
      $path #/"$testnum"*
