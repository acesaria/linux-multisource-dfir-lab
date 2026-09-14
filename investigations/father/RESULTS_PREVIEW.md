# Father — example result tables (Definitive Methodology)

> **ILLUSTRATIVE ONLY — NOT FORENSIC RESULTS.** Every time, count, PID, address,
> identifier, and observation below is fictional. No forensic tools were run to
> produce these tables. They demonstrate presentation and reasoning only; never
> copy these values into a real run's findings or the thesis as measured results.

**Research question:** What can acquired static Disk, RAM, and Timeline analysis reveal about an LD_PRELOAD compromise, and what does their correlation add beyond any single source?

## Table 1. Reconstructed chronology — fictional example

Times are relative to the first selected filesystem timestamp (T+0). Evidence IDs beginning `DEMO-` are explanatory placeholders.

| Relative time | Observation | Evidence locator / origin | Interpretation and limit |
|---|---|---|---|
| T+0 s | A library's filesystem birth timestamp is recorded. | `DEMO-D1`: library inode | Dates filesystem object creation, not necessarily installation of its present bytes. |
| T+24 s | The preload file has this modification timestamp; its acquired contents name the library. | `DEMO-T1`: Plaso metadata event (`filestat`) | Consistent with configuration around this time; does not expose every earlier version. |
| T+36 s | Service records show SSH stopping and starting. | `DEMO-T2`: Plaso events from system journal | Establishes a service sequence; the cause is not supplied by the service messages alone. |
| T+48 s | A privileged shell has this recorded process start time and a parent relationship to SSH. | `DEMO-M1`: RAM process records (`linux.pslist`) | Provides runtime context. Parentage alone does not establish a backdoor. |
| At RAM capture | The library is mapped in SSH; the shell references an established external socket. | `DEMO-M2`: RAM mappings; `DEMO-M3`: socket object | Jointly consistent with the configured library being involved in the observed remote-shell context. |

## Table 2. Claim Coverage & Source Support

This table evaluates forensic observability against the declarative Ground Truth (GT) manifest. 
**Support Criteria:** Supported (**S**), Partial (**P**), Unsupported (**U**), Not Applicable (**N/A**).

| GT Claim ID | Static Disk | Timeline | RAM | Combined Conclusion | Note (Missing elements) |
|---|---|---|---|---|---|
| `ldpreload_modified` | **S** (Inode/content) | **S** (Plaso `filestat`) | **U** | **Supported** | Configuration persistence proven. RAM cache unexamined. |
| `malicious_so_loaded` | **N/A** | **N/A** | **S** (VMA match) | **Supported** | Static sources cannot independently prove memory mapping. |
| `staging_file_deleted` | **P** (Name/inode only) | **S** (Deletion event) | **U** | **Partial** | File content is unrecoverable (carving out of scope). |
| `c2_connection` | **N/A** | **U** (No logs) | **S** (Socket state) | **Supported** | Volatile state recovered; historical network traffic out of scope. |

## Table 3. Multi-Source Contribution (Quantitative Summary)

This table quantifies the epistemic value of combining multiple investigative lenses.
*   **Sufficient:** The source independently establishes the claim.
*   **Corroborated:** $\ge 2$ sources independently establish the claim.
*   **Jointly Sufficient:** No single source is sufficient, but their intersection establishes the claim.

| Run / Distro | Total GT Claims | Disk Sufficient | Timeline Sufficient | RAM Sufficient | Corroborated ($\ge 2$) | Jointly Sufficient | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|
| DEMO-Ubuntu-22 | 4 | 1 | 1 | 2 | 1 | 1 | 0 |
| DEMO-Debian-13 | 4 | 1 | 0 | 2 | 0 | 1 | 1 |

*Note: The values above are illustrative. A claim that is 'Jointly Sufficient' represents the direct value added by cross-source correlation.*

## Table 4. Explored Footprint Inventory

Descriptive counts of the retained footprint. These are observed relevant objects, not global detection rates. Deduplication is applied (e.g., multiple threads referencing one socket count as one object).

| Run / Distro | Infected Processes | Relevant Sockets | Staging Artifacts Validated |
|---|---:|---:|---:|
| DEMO-Ubuntu-22 | 2 (PID 112, 114) | 1 (ESTABLISHED) | 0 |
| DEMO-Debian-13 | 1 (PID 400) | 1 (LISTEN) | 1 |

## What the real version must replace
- Replace every fictional entry with a reviewed observation and a real locator.
- Record image identity, acquisition times, tool versions, extraction scope, and timestamp semantics alongside the tables.
- Keep scenario-command times and laboratory validation in their own section; they cannot silently fill gaps in Table 1.