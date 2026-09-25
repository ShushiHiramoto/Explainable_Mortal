#!/bin/bash

# Create a temporary empty hooks directory to bypass NVIDIA hook
TMP_HOOKS_DIR=$(mktemp -d)
trap "rm -rf $TMP_HOOKS_DIR" EXIT

docker run --rm \
   -v .://workspace/mortal \
   -w //workspace/mortal \
   --entrypoint bash \
   explainable-mortal \
   -c "cargo build -p libriichi --lib --release && cp target/release/libriichi.so mortal/"