"""Read-only structural validator for Architecture Packages (v2)."""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_specification_package import validate as validate_specification  # noqa: E402


SECTIONS = (
    "Decision Summary",
    "Repository Findings",
    "Architecture Candidates",
    "Comparison and Recommendation",
    "Proposed Design",
    "Interfaces and Behavior",
    "Implementation Plan",
    "Testing Strategy",
    "Verification Matrix",
    "Requirements Traceability",
    "Risks and Open Questions",
    "Frozen Specification",
)
TICKET_FIELDS = ("Dependencies", "Allowed", "Forbidden", "Criteria", "Approach", "Outputs")
CHECK_FIELDS = ("Command", "Working directory", "Prerequisites", "Expected")
BEGIN_SPEC = "<!-- BEGIN SPECIFICATION PACKAGE -->"
END_SPEC = "<!-- END SPECIFICATION PACKAGE -->"


def _parts(text, headings):
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        yield heading, text[heading.end():end].strip()


def _fields(body, names, context, errors):
    result = {}
    for name in names:
        values = re.findall(r"^- " + re.escape(name) + r":\s*(.*)$", body, re.MULTILINE)
        if len(values) != 1 or not values[0].strip():
            errors.append(f"{context}: requires exactly one nonempty '{name}' field")
        else:
            result[name] = values[0].strip()
    return result


def _extract_specification(text, errors):
    if text.count(BEGIN_SPEC) != 1 or text.count(END_SPEC) != 1:
        errors.append("requires exactly one pair of specification package markers in Frozen Specification")
        return "", text, ""
    begin = text.index(BEGIN_SPEC)
    end = text.index(END_SPEC)
    frozen_heading = text.rfind("## Frozen Specification", 0, begin)
    if begin >= end or frozen_heading < 0 or text[end + len(END_SPEC):].strip():
        errors.append("specification markers must be ordered in the final Frozen Specification section")
        return "", text, ""
    raw_embedded = text[begin + len(BEGIN_SPEC):end]
    embedded = raw_embedded
    if embedded.startswith("\r\n"):
        embedded = embedded[2:]
    elif embedded.startswith("\n"):
        embedded = embedded[1:]
    if embedded.endswith("\r\n"):
        embedded = embedded[:-2]
    elif embedded.endswith("\n"):
        embedded = embedded[:-1]
    outer = text[:frozen_heading]
    errors.extend(f"embedded specification: {error}" for error in validate_specification(embedded))
    return embedded, outer, raw_embedded


def _unique_ids(pattern, body, label, errors):
    identifiers = re.findall(pattern, body, re.MULTILINE)
    duplicates = sorted({item for item in identifiers if identifiers.count(item) > 1})
    if duplicates:
        errors.append(f"duplicate {label} identifier(s): {', '.join(duplicates)}")
    return set(identifiers)


def _validate_candidates(body, errors):
    candidates = re.findall(r"^### (C\d+)\s+[—-]\s+(.+)$", body, re.MULTILINE)
    ids = [identifier for identifier, _ in candidates]
    if len(ids) < 2:
        errors.append("Architecture Candidates requires at least two structurally distinct C candidates")
    if len(ids) != len(set(ids)):
        errors.append("Architecture Candidates contains duplicate candidate identifiers")
    return set(ids)


def _validate_tickets(body, criteria, errors):
    headings = list(re.finditer(r"^### (T\d+)\s+[—-]\s+(.+)$", body, re.MULTILINE))
    if not headings:
        errors.append("Implementation Plan requires at least one T ticket")
        return set()
    tickets, graph, covered = {}, {}, set()
    for heading, ticket_body in _parts(body, headings):
        ticket_id, fields, dependencies, ticket_criteria = _parse_ticket(
            heading, ticket_body, criteria, errors
        )
        if ticket_id in tickets:
            errors.append(f"duplicate ticket: {ticket_id}")
        tickets[ticket_id] = fields
        graph[ticket_id] = dependencies
        covered.update(ticket_criteria)
    _validate_dependency_graph(graph, errors)
    for criterion in sorted(criteria - covered):
        errors.append(f"unassigned criterion: {criterion}")
    return {ticket_id: _list_cell(fields.get("Criteria", "")) for ticket_id, fields in tickets.items()}


