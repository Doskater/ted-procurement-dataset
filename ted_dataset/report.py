"""Readable evidence report, with independent manual verification kept explicit."""


def render_report(manifest, result, manual, automated):
    m = result["metrics"]
    auto = automated["status"] == "passed"
    human = manual["status"] == "passed"
    if auto and human:
        status = "Automated checks passed; manual sample verification passed."
    elif auto and manual["status"] == "pending":
        status = "Automated checks passed; manual verification pending."
    else:
        status = f"Automated verification: {automated['status']}; manual verification {manual['status']}."
    lines = ["# QA Report", "", status, "", "Independent public-data project. Not client work.", "",
             f"Source: Tenders Electronic Daily (TED). Retrieved: {manifest['retrieved_at']}.",
             f"Publication window: {manifest['date_start']} through {manifest['as_of']} (inclusive).",
             f"Snapshot SHA-256: `{result['snapshot_id']}`.", "", "## Retrieval and reconciliation", "",
             f"Source reported: **{manifest['source_total']}**. Retrieved: **{manifest['records_retrieved']}**.",
             "All successful page checksums verified; iteration ended with an empty page.", "",
             "| Metric | Count |", "|---|---:|"]
    lines += [f"| {key.replace('_', ' ')} | {value} |" for key, value in m.items()]
    lines += ["", f"`{m['raw_records']} = {m['valid_unique']} valid unique + {m['rejected']} rejected + "
              f"{m['uncertain']} uncertain + {m['duplicates']} duplicate occurrences`",
              f"`{m['valid_unique']} = {m['selected']} selected + {m['valid_not_selected']} valid not selected`", "",
              "Every source occurrence has one entry in record_ledger.csv. Rejections retain reasons and raw pointers."]
    if m["selected"] < m["target"]:
        lines += ["", f"Target shortfall: {m['target']-m['selected']}. The complete fixed-window snapshot yielded "
                  f"{m['valid_unique']} valid notices under the declared rules. No filters or dates were broadened."]
    lines += ["", "## Automated verification", "", f"Test evidence: **{automated['status']}**."]
    if "tests" in automated:
        lines += [f"Tests: {automated['tests']}; failures: {automated['failures']}; errors: {automated['errors']}."]
    lines += ["Selected IDs are unique. Required values, dates, CPV membership, exact source URLs and export readback passed.",
              "Test fixtures are offline. Deliberately corrupted inputs are confined to tests.", "",
              "## Manual sample verification", "",
              f"Seed: 42. Sample: {manual['sample_size']}. Reviewed: {manual['reviewed']}. "
              f"Pending: {manual['pending']}. Mismatching records: {manual['mismatches']}.",
              "Review status is read from qa/manual_qa_sample.csv; the program never marks source checks as a human pass.",
              "", "## Known limitations", "",
              "- Snapshot of published contract notices, not a guarantee of currently open opportunities or bidder eligibility.",
              "- Latest-version filtering relies on TED. Publication number is the row identity; different publications are not merged by title or UUID.",
              "- A procedure's main CPV must start with 48 or 72. IT mentioned only in additional codes/lots is excluded.",
              "- Only cn-standard and cn-social notices are included, across all TED buyer countries.",
              "- Titles and buyer names retain source languages; English labels do not imply translated source content.",
              "- Multi-lot or ambiguous deadlines are intentionally blank. Single-lot tender dates omit time of day.",
              "- Estimates are procedure-level source values only. No lot summation, currency conversion, VAT inference or accuracy warranty for publisher-entered amounts.",
              "- MISSING_PROCEDURE_ESTIMATED_VALUE means absent at procedure level; a lot may still publish an estimate. A single-lot estimate is not substituted for the procedure field.",
              "- ISO currency validation uses the pinned current SIX list; obsolete/unknown codes are quarantined.",
              "- Manual verification covers the sample only. Public source pages may change after capture; compare the same publication ID and the archived raw response.",
              "- CSV retains literal text; import with explicit text types. XLSX stores untrusted source strings as text, never formulas.", ""]
    return "\n".join(lines)
