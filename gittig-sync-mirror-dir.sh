#!/bin/bash
# Usage: gittig-sync-mirror-dir.sh MIRROR_DIRECTORY
./gittig sync --local-dir $1 "${@:2}"
