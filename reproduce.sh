#!/bin/bash
# One-command reproduction for the crypto-forensics magazine note.
# Verifies the headline numbers against the frozen analysis data files.
# Requires: python3 only.
set -e
cd "$(dirname "$0")"
python3 verify.py
