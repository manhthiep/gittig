#!/bin/bash
# Usage: gittig-clone-mirror-manifest.sh MANIFEST_FILE
./gittig clone --mirror --manifest=$1 "${@:2}"
