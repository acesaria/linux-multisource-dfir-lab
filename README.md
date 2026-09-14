# Linux Multi-Source DFIR Lab

[Canonical repository](https://github.com/acesaria/linux-multisource-dfir-lab)

Linux Multi-Source DFIR Lab supports a Master's thesis on reproducible Linux
post-mortem DFIR experiments. It runs controlled compromise scenarios in
isolated VMs, acquires disk and memory evidence, and supports manual
investigation with Sleuth Kit, Plaso, and Volatility 3 across filesystem,
timeline, and memory sources.

The project is research infrastructure, not a production SIEM, EDR, malware
sandbox, live-response platform, automatic detector, or automatic
reconstruction system.

## Project goal and completion

Explain what controlled Linux attacks can be reconstructed from acquired disk,
timeline views and RAM, and what combining them establishes. Automation supports
scenario execution and acquisition; forensic interpretation is manual.

The completion target is reviewed, reproducible results for all planned thesis
scenarios (Father, ptrace, Diamorphine and BadBPF), using the four locked tables,
with source locators, claim support, recovery outcomes and limitations. The thesis
is brought to completion from that complete results package. The user estimates
approximately one more month of work from 10 September 2026; this supersedes the
previous two-case September milestone as the overall completion target.

Methodology is definitively approved in
[RESULTS_PREVIEW.md](investigations/father/RESULTS_PREVIEW.md). That file is
read-only. Its four tables are the target; example values are fictional.
Metric-selection debate is closed. Deletion recovery is an active task, including
journal reconstruction and targeted carving of unallocated space, integrated
through standard commands and small notebook cells.

## Current repository surface

The CLI exposes `init`, `setup`, `build`, `run`, and `destroy`. `build` publishes
a scenario's prebuilt artifact and is required before running that scenario.
`run` dispatches directly to one of five scenario keys:

- `interactive_shell`;
- `kernel_ebpf_badbpf`;
- `kernel_diamorphine`;
- `ptrace_fa`;
- `userland_father_ldpreload`.

A full run restores the prepared baseline, executes and validates the selected
scenario, acquires memory while the VM is on, shuts the VM down, acquires disk,
and then stops. Investigation-time tools produce only the outputs the analyst
needs; cross-source interpretation and conclusions are human work.

Fresh runs include explicit scenario claims and are recorded as `vanilla`.
There is no runtime selector for a hardened security profile. Distro definitions exist for
Ubuntu 22.04, Ubuntu 24.04, and Debian 13, but Ubuntu 22.04 is the current
deep-analysis platform. Broader replication and optional scenarios must not
delay the minimum thesis deliverables.

## Evidence and run records

Each run is rooted under `shared/experiments/<run_id>/`. An acquired run keeps:

```text
manifest.json                         platform, revision, snapshot, inputs, claims, timestamps
command_log.jsonl                     append-only commands and validations with stable IDs
terminal_transcript.txt               human-readable scenario terminal record
dumps/acquisition.json                compact RAM and logical-disk acquisition metadata
dumps/acquisition.log                 acquisition commands and tool diagnostics
```

Each runner declares `get_scenario_claims()`. Claims contain only `id`,
`statement`, `basis`, `basis_type` and `validation_limit`. Their basis references
stable command-log IDs (`command_log.jsonl#record_id`), copied run inputs or
manifest facts (`manifest.json#scenario_facts.<name>`). They are published only
after successful scenario validation; a failed scenario retains `claims: []`.
They describe expected effects, not independently verified final-state truth.
An acquisition failure retains these claims and any completed acquisition
metadata. `scenario_facts` holds runtime observations such as PIDs and endpoints.

The five run timestamps use UTC with six fractional digits. RAM start/end times
bracket `virsh dump --memory-only`, excluding version probing and file hashing;
the acquisition record carries the same values. Durations use a monotonic clock.
Disk timing covers conversion through EWF verification. Run completion is
recorded after cleanup.

In `dumps/acquisition.json`, memory SHA-256 and size describe the captured file.
Disk SHA-256 and size describe the **logical disk across all EWF segments**:
`path` names the first segment, `segments` lists the set, and `hash_scope` is
`logical_disk`. The digest is recomputed by `ewfverify -d sha256`; it is not the
hash of the `.E01` container file. Individual segments are not separately hashed.
Python uses SHA-256 exclusively; libewf's internal MD5 calculation is the sole
exception, and no MD5 field is serialized. Tool versions are keyed by tool name.

Both JSON manifests use two-space indentation and contain no terminal streams.
Acquisition diagnostics go to `dumps/acquisition.log`; loose `hashes.txt` and
per-tool JSON status files are no longer generated. Unattempted acquisitions are
`null`; incomplete records retain their timing, actual subprocess exit status,
and a short error. A zero exit status with an error is a failed output-validation
step, not a successful acquisition. The acquisition sidecar is the authority for
acquisition provenance. A successful `--no-acquire` run keeps the root records but no acquisition sidecar; it validates only the scenario and is
not a complete forensic experiment.

Accepted evidence and raw exports are immutable. Other generated caches may be
recreated, but accepted run material must not be overwritten. Tool failures,
zero-result tools, and source-scoped negative observations remain distinct.

## Repository layout

```text
cli.py                    command entry point
infra/                    libvirt/QEMU, Ansible, images, distro definitions
orchestrator/core/        lifecycle, VM state, configuration, run paths
orchestrator/forensics/   acquisition and investigation/verification runners
scenarios/                explicit scenario runners and command logging
docs/investigations/      scenario/run notebooks, accepted reports, comparative material
shared/                   generated run evidence, exports, and local analysis
```

Operational identifiers such as the `forensic-lab` CLI name, schema names, guest
paths, and evidence artifacts are retained when they are part of the working
system or a recorded run.

## Basic use

Create the local configuration and virtual environment first:

```bash
cp config.yaml.example config.yaml
./setup-venv.sh
```

Then use the repository interpreter:

```bash
.venv/bin/python cli.py init
.venv/bin/python cli.py setup --distro ubuntu-22.04
.venv/bin/python cli.py build --distro ubuntu-22.04 \
  --scenario userland_father_ldpreload
.venv/bin/python cli.py run --distro ubuntu-22.04 \
  --scenario userland_father_ldpreload
```

### Pinned image and prebuilt inputs

Ubuntu eventually prunes dated cloud-image release directories, so the pinned
URL may return 404. Before downloading, `infra.image_store.ensure_image` checks
`<state_dir>/images/<filename>` and verifies it against the profile checksum; an
exact image obtained elsewhere can therefore be placed at
`/var/lib/forensic-lab/images/ubuntu-22.04-20260515-server-cloudimg-amd64.img`.
Verification, not the transfer source, controls acceptance. Prebuilt inputs are
not committed: run `build` before `run` for every scenario that consumes one.

```bash
sudo install -o root -g root -m 0444 /path/to/ubuntu-22.04-20260515-server-cloudimg-amd64.img /var/lib/forensic-lab/images/ubuntu-22.04-20260515-server-cloudimg-amd64.img
```

### Complete experiment command sheet

```bash
cp config.yaml.example config.yaml
./setup-venv.sh
.venv/bin/python cli.py init
.venv/bin/python cli.py setup --distro ubuntu-22.04
.venv/bin/python cli.py build --distro ubuntu-22.04 --scenario userland_father_ldpreload
.venv/bin/python cli.py build --distro ubuntu-22.04 --scenario ptrace_fa
.venv/bin/python cli.py build --distro ubuntu-22.04 --scenario kernel_diamorphine
.venv/bin/python cli.py build --distro ubuntu-22.04 --scenario kernel_ebpf_badbpf
.venv/bin/python cli.py run --distro ubuntu-22.04 --scenario userland_father_ldpreload
.venv/bin/python cli.py run --distro ubuntu-22.04 --scenario ptrace_fa
.venv/bin/python cli.py run --distro ubuntu-22.04 --scenario kernel_diamorphine
.venv/bin/python cli.py run --distro ubuntu-22.04 --scenario kernel_ebpf_badbpf
# Evidence: shared/experiments/<run_id>/
```

### Host prerequisites

The host runs Linux with KVM available. On Debian/Ubuntu:

```bash
sudo apt install qemu-kvm libvirt-daemon-system virtinst cloud-image-utils \
                 libewf-dev sleuthkit plaso-tools ansible python3-venv
pipx install volatility3          # installs the "vol" command, not "vol3"
ln -s "$(command -v vol)" "$(dirname "$(command -v vol)")/vol3"
sudo usermod -aG libvirt,kvm "$USER" && newgrp libvirt
```

The alias above exists because every command in this repository — `config.yaml`'s
`vol_bin`, the orchestrator's setup-time probe, and every investigation
notebook's manual commands — was written against the name `vol3`, which is not
what upstream Volatility 3 actually installs (its `pyproject.toml` defines only
`vol` and `volshell`). Renaming every reference instead of aliasing the binary
would touch already-written investigation notebooks for no benefit; the alias
keeps every existing command reproducible as written.

Installing `libewf-dev` alongside `sleuthkit` does **not** guarantee the
distribution's prebuilt `sleuthkit` package was itself compiled against
libewf; that is decided at the distribution's own build time, not by what is
installed afterwards. Verify explicitly before relying on it:

```bash
mmls -i list        # must list "ewf" among the supported image types
```

If it does not, `cli.py setup` will fail loudly on its first toolchain probe
(`mmls` against an acquired `.E01` image) rather than mid-scenario. The fix is
to build Sleuth Kit from source against `libewf-dev`, or install a build known
to include EWF support (some distributions ship one via a PPA or backports).

The lab VM is reached over SSH with a dedicated key, whose paths are declared in
`config.yaml`:

```bash
ssh-keygen -t ed25519 -f ~/.ssh/forensics-lab -N ""
```

`cli.py` verifies, before each command, only the binaries that command will
actually use, and stops with an explicit list if any is missing. Passwordless
sudo inside the disposable guest is a documented deployment precondition, not an
emulation of initial compromise.

Volatility symbol tables (ISF) are **generated**, not distributed: `cli.py setup`
builds the table for the guest kernel and writes it under `shared/isf/`. A fresh
clone therefore starts without them, by design.

## Documentation

- [Investigation method](docs/INVESTIGATION_METHOD.md) defines the current narrative-first approach.
- [Father investigation](investigations/father/README.md) is the active unified notebook.
- `docs/investigations/` preserves historical case records; its old metric
  definitions do not govern new investigations.
- [Agent entry](AGENTS.md) and [ICM routing](ai/CONTEXT.md) are tracked for local and online review.
- `scenarios/<id>/README.md` documents each controlled treatment's behaviour.
- Named investigation documents apply only to their cited immutable runs.

## Third-party components

Compromise techniques are not reimplemented here. Each scenario vendors a
pristine upstream archive pinned to a specific commit and verified by hash; the
pin, the archive hash and the licence are recorded in the scenario's
`*.lock.yml`, and the prepared artefact is built on a separate builder VM that
never becomes the system under examination.

| Scenario | Upstream project | Licence |
|---|---|---|
| `userland_father_ldpreload` | [Father](https://github.com/mav8557/Father) | Unlicense |
| `kernel_diamorphine` | [Diamorphine](https://github.com/m0nad/Diamorphine) | BSD-3-Clause |
| `kernel_ebpf_badbpf` | [bad-bpf](https://github.com/pathtofile/bad-bpf) | BSD-3-Clause / GPL-2.0 |

The forensic toolchain (The Sleuth Kit, Plaso, Volatility 3, libewf, libvirt,
QEMU) is used unmodified and is not redistributed by this repository.

Previous automatic detection, matching, scoring, and reconstruction work is
historical. Its final checkpoint is preserved by the immutable
`automatic-reconstruction-v3-final` tag and must not be treated as the current
architecture.
