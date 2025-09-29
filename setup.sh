#!/bin/bash

set -e

TPAR_DIR="external/t-par"

if [ ! -f "$TPAR_DIR/Makefile" ]; then
  echo "Error: Makefile not found in $TPAR_DIR"
  exit 1
fi

echo "Building t-par in $TPAR_DIR ..."
cd "$TPAR_DIR"
make

echo "t-par build complete."
