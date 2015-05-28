#!/bin/bash
# Usage: gittig-clone-mirror-manifest.sh MANIFEST_FILE
time ./gittig clone --mirror --manifest=$1 "${@:2}"
