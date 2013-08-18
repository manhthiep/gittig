#!/bin/bash
# Usage: git-sync.sh WORKING_DIRECTORY
./pygit.py sync -d $1 "${@:2}"
