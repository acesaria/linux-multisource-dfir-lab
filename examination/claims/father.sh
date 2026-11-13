#!/usr/bin/env bash
# claims/father.sh <run_dir> [STEP_ID]: targeted checks for the father scenario, one or more per claim.
# The constants below come from the scenario definition (ground truth), never from another run's evidence.
# Convention: rc=0 means the predicate matched. On a control run every C_ step must end non-zero.
. "$(dirname "$0")/../lib.sh" "$@"; need_env
export IMPLANT=/usr/lib/selinux.so.3 IMPLANT_CFG=/lib/selinux.so.3 REF=/usr/lib/x86_64-linux-gnu/libc.so.6
export STAGED=/tmp/rk.so HARVEST=/tmp/__malicious_harvest RECON=/tmp/__malicious_recon
export IMPLANT_SHA=$(jq -er '.inputs[0].artifacts[0].sha256' "$RUN_DIR/manifest.json")
V='vol3 -q -s "$SYMBOLS" -f "$MEM"'
# cached FILE -> dump its page cache to data/ram/<label> and print sha256 (address parsed from the Files row)
ramfile() { echo "mkdir -p \"\$DATA/ram/$1\"; $V linux.pagecache.Files --find $2 | tee /dev/stderr | awk -F'\\t' -v p=$2 '\$13==p{print \$5}' | head -1 | xargs -r -I{} $V -o \"\$DATA/ram/$1\" linux.pagecache.InodePages --inode {} --dump >&2; sha256sum \"\$DATA/ram/$1\"/*.dmp"; }

# preload_persistence
step C_preload_disk      'grep -F "$IMPLANT_CFG" "$MNT/etc/ld.so.preload"'
step C_timeline_preload  'grep -F "/etc/ld.so.preload" "$OUT/T02_window.txt"'
step C_preload_ram       "$(ramfile preload /etc/ld.so.preload) && grep -aF \"\$IMPLANT_CFG\" \"\$DATA/ram/preload\"/*.dmp"
# implant_timestomp: mtime equals the reference mtime AND is older than the file's own creation time
step C_timestomp_disk    'stat --printf="%n\t%y\t%w\n" "$MNT$IMPLANT" "$MNT$REF" | awk -F "\t" '\''{print; m[NR]=$2; c[NR]=$3} END{exit !(NR==2 && m[1]!="" && m[1]==m[2] && c[1]!="-" && c[1]>m[1])}'\'''
step C_timestomp_ram     "($V linux.pagecache.Files --find \$IMPLANT && $V linux.pagecache.Files --find \$REF) | awk -F'\t' -v p=\"\$IMPLANT\" -v r=\"\$REF\" '{print} \$13==p{m=\$11; a=1} \$13==r{n=\$11; b=1} END{exit !(a && b && m!=\"\" && m==n)}'"
# credential_staging: staged copy is byte-identical to /etc/shadow, mode 0600
step C_harvest_disk      'a=$(sudo sha256sum "$MNT$HARVEST") || exit; b=$(sudo sha256sum "$MNT/etc/shadow") || exit; printf "%s\n" "$a" "$b"; mode=$(stat -c %a "$MNT$HARVEST") || exit; printf "mode=%s\n" "$mode"; [[ ${a%% *} == "${b%% *}" && $mode == 600 ]]'
step C_harvest_ram       "$(ramfile harvest \$HARVEST)"
# recon_staged
step C_recon_disk        'head -5 "$MNT$RECON" | grep -E "uid=|Linux "'
step C_recon_ram         "$(ramfile recon \$RECON)"
# runtime_loading_backdoor: processes mapping the implant, and their sockets
step C_implant_disk      'sha256sum "$MNT$IMPLANT" | grep -F "$IMPLANT_SHA"'
step C_runtime_ram_maps  'grep -F "$IMPLANT_CFG" "$OUT/M03_libraries.txt"'
step C_runtime_ram_socks 'for pid in $(awk -F"\t" "\$4 ~ /selinux\.so\.3/ {print \$2}" "$OUT/M03_libraries.txt" | sort -u); do awk -F"\t" -v p=$pid "\$3==p && /ESTABLISHED/" "$OUT/M04_sockstat.txt"; done | grep .'
# deleted_staging_artifact: a deleted name, or the implant bytes outside any allocated file
step C_staged_disk_name  'grep -P "\t${STAGED#/}( \(realloc\))?$" "$OUT/FS02_deleted.txt"'
step C_staged_disk_recovered 'grep -E "^${IMPLANT_SHA}[[:space:]]" "$OUT/R01_hashes.txt"'
step C_staged_ram_name   "$V linux.pagecache.Files --find \$STAGED | grep -F \$STAGED"
# shell_history_cleanup: only a positive trace counts (a cleanup command recovered somewhere)
step C_history_disk      'grep -aE "history -c|unset HISTFILE|bash_history" "$OUT/FS04_authlog.txt" "$OUT/FS04_journal.txt"'
step C_history_ram       'grep -E "history -c|unset HISTFILE|bash_history" "$OUT/M05_bash.txt"'
