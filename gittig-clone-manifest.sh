#!/bin/bash
# Usage: gittig-clone-manifest.sh MANIFEST_FILE
time ./gittig clone --manifest=$1 "${@:2}"
