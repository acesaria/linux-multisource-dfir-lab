"""Father claim elements for the strict predicate rule (ac, 2026-10-01).

A source supports a claim only when every element of the claim's statement is observed in that
source; some elements give partial and none unsupported (``fx.propose``). The same elements are
evaluated for disk, timeline and RAM. TERMS are the values the claim statements name. They are
compared with the evidence only in each block's claim check, after the block has answered its
own question from the evidence. Scenario-level, not run-level: the same for every Father run.
"""

TERMS = {
    "preload": "/etc/ld.so.preload",
    "object": "/lib/selinux.so.3",
    "libc": "/lib/x86_64-linux-gnu/libc.so.6",
    "shadow": "/etc/shadow",
    "harvest": "/tmp/__malicious_harvest",
    "harvest_mode": 0o600,
    "staged": "/tmp/rk.so",
    "recon": "/tmp/__malicious_recon",
}

ELEMENTS = {
    "preload_persistence": ("preload_file", "names_object"),
    "implant_timestomp": ("mtime_from_libc", "atime_from_libc", "mtime_before_creation"),
    "credential_staging": ("harvest_file", "mode_0600", "content_of_shadow"),
    "runtime_loading_backdoor": ("activated", "validated", "connection_at_capture"),
    "deleted_staging_artifact": ("staged_file", "unlinked", "after_use_before_capture"),
    "recon_staged": ("recon_file", "recon_content"),
    "shell_history_cleanup": ("history_cleared", "history_file_removed", "histfile_unset"),
}

# Generic indicators of MITRE ATT&CK T1070.003 (Clear Command History), not scenario commands.
# POSIX ERE syntax: the same pattern drives grep -E over the image and Volatility's Python re.
HISTORY_INDICATORS = {
    "history_cleared": r"history -c|history -w /dev/null|set \+o history",
    "history_file_removed": r"(rm|shred|truncate) [^;&|]{0,80}(HISTFILE|bash_history)",
    "histfile_unset": r"unset HISTFILE|HISTFILE=/dev/null|HISTSIZE=0",
}

# Reconnaissance output markers: id, uname -a, os-release and passwd lines.
RECON_MARKERS = (rb"uid=\d+\(", rb"\nLinux \S+ \d", rb"PRETTY_NAME=", rb"\nroot:x:0:0:")
