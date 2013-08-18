#!/bin/bash
# Usage: mirror-from-url.sh URL
./pygit.py clone --mirror --url=$1 "${@:2}"
