<task>
  <role>
    You are Claude Code, using Claude Opus 5.5, preparing one bounded Father
    forensic review draft. Execute this task in the primary checkout. ac is the
    analyst who accepts claim predicates, statuses, chronology, and conclusions;
    your assessments are proposals for review.
  </role>

  <context>
    <routing>Treat this file as the single active task and stop at its endpoint.</routing>
    <run>father-u22-20260913-01 (Ubuntu 22.04)</run>
    <stage>Stage 4A: draft findings and four-table preview</stage>
    <goal>
      Produce a source-located proposal that shows which of Father's four result
      tables can be populated from the current investigation, which entries remain
      open, and precisely what evidence or analyst decisions are missing.
    </goal>
    <required_inputs>
      Read AGENTS.md, ai/CONTEXT.md, ai/RULES.md, ai/forensic/CONTEXT.md,
      ai/tasks/investigation-refactor.md, ai/tasks/father.md, and the results
      contract in ai/RULES.md. Inspect this run's manifest.json,
      command_log.jsonl, dumps/acquisition.json,
      investigation/prepared/prepare.json, relevant investigation/output/
      transcripts, and investigation/findings/ drafts. Extract relevant notebook
      cell sources and bounded saved outputs with a script.
    </required_inputs>
    <verified_starting_facts>
      The manifest has seven claims: preload_persistence, implant_timestomp,
      credential_staging, runtime_loading_backdoor, deleted_staging_artifact,
      recon_staged, shell_history_cleanup. Disk, timeline, and RAM give 21
      claim/source assessment cells.

      The existing findings/findings.json has two unaccepted draft partial disk
      entries with stale Section 1 locators. findings.py is absent; Section 6 is
      a placeholder.

      The canonical prepared/raw/timeline.jsonl is 391,992,089 bytes with 310,364
      events, including 302,947 filestat events (97.6%). The Plaso store is partial
      because of two GZIP extraction and three syslog year-inference warnings.
      The Section 5 pivot and juxtaposition CSVs and transcripts already exist.
      Section 3.8 currently sets DEBUG=True and skips its body. Sections 6-7 are
      placeholders.

      ac provisionally accepts a verified content-hash match as support for the
      copied-content component of credential staging, and the root/GID 1337 shell
      sharing the sshd connection together with the open socket as support for
      the runtime backdoor. Check the remaining words of each claim against the
      actual observations. Leave other genuine predicate choices open for review.
    </verified_starting_facts>
  </context>

  <method>
    <step index="1">
      Recheck the starting facts against the real run. Bind each claim to its
      manifest definition and command-log basis. Examine relevant notebook
      observations and preserved outputs. Verify every locator against an
      existing file or exact source record; treat older draft locators as leads.
      Use targeted read-only commands against existing products where a decisive
      point needs checking. Use the existing full Plaso export and bounded views
      of it; keep the 392 MB JSONL and other prepared products in place.
    </step>
    <step index="2">
      Propose, for each claim, the observations that would justify supported or
      partial and any source that is genuinely not_applicable. Build one compact
      seven-row, three-source grid. Give each cell an explicit proposed RULES.md
      status or label it as an unresolved analyst decision. Add sparse evidence
      notes with claim, source, locator, observation, origin, and limitation where
      a positive observation or bounded negative needs explanation.
    </step>
    <step index="3">
      Preview the four tables defined in ai/RULES.md: reconstructed chronology;
      the claim coverage grid; multi-source contribution; and explored footprint
      inventory. Ground chronology rows in forensic timestamps with their meaning
      and uncertainty. Classify independence by underlying record origin:
      TSK bodyfile, mactime, and Plaso filestat may render the same filesystem
      metadata. Deduplicate process identities, shared sockets, aliases, and
      recovered copies. Separate recovered content, metadata or name traces,
      and evidence of unlinking.
    </step>
    <step index="4">
      Calculate permitted source counts and support-rate numerators and
      denominators from explicit proposed statuses. Use supported + partial +
      unsupported as the investigated denominator; report not_applicable,
      not_examined, tool_failure, and unresolved decisions separately. Mark
      values pending where a verdict or examination is still open. Identify the
      smallest concrete checks and analyst choices needed to finish the tables.
    </step>
  </method>

  <assessment_rules>
    Use unsupported for a specified relevant examination that did not establish
    the claim. Use not_examined for unfinished relevant analysis and tool_failure
    for a blocked analysis. A missing evidence note leaves the grid cell explicit;
    it never supplies a default status. Treat skipped cells, absent entries, and
    tool warnings within their measured scope. Keep run records as execution
    reference, distinct from forensic support. Count corroboration only when
    independently sufficient observations arise from different origins; keep
    overlapping source totals separate. Present disputed predicates with their
    competing evidence and numerical effect.
  </assessment_rules>

  <write_scope>
    Write one concise review document at
    shared/experiments/father-u22-20260913-01/investigation/output/stage4a-results-proposal.md.
    Replace only the Last handoff block, in at most 12 lines, in
    ai/tasks/investigation-refactor.md. Preserve the notebook, helpers, existing
    findings, results, prepared products, evidence, manifests, logs, and other
    dirty work. Leave the changes uncommitted. Reserve findings.py, results/,
    Section 6, notebook cleanup, and deeper code review for later selected tasks.
    Keep the draft flat and small, using the existing result contract and products
    in place of new schemas, scoring code, tests, or exports.
  </write_scope>

  <thinking>
    Before the final response, use private adaptive reasoning to reconcile each
    proposed status with its predicate, locator, source origin, examination state,
    and effect on the counts. Check the four tables against the same 21-cell grid.
    Keep internal reasoning private; provide concise evidence-backed explanations
    and open decisions in the review document and final response.
  </thinking>

  <output_format>
    <review_document>
      Include proposed predicates, the 21-cell grid, sparse evidence notes,
      the four table previews, source rates with numerators and denominators,
      and a short list of unresolved examinations or analyst judgments. Label
      every table and count draft pending ac's review.
    </review_document>
    <final_response>
      Link the review document. Show the compact status grid and computed counts,
      then the decisive evidence limits and open decisions. Report the checks
      actually run and any Claude Code model switch.
    </final_response>
  </output_format>

  <definition_of_done>
    The review document exists; its seven claim IDs match the manifest; all 21
    source cells have a proposed status or an explicit unresolved decision; cited
    locators resolve to preserved records; rates follow the RULES.md denominator;
    the chronology preserves timestamp semantics; footprint counts deduplicate
    identities; all four tables expose pending values honestly; the scoped diff
    passes git diff --check; and Last handoff records actual checks and limits.
  </definition_of_done>

  <endpoint>
    Stop after delivering the draft for supervisor and ac review. The draft
    becomes an accepted finding or result only through a later human decision.
  </endpoint>
</task>