def _parse_ticket(heading, body, criteria, errors):
    ticket_id = heading.group(1)
    fields = _fields(body, TICKET_FIELDS, ticket_id, errors)
    if fields.get("Allowed", "").lower() == "none":
        errors.append(f"{ticket_id}: Allowed requires concrete scope")
    if fields.get("Approach", "").lower() == "none":
        errors.append(f"{ticket_id}: Approach requires implementation detail")
    ticket_criteria = {value.strip() for value in fields.get("Criteria", "").split(",") if value.strip()}
    for criterion in sorted(ticket_criteria - criteria):
        errors.append(f"{ticket_id}: unknown criterion {criterion}")
    dependencies = fields.get("Dependencies", "None")
    dependency_ids = [] if dependencies == "None" else [item.strip() for item in dependencies.split(",")]
    return ticket_id, fields, dependency_ids, ticket_criteria


def _validate_dependency_graph(graph, errors):
    for ticket_id, dependencies in graph.items():
        for dependency in dependencies:
            if dependency not in graph:
                errors.append(f"{ticket_id}: unknown dependency {dependency}")
    active, visited = set(), set()

    def visit(ticket_id):
        if ticket_id in active:
            errors.append(f"cyclic ticket dependencies involving {ticket_id}")
            return
        if ticket_id in visited:
            return
        active.add(ticket_id)
        for dependency in graph[ticket_id]:
            if dependency in graph:
                visit(dependency)
        active.remove(ticket_id)
        visited.add(ticket_id)

    for ticket_id in graph:
        visit(ticket_id)


def _validate_matrix(body, errors):
    local = re.search(r"^### Local\s*$\n(.*)$", body, re.MULTILINE | re.DOTALL)
    if not local:
        errors.append("Verification Matrix requires a nonempty Local section")
        return set()
    checks = list(re.finditer(r"^#### (L\d+)\s+[—-]\s+(.+)$", local.group(1), re.MULTILINE))
    if not checks:
        errors.append("Verification Matrix Local requires at least one L check")
        return set()
    seen = set()
    for check, check_body in _parts(local.group(1), checks):
        check_id = check.group(1)
        if check_id in seen:
            errors.append(f"duplicate check: {check_id}")
        seen.add(check_id)
        fields = _fields(check_body, CHECK_FIELDS, check_id, errors)
        if fields.get("Command", "").lower() in ("none", "n/a"):
            errors.append(f"{check_id}: Command must be runnable")
    return seen


def _list_cell(cell):
    return {value.strip() for value in cell.split(",") if value.strip()}


def _traceability_row(cells, criteria, available, rows, errors):
    if len(cells) != 4 or cells[0] not in criteria:
        return
    criterion, *columns = cells
    if criterion in rows:
        errors.append(f"Requirements Traceability has duplicate row for {criterion}")
    rows[criterion] = columns
    _validate_traceability_references(criterion, columns, available, errors)


def _validate_traceability_references(criterion, columns, available, errors):
    for label, cell in zip(("decision", "ticket", "verification"), columns):
        identifiers = _list_cell(cell)
        if not identifiers:
            errors.append(f"{criterion}: traceability requires at least one {label} identifier")
        for identifier in identifiers - available[label]:
            errors.append(f"{criterion}: unknown {label} identifier {identifier}")
        if label == "ticket":
            for identifier in identifiers & available[label]:
                if criterion not in available["ticket_criteria"][identifier]:
                    errors.append(f"{criterion}: {identifier} does not declare this criterion")


