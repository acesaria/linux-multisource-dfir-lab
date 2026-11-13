#!/usr/bin/env bash
# 10_disk.sh <run_dir> [STEP_ID]: fixed disk sweep. Same commands for every run; nothing scenario-specific.
. "$(dirname "$0")/lib.sh" "$@"; need_env
F='-o "$OFFSET"'    # every Sleuth Kit call reads by path at the derived offset

step FS01_fstab       "fcat $F /etc/fstab \"\$E01\""
step FS01_timezone    "fcat $F /etc/timezone \"\$E01\""
step FS02_fls         "fls -r -p $F \"\$E01\""
step FS02_deleted     'grep -F "*" "$OUT/FS02_fls.txt"'
step FS02_varlog      'grep -P "\tvar/log/[^/]+(/[^/]+)?$" "$OUT/FS02_fls.txt"'
step FS03_persistence 'grep -P "\t(etc/(ld\.so\.preload|rc\.local|crontab)|etc/cron\.[a-z]+/.+|var/spool/cron/.+|etc/systemd/system/[^/]+\.(service|timer))$" "$OUT/FS02_fls.txt"'
step FS03_startup     'grep -P "\t(etc/(profile|bash\.bashrc)|etc/profile\.d/.+|(home/[^/]+|root)/\.(profile|bashrc|bash_profile|bash_login))$" "$OUT/FS02_fls.txt"'
step FS03_ssh_keys    'grep -P "\t(home/[^/]+|root)/\.ssh/authorized_keys2?$" "$OUT/FS02_fls.txt"'
step FS03_tmp         'grep -P "\t(tmp|var/tmp|dev/shm)/" "$OUT/FS02_fls.txt"'
step FS04_history     'grep -P "\t(home/[^/]+|root)/(\.[^/]*_history|\.viminfo|\.lesshst)$" "$OUT/FS02_fls.txt"'
step FS04_accounts    "fcat $F /etc/passwd \"\$E01\" | grep -E 'sh\$'; fcat $F /etc/group \"\$E01\" | grep '^sudo:'"
step FS04_authlog     "fcat $F /var/log/auth.log \"\$E01\" | grep -E 'Accepted|Failed|Invalid user|COMMAND=|useradd|usermod'"
step FS04_journal     "rm -rf \"\$DATA/journal\"; tsk_recover -a -d \$(ifind -n /var/log/journal $F \"\$E01\") $F \"\$E01\" \"\$DATA/journal\" >/dev/null && journalctl -D \"\$DATA/journal\" -b -0 -o short-iso-precise -t sshd -t sudo -t systemd-logind"
step FS04_wtmp        "fcat $F /var/log/wtmp \"\$E01\" > \"\$DATA/wtmp\" && last -F -f \"\$DATA/wtmp\""
step FS05_preload     "fcat $F /etc/ld.so.preload \"\$E01\""
step T01_bodyfile     "fls -r -m / $F \"\$E01\""
step T01_mactime      'mactime -d -y -b "$OUT/T01_bodyfile.txt"'
