#!/usr/bin/env bash
# 30_timeline.sh <run_dir> [STEP_ID]: fixed timeline sweep. Same commands for every run; nothing scenario-specific.
. "$(dirname "$0")/lib.sh" "$@"; need_env
export RUN_DIR

step T02_log2timeline '
  rm -f "$DATA/timeline.plaso" || exit
  year=$(jq -er '\''.timestamps.scenario_started_at[:4]'\'' "$RUN_DIR/manifest.json") || exit
  partition=$(awk -v offset="$OFFSET" '\''$3+0 == offset && $2 ~ /^[0-9]+$/ {print $2+1}'\'' "$OUT/D02_mmls.txt") || exit
  [[ $partition =~ ^[0-9]+$ ]] || { echo "no unique root partition in D02_mmls.txt" >&2; exit 2; }
  log2timeline --storage-file "$DATA/timeline.plaso" --preferred-year "$year" --partitions "$partition" --logfile "$OUT/T02_log2timeline.log.gz" "$E01"
'
step T02_pinfo 'pinfo "$DATA/timeline.plaso"'
step T02_timeline 'rm -f "$DATA/timeline.csv" && psort -q --status_view none --output-time-zone UTC -o dynamic --fields datetime,timestamp_desc,source,parser,message,display_name --logfile "$OUT/T02_psort.log.gz" -w "$DATA/timeline.csv" "$DATA/timeline.plaso" && cat "$DATA/timeline.csv"'
step T02_window 'python3 - <<'\''PY'\''
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

manifest = json.loads((Path(os.environ["RUN_DIR"]) / "manifest.json").read_text())
start = datetime.fromisoformat(manifest["timestamps"]["scenario_started_at"].replace("Z", "+00:00"))
end = datetime.fromisoformat(manifest["timestamps"]["run_ended_at"].replace("Z", "+00:00"))
start = start.astimezone(timezone.utc).isoformat(timespec="microseconds")
end = end.astimezone(timezone.utc).isoformat(timespec="microseconds")
count = 0
with (Path(os.environ["OUT"]) / "T02_timeline.txt").open(newline="") as source:
    reader = csv.reader(source)
    writer = csv.writer(sys.stdout, lineterminator="\n")
    writer.writerow(next(reader))
    for row in reader:
        # UTC ISO strings leave unknown Plaso timestamps outside the window.
        if start <= row[0] <= end:
            writer.writerow(row)
            count += 1
sys.exit(0 if count else 1)
PY'
