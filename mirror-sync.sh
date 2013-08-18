#!/bin/bash
# Usage: mirror-sync.sh MIRROR_DIRECTORY
./pygit.py sync -d $1 "${@:2}"
