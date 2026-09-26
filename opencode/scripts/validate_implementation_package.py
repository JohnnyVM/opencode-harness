"""Read-only, structural validation of a pasted Implementation Package (v2)."""

import re
import sys


SECTIONS = (
    "Problem Statement", "Solution", "User Stories", "Implementation Decisions",
    "Testing Decisions", "Tickets and Dependencies", "Acceptance Criteria",
    "Verification Commands", "Risks", "Explicit Unknowns", "Out of Scope",
)
FIELDS = ("Dependencies", "Allowed", "Forbidden", "Criteria", "Approach")
LOCAL_FIELDS = ("Command", "Working directory", "Prerequisites", "Expected")
STATUS = re.compile(r"^status:\s*(\S.*)$", re.MULTILINE)
HEADING = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
TICKET = re.compile(r"^### (T\d+)\s+[—-]\s+(.+)$", re.MULTILINE)
CRITERION = re.compile(r"^- (AC\d+):\s*(.+)$", re.MULTILINE)
CHECK = re.compile(r"^#### (L\d+)\s+[—-]\s+(.+)$", re.MULTILINE)


def _parts(text, headings):
    """Split a section into same-level headings and their contents."""
    result = []
    for index, match in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        result.append((match, text[match.end():end].strip()))
    return result


def _fields(body, names, context, errors):
    found = {}
    for name in names:
        matches = re.findall(r"^- " + re.escape(name) + r":\s*(.*)$", body, re.MULTILINE)
        if len(matches) != 1 or not matches[0].strip():
            errors.append(f"{context}: requires exactly one nonempty '{name}' field")
        else:
            found[name] = matches[0].strip()
    return found


def validate(text):
    """Return all structural findings without changing the supplied text."""
    errors = []
    statuses = STATUS.findall(text)
    if len(statuses) != 1 or statuses[0] not in (
        "SPEC_APPROVED_BY_AGENT", "SPEC_APPROVED_BY_USER"
    ):
        errors.append("requires exactly one valid status field")
    if re.search(r"\b(?:TBD|TODO)\b|\[[^\]\n]+\]", text, re.IGNORECASE):
        errors.append("contains a placeholder or unresolved TODO/TBD")

    headings = list(HEADING.finditer(text))
    sections = {}
    for match, body in _parts(text, headings):
        name = match.group(1)
        if name in sections:
            errors.append(f"duplicate section: {name}")
        sections[name] = body
    for name in SECTIONS:
        if not sections.get(name):
            errors.append(f"missing or empty section: {name}")

    tickets = {}
    ticket_body = sections.get("Tickets and Dependencies", "")
    matches = list(TICKET.finditer(ticket_body))
    for match, body in _parts(ticket_body, matches):
        ticket_id = match.group(1)
        if ticket_id in tickets:
            errors.append(f"duplicate ticket: {ticket_id}")
        fields = _fields(body, FIELDS, ticket_id, errors)
        tickets[ticket_id] = fields
    if ticket_body and not matches:
        errors.append("Tickets and Dependencies: requires at least one T ticket")

    criteria = {}
    criteria_body = sections.get("Acceptance Criteria", "")
    for match in CRITERION.finditer(criteria_body):
        if match.group(1) in criteria:
            errors.append(f"duplicate criterion: {match.group(1)}")
        criteria[match.group(1)] = match.group(2).strip()
    if criteria_body and not criteria:
        errors.append("Acceptance Criteria: requires at least one AC criterion")

    graph = {}
    covered_criteria = set()
    for ticket_id, fields in tickets.items():
        if fields.get("Allowed", "").lower() == "none":
            errors.append(f"{ticket_id}: Allowed requires concrete scope")
        if fields.get("Approach", "").lower() == "none":
            errors.append(f"{ticket_id}: Approach requires implementation detail")
        dependencies = fields.get("Dependencies", "None")
        deps = [] if dependencies == "None" else [x.strip() for x in dependencies.split(",")]
        graph[ticket_id] = deps
        for dep in deps:
            if dep not in tickets:
                errors.append(f"{ticket_id}: unknown dependency {dep}")
        for criterion in fields.get("Criteria", "").split(","):
            if criterion.strip() and criterion.strip() not in criteria:
                errors.append(f"{ticket_id}: unknown criterion {criterion.strip()}")
            elif criterion.strip():
                covered_criteria.add(criterion.strip())
    for criterion in sorted(criteria.keys() - covered_criteria):
        errors.append(f"unassigned criterion: {criterion}")
    visited = set()
    active = set()

    def visit(ticket_id):
        if ticket_id in active:
            errors.append(f"cyclic ticket dependencies involving {ticket_id}")
            return
        if ticket_id in visited:
            return
        active.add(ticket_id)
        for dep in graph[ticket_id]:
            if dep in graph:
                visit(dep)
        active.remove(ticket_id)
        visited.add(ticket_id)

    for ticket_id in graph:
        visit(ticket_id)

    verification = sections.get("Verification Commands", "")
    subheadings = list(re.finditer(r"^### (.+?)\s*$", verification, re.MULTILINE))
    parts = {}
    for match, body in _parts(verification, subheadings):
        if match.group(1) in parts:
            errors.append(f"duplicate verification section: {match.group(1)}")
        parts[match.group(1)] = body
    for name in parts.keys() - {"Local"}:
        errors.append(f"Verification Commands: unexpected section: {name}")
    body = parts.get("Local", "")
    if not body:
        errors.append("Verification Commands: missing or empty Local section")
    else:
        checks = list(CHECK.finditer(body))
        for heading in re.findall(r"^#### (.+)$", body, re.MULTILINE):
            if not re.match(r"L\d+\s+[—-]\s+.+", heading):
                errors.append(f"Local: unexpected check: {heading}")
        if not checks:
            errors.append("Local: requires at least one L check")
        seen = set()
        for match, check_body in _parts(body, checks):
            check_id = match.group(1)
            if check_id in seen:
                errors.append(f"duplicate check: {check_id}")
            seen.add(check_id)
            _fields(check_body, LOCAL_FIELDS, check_id, errors)

    unknowns = sections.get("Explicit Unknowns", "")
    if unknowns.lower() != "none" and re.search(r"\bblocking\b", unknowns, re.IGNORECASE):
        errors.append("Explicit Unknowns: blocking requirements must be resolved")
    return errors


def main():
    errors = validate(sys.stdin.read())
    if errors:
        for error in errors:
            print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print("VALID: Implementation Package structure")
    return 0


if __name__ == "__main__":
    sys.exit(main())
