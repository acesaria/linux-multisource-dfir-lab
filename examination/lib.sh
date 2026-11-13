# lib.sh: sourced by every examination script as:  . "$(dirname "$0")/lib.sh" <run_dir> [STEP_ID]
# Gives: run identity checks, evidence paths, and step() which records every command it runs.
set -u -o pipefail
export TZ=UTC LC_ALL=C
die() { echo "ERROR: $*" >&2; exit 2; }

[[ -n ${1:-} ]] || die "usage: $0 <run_dir> [STEP_ID]"
RUN_DIR=$(cd "$1" && pwd) || die "no such run directory: $1"
ONLY=${2:-}                                   # optional: rerun just this step
INV=$RUN_DIR/investigation; OUT=$INV/outputs; DATA=$INV/data
mkdir -p "$OUT" "$DATA"

RUN_ID=$(jq -er .run_id "$RUN_DIR/manifest.json") || die "manifest.json has no run_id"
[[ $RUN_ID == "$(basename "$RUN_DIR")" ]] || die "manifest run_id '$RUN_ID' is not the directory name"
ACQ=$RUN_DIR/dumps/acquisition.json
E01=$RUN_DIR/dumps/$(jq -er .disk.path "$ACQ");   DISK_SHA=$(jq -er .disk.sha256 "$ACQ")
MEM=$RUN_DIR/dumps/$(jq -er .memory.path "$ACQ"); MEM_SHA=$(jq -er .memory.sha256 "$ACQ")
SYMBOLS=${SYMBOLS:-$RUN_DIR/../../isf}
export RUN_ID E01 MEM DISK_SHA MEM_SHA SYMBOLS OUT DATA

# run.env holds values derived from THIS evidence by 00_open.sh. Refuse one that came from another run.
if [[ -f $INV/run.env ]]; then
  set -a; . "$INV/run.env"; set +a
  [[ ${ENV_RUN_ID:-} == "$RUN_ID" && ${ENV_DISK_SHA:-} == "$DISK_SHA" ]] \
    || die "investigation/run.env was derived from another run (${ENV_RUN_ID:-?}); delete it and rerun 00_open.sh"
fi
need_env() {
  [[ -n ${OFFSET:-} ]] || die "no run.env yet: run 00_open.sh first"
  [[ -n ${MNT:-} ]] && mountpoint -q "$MNT" || die "evidence root is not mounted (${MNT:-unset}): run 00_open.sh first"
}

# step ID 'command'   Runs the command, keeps native stdout, stderr and exit status, logs one row.
# rc=0 means the command (or its final grep) succeeded; a non-zero rc is a recorded result, not a crash.
step() {
  local id=$1 cmd=$2 rc lines
  [[ -z $ONLY || $id == "$ONLY" ]] || return 0
  bash -o pipefail -c "$cmd" >"$OUT/$id.txt" 2>"$OUT/$id.err"; rc=$?
  [[ -s $OUT/$id.err ]] || rm -f "$OUT/$id.err"
  lines=$(wc -l <"$OUT/$id.txt")
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$RUN_ID" "$id" "$rc" "$lines" "$(date -u +%FT%TZ)" "${cmd//$'\n'/\\n}" >>"$OUT/_steps.tsv"
  printf '%-24s rc=%-3s lines=%s\n' "$id" "$rc" "$lines"
}
