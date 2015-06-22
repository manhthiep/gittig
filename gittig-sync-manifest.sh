#!/bin/bash
# Usage: gittig-sync-manifest.sh MANIFEST_FILE
time ./gittig sync --manifest=$1 "${@:2}"
