#!/bin/bash
# Usage: gittig-clone-url.sh GIT_REPO_URL
time ./gittig clone --url="$1" "${@:2}"
