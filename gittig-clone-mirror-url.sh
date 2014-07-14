#!/bin/bash
# Usage: gittig-clone-mirror-url.sh GIT_REPO_URL
./gittig clone --mirror --url="$1" "${@:2}"
