#!/usr/bin/env bash
# 20_memory.sh <run_dir> [STEP_ID]: fixed memory sweep. Same commands for every run.
. "$(dirname "$0")/lib.sh" "$@"
V='vol3 -q -s "$SYMBOLS" -f "$MEM"'

step M01_banners    'vol3 -q -f "$MEM" banners.Banners'
step M02_pslist     "$V linux.pslist.PsList"
step M02_pstree     "$V linux.pstree.PsTree"
step M03_libraries  "$V linux.library_list.LibraryList"
step M04_sockstat   "$V linux.sockstat.Sockstat"
step M05_bash       "$V linux.bash.Bash"
step M06_files      "$V linux.pagecache.Files"
step M06_persistence 'grep -P "\t/(etc/(ld\.so\.preload|rc\.local|crontab)|etc/cron\.[a-z]+/.+|var/spool/cron/.+|etc/systemd/system/[^/]+\.(service|timer))\t" "$OUT/M06_files.txt"'
step M06_tmp        'grep -P "\t/(tmp|var/tmp|dev/shm)/[^\t]+\t" "$OUT/M06_files.txt"'
step M08_modules    "$V linux.malware.hidden_modules.Hidden_modules"
step M09_malfind    "$V linux.malware.malfind.Malfind"
