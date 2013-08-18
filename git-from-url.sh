#!/bin/bash
# Usage: git-from-url.sh URL
./pygit.py clone --url=$1 "${@:2}"
