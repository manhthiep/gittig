#!/bin/bash
# Usage: gittig-clone-mirror-url.sh GIT_REPO_URL
time ./gittig clone --mirror --url="$1" "${@:2}"
