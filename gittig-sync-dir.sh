#!/bin/bash
# Usage: gittig-sync-dir.sh MIRROR_DIRECTORY
time ./gittig sync --dir $1 "${@:2}"
