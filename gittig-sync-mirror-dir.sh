#!/bin/bash
# Usage: gittig-sync-mirror-dir.sh MIRROR_DIRECTORY
time ./gittig sync --dir $1 "${@:2}"
