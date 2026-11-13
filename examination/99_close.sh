#!/usr/bin/env bash
# 99_close.sh <run_dir>: release this run's read-only evidence mount.
. "$(dirname "$0")/lib.sh" "$@"
export MNT=${MNT:-/mnt/exam-$RUN_ID/root}

step D99_close '
  ewf=${MNT%/root}/ewf
  if mountpoint -q "$MNT"; then sudo umount "$MNT" || exit; fi
  if [[ -n ${LOOPDEV:-} ]]; then
    backing=$(sudo losetup --list --noheadings --output BACK-FILE "$LOOPDEV") || exit
    if [[ -n $backing ]]; then
      [[ $backing == "$ewf/ewf1" ]] || { echo "loop device belongs to another image: $LOOPDEV ($backing)" >&2; exit 2; }
      sudo losetup --detach "$LOOPDEV" || exit
    fi
  fi
  if mountpoint -q "$ewf"; then sudo umount "$ewf" || exit; fi
  for d in "$MNT" "$ewf"; do
    if [[ -d $d ]]; then sudo rmdir "$d" || exit; fi
  done
'
