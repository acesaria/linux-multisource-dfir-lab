#!/usr/bin/env bash
# 00_open.sh <run_dir>: verify the evidence, find the root filesystem, write investigation/run.env.
. "$(dirname "$0")/lib.sh" "$@"

step D01_disk_hash 'ewfverify -q -d sha256 "$E01" | grep -F "$DISK_SHA"'
step D01_mem_hash  'sha256sum "$MEM" | grep -F "$MEM_SHA"'
step D02_mmls      'mmls "$E01"'

# Root filesystem = the first partition where Sleuth Kit can read /etc/os-release. No offset is typed.
OFFSET=
for s in $(awk '$3 ~ /^[0-9]+$/ && $2 !~ /Meta|---/ {print $3+0}' "$OUT/D02_mmls.txt"); do
  if fcat -o "$s" /etc/os-release "$E01" >/dev/null 2>&1; then OFFSET=$s; break; fi
done
[[ -n $OFFSET ]] || die "no partition with a readable /etc/os-release (unsupported filesystem?). See outputs/D02_mmls.txt"

{ echo "ENV_RUN_ID=$RUN_ID"; echo "ENV_DISK_SHA=$DISK_SHA"; echo "OFFSET=$OFFSET"; } >"$INV/run.env"
export OFFSET
step D02_fsstat     'fsstat -o "$OFFSET" "$E01" | head -40'
step D02_os_release 'fcat -o "$OFFSET" /etc/os-release "$E01"'
echo; echo "Review before continuing:  $INV/run.env"; cat "$INV/run.env"
grep -E 'File System Type|Last mounted on|Volume Name' "$OUT/D02_fsstat.txt"
grep -E '^(PRETTY_NAME|VERSION_ID)=' "$OUT/D02_os_release.txt"

# Start the scoring table from THIS run's manifest, so it is never copied from another run.
if [[ ! -f $INV/scores.tsv ]]; then
  { printf 'run_id\tclaim\tsource\tstatus\tevidence\tnote\n'
    jq -r --arg r "$RUN_ID" '.claims[].id | ($r+"\t"+.+"\tdisk\t\t\t"), ($r+"\t"+.+"\tram\t\t\t")' "$RUN_DIR/manifest.json"; } >"$INV/scores.tsv"
  echo "Created $INV/scores.tsv"
fi