def _validate_traceability(body, criteria, available, errors):
    rows = {}
    for line in body.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        _traceability_row(cells, criteria, available, rows, errors)
    for criterion in sorted(criteria - rows.keys()):
        errors.append(f"missing traceability row for {criterion}")
    return rows


def validate(text, expected_specification=None):
    """Return every structural finding without changing the supplied text."""
    errors = []
    embedded, outer, raw_embedded = _extract_specification(text, errors)
    if expected_specification is not None:
        wrappers = ("", "\n", "\r\n")
        valid_embeddings = {
            prefix + expected_specification + suffix
            for prefix in wrappers
            for suffix in wrappers
        }
        if raw_embedded not in valid_embeddings:
            errors.append("embedded specification differs from the supplied Specification Package")
    if not outer.startswith("package-version: 2\nstatus: ARCHITECTURE_READY"):
        errors.append("package must begin with package-version: 2 followed by status: ARCHITECTURE_READY")
    versions = re.findall(r"^package-version:\s*(\S+)\s*$", outer, re.MULTILINE)
    if versions != ["2"]:
        errors.append("requires exactly one package-version: 2 (version 1 packages must be regenerated)")
    statuses = re.findall(r"^status:\s*(\S.*)$", outer, re.MULTILINE)
    if statuses != ["ARCHITECTURE_READY"]:
        errors.append("requires exactly one outer ARCHITECTURE_READY status")
    if re.search(r"\b(?:TBD|TODO)\b|\{\{[^{}\n]+\}\}", outer, re.IGNORECASE):
        errors.append("contains a placeholder or unresolved TODO/TBD")

    headings = list(re.finditer(r"^## (.+?)\s*$", outer, re.MULTILINE))
    found = {}
    for heading, body in _parts(outer, headings):
        name = heading.group(1)
        if name in found:
            errors.append(f"duplicate section: {name}")
        found[name] = body
    if tuple(found) != SECTIONS[:-1]:
        errors.append("v2 sections are missing, unexpected, or out of order")
    for name in SECTIONS[:-1]:
        if not found.get(name):
            errors.append(f"missing or empty section: {name}")

    criteria = set(re.findall(r"^- (AC\d+):", embedded, re.MULTILINE))
    _validate_design_and_traceability(found, criteria, errors)
    return errors


def _validate_design_and_traceability(found, criteria, errors):
    candidates = _validate_candidates(found.get("Architecture Candidates", ""), errors)
    comparison = found.get("Comparison and Recommendation", "")
    _validate_comparison(comparison, candidates, errors)
    decisions = _unique_ids(r"^### (D\d+)\s+[—-]\s+.+$", found.get("Proposed Design", ""), "decision", errors)
    if not decisions:
        errors.append("Proposed Design requires at least one D design decision")
    ticket_criteria = _validate_tickets(found.get("Implementation Plan", ""), criteria, errors)
    checks = _validate_matrix(found.get("Verification Matrix", ""), errors)
    available = {
        "decision": decisions,
        "ticket": set(ticket_criteria),
        "ticket_criteria": ticket_criteria,
        "verification": checks,
    }
    _validate_traceability(found.get("Requirements Traceability", ""), criteria, available, errors)
    if re.search(r"\bblocking\b", found.get("Risks and Open Questions", ""), re.IGNORECASE):
        errors.append("Risks and Open Questions cannot contain blocking unknowns")


def _validate_comparison(comparison, candidates, errors):
    header = re.search(r"^\|[^\n]+", comparison, re.MULTILINE)
    if not header or not re.match(r"^\|\s*Criterion\s*\|", header.group(0)):
        errors.append("Comparison and Recommendation requires a criterion comparison table")
    for candidate in candidates:
        if not header or candidate not in header.group(0):
            errors.append(f"Comparison and Recommendation must compare {candidate}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--specification", type=Path)
    args = parser.parse_args()
    expected = args.specification.read_text() if args.specification else None
    errors = validate(sys.stdin.read(), expected)
    if errors:
        for error in errors:
            print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print("VALID: Architecture Package v2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
