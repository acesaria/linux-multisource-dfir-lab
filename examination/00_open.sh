#!/usr/bin/env bash
# 00_open.sh <run_dir>: verify the evidence, find the root filesystem, write investigation/run.env.
. "$(dirname "$0")/lib.sh" "$@"

step D01_disk_hash 'ewfverify -q -d sha256 "$E01" | grep -F "$DISK_SHA"'
step D01_mem_hash  'sha256sum "$MEM" | grep -F "$MEM_SHA"'
step D02_mmls      'mmls "$E01"'

export MNT=/mnt/exam-$RUN_ID/root INV
step D03_mount '
  # /etc/os-release may be a symlink; probe its allocated target with Sleuth Kit.
  OFFSET=
  for s in $(awk '\''$3 ~ /^[0-9]+$/ && $2 !~ /Meta|---/ {print $3+0}'\'' "$OUT/D02_mmls.txt"); do
    if fcat -o "$s" /usr/lib/os-release "$E01" >/dev/null; then OFFSET=$s; break; fi
  done
  [[ -n $OFFSET ]] || { echo "no partition with a readable /usr/lib/os-release; see D02_mmls.txt" >&2; exit 2; }
  ewf=${MNT%/root}/ewf
  if mountpoint -q "$MNT"; then
    LOOPDEV=$(findmnt -n -o SOURCE --mountpoint "$MNT") || exit
  else
    sudo mkdir -p "$ewf" "$MNT" || exit
    if ! mountpoint -q "$ewf"; then
      sudo ewfmount -X ro,allow_other "$E01" "$ewf" || exit
    fi
    LOOPDEV=$(sudo losetup --find --show --read-only --offset "$((OFFSET * 512))" "$ewf/ewf1") || exit
    printf "ENV_RUN_ID=%q\nENV_DISK_SHA=%q\nOFFSET=%q\nMNT=%q\nLOOPDEV=%q\n" "$RUN_ID" "$DISK_SHA" "$OFFSET" "$MNT" "$LOOPDEV" >"$INV/run.env"
    sudo mount -o ro,noload,nodev,nosuid,noexec "$LOOPDEV" "$MNT" || exit
  fi
  printf "ENV_RUN_ID=%q\nENV_DISK_SHA=%q\nOFFSET=%q\nMNT=%q\nLOOPDEV=%q\n" "$RUN_ID" "$DISK_SHA" "$OFFSET" "$MNT" "$LOOPDEV" >"$INV/run.env"
  findmnt --mountpoint "$ewf" && findmnt --mountpoint "$MNT" && sudo losetup --list "$LOOPDEV"
'
. "$INV/run.env"
export OFFSET
need_env
step D02_fsstat     'fsstat -o "$OFFSET" "$E01" | sed -n "1,40p"'
step D02_os_release 'p="$MNT/etc/os-release"; if [[ -L $p ]]; then target=$(readlink "$p") || exit; printf "%s\n" "$target"; if [[ $target == /* ]]; then p="$MNT$target"; else p="${p%/*}/$target"; fi; fi; cat "$p"'
echo; echo "Review before continuing:  $INV/run.env"; cat "$INV/run.env"
grep -E 'File System Type|Last mounted on|Volume Name' "$OUT/D02_fsstat.txt"
grep -E '^(PRETTY_NAME|VERSION_ID)=' "$OUT/D02_os_release.txt"

# Start the scoring table from THIS run's manifest, so it is never copied from another run.
if [[ ! -f $INV/scores.tsv ]]; then
  { printf 'run_id\tclaim\tsource\tstatus\tevidence\tnote\n'
    jq -r --arg r "$RUN_ID" '.claims[].id | ($r+"\t"+.+"\tdisk\t\t\t"), ($r+"\t"+.+"\tram\t\t\t")' "$RUN_DIR/manifest.json"; } >"$INV/scores.tsv"
  echo "Created $INV/scores.tsv"
fi
