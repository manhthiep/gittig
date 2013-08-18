#!/bin/bash
# Usage: git-from-manifest.sh MANIFEST_FILE
./pygit.py clone --manifest=$1 "${@:2}"
