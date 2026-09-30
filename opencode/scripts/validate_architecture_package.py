"""Read-only structural validator for Architecture Packages (v1)."""

import argparse
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_specification_package import validate as validate_specification  # noqa: E402


SECTIONS = (
    "Architecture Summary",
    "Usage and Interface Sketch",
    "Structural Decisions",
    "Implementation Decisions",
    "Testing Strategy",
    "Tickets and Dependencies",
    "Verification Matrix",
    "Architecture Risks",
    "Architecture Unknowns",
)
TICKET_FIELDS = ("Dependencies", "Allowed", "Forbidden", "Criteria", "Approach")
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
        errors.append("requires exactly one pair of specification package markers")
        return "", text, ""
    begin = text.index(BEGIN_SPEC)
    end = text.index(END_SPEC)
    if begin >= end:
        errors.append("specification package markers are out of order")
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
    outer = text[:begin] + text[end + len(END_SPEC):]
    spec_errors = validate_specification(embedded)
    errors.extend(f"embedded specification: {error}" for error in spec_errors)
    return embedded, outer, raw_embedded


def _validate_tickets(body, criteria, errors):
    headings = list(re.finditer(r"^### (T\d+)\s+[—-]\s+(.+)$", body, re.MULTILINE))
    if not headings:
        errors.append("Tickets and Dependencies requires at least one T ticket")
        return
    tickets, graph, covered = _parse_tickets(body, headings, criteria, errors)
    _validate_dependency_graph(tickets, graph, errors)
    for criterion in sorted(criteria - covered):
        errors.append(f"unassigned criterion: {criterion}")


def _parse_tickets(body, headings, criteria, errors):
    tickets = {}
    graph = {}
    covered = set()
    for heading, ticket_body in _parts(body, headings):
        ticket_id = heading.group(1)
        if ticket_id in tickets:
            errors.append(f"duplicate ticket: {ticket_id}")
        fields = _fields(ticket_body, TICKET_FIELDS, ticket_id, errors)
        tickets[ticket_id] = fields
        dependencies = fields.get("Dependencies", "None")
        graph[ticket_id] = [] if dependencies == "None" else [item.strip() for item in dependencies.split(",")]
        if fields.get("Allowed", "").lower() == "none":
            errors.append(f"{ticket_id}: Allowed requires concrete scope")
        if fields.get("Approach", "").lower() == "none":
            errors.append(f"{ticket_id}: Approach requires implementation detail")
        for criterion in fields.get("Criteria", "").split(","):
            criterion = criterion.strip()
            if criterion:
                covered.add(criterion)
                if criterion not in criteria:
                    errors.append(f"{ticket_id}: unknown criterion {criterion}")
    return tickets, graph, covered


def _validate_dependency_graph(tickets, graph, errors):
    for ticket_id, dependencies in graph.items():
        for dependency in dependencies:
            if dependency not in tickets:
                errors.append(f"{ticket_id}: unknown dependency {dependency}")

    active = set()
    visited = set()

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
        return
    check_body = local.group(1)
    checks = list(re.finditer(r"^#### (L\d+)\s+[—-]\s+(.+)$", check_body, re.MULTILINE))
    if not checks:
        errors.append("Verification Matrix Local requires at least one L check")
        return
    seen = set()
    for check, body_part in _parts(check_body, checks):
        check_id = check.group(1)
        if check_id in seen:
            errors.append(f"duplicate check: {check_id}")
        seen.add(check_id)
        _fields(body_part, CHECK_FIELDS, check_id, errors)


def validate(text, expected_specification=None):
    """Return every structural finding without changing the supplied text."""
    errors = []
    embedded, outer, raw_embedded = _extract_specification(text, errors)
    sizes = re.findall(r"^specification-bytes:\s*(\S.*)$", outer, re.MULTILINE)
    digests = re.findall(r"^specification-sha256:\s*(\S.*)$", outer, re.MULTILINE)
    if len(sizes) != 1 or not sizes[0].isdigit():
        errors.append("requires exactly one numeric specification-bytes field")
    if len(digests) != 1 or not re.fullmatch(r"[0-9a-f]{64}", digests[0]):
        errors.append("requires exactly one lowercase SHA-256 specification-sha256 field")
    if len(sizes) == 1 and sizes[0].isdigit() and len(digests) == 1:
        size = int(sizes[0])
        wrappers = ("", "\n", "\r\n")
        candidates = {
            raw_embedded[len(prefix):len(raw_embedded) - len(suffix) if suffix else None]
            for prefix in wrappers
            for suffix in wrappers
            if raw_embedded.startswith(prefix) and raw_embedded.endswith(suffix)
        }
        if not any(
            len(candidate.encode("utf8")) == size
            and hashlib.sha256(candidate.encode("utf8")).hexdigest() == digests[0]
            for candidate in candidates
        ):
            errors.append("embedded specification does not match its byte count and SHA-256")
    if expected_specification is not None:
        wrappers = ("", "\n", "\r\n")
        valid_embeddings = {
            prefix + expected_specification + suffix
            for prefix in wrappers
            for suffix in wrappers
        }
        if raw_embedded not in valid_embeddings:
            errors.append("embedded specification differs from the supplied Specification Package")
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
    for name in SECTIONS:
        if not found.get(name):
            errors.append(f"missing or empty section: {name}")
    for name in found.keys() - set(SECTIONS):
        errors.append(f"unexpected section: {name}")

    criteria = set(re.findall(r"^- (AC\d+):", embedded, re.MULTILINE))
    _validate_tickets(found.get("Tickets and Dependencies", ""), criteria, errors)
    _validate_matrix(found.get("Verification Matrix", ""), errors)
    unknowns = found.get("Architecture Unknowns", "")
    if unknowns.lower() != "none" and re.search(r"\bblocking\b", unknowns, re.IGNORECASE):
        errors.append("Architecture Unknowns: blocking decisions must be resolved")
    return errors


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
    print("VALID: Architecture Package v1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
