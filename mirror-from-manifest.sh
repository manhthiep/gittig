#!/bin/bash
# Usage: mirror-from-manifest.sh MANIFEST_FILE
./pygit.py clone --mirror --manifest=$1 "${@:2}"
