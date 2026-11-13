#!/usr/bin/env bash
# pivot.sh <run_dir> <P##_name> '<command>': run one exploratory command and record it like any other step.
# Literal inodes, PIDs and addresses are fine here: the row is logged under this run only.
. "$(dirname "$0")/lib.sh" "$1"; need_env
[[ ${2:-} == P[0-9][0-9]_* && -n ${3:-} ]] || die "usage: pivot.sh <run_dir> P01_name 'command'"
step "$2" "$3"; cat "$OUT/$2.txt"
