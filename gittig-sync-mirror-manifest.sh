#!/bin/bash
# Usage: gittig-sync-mirror-manifest.sh MANIFEST_FILE
time ./gittig sync --mirror --manifest=$1 "${@:2}"
