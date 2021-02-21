#!/bin/bash
dir=$(ls)
subdir=$(ls scripts)

if [[ $dir == *"pages"* ]]; then rm -rf pages; fi

if [[ $dir == *"psengine.db"* ]]; then rm psengine.db; fi

if [[ $dir == *"invalidurls"* ]]; then rm invalidurls; fi

if [[ $subdir == *"__pycache__"* ]]; then rm -rf scripts/__pycache__; fi
