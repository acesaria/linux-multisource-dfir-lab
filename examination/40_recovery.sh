#!/usr/bin/env bash
# 40_recovery.sh <run_dir> [STEP_ID]: fixed deleted-file recovery. Same commands for every run; nothing scenario-specific.
. "$(dirname "$0")/lib.sh" "$@"; need_env
export RUN_DIR

step R01_version 'ext4magic -V'
step R01_recover '
  start=$(jq -er '\''.timestamps.scenario_started_at'\'' "$RUN_DIR/manifest.json") || exit
  end=$(jq -er '\''.timestamps.run_ended_at'\'' "$RUN_DIR/manifest.json") || exit
  start=$(date -d "$start" +%s) || exit
  end=$(date -d "$end" +%s) || exit
  sudo ext4magic "$LOOPDEV" -a "$start" -b "$end" -r -d "$DATA/recovered"
'
step R01_hashes 'sudo find "$DATA/recovered" -type f -exec sha256sum {} + | grep .'
