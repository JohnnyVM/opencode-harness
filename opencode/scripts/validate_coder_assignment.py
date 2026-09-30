"""Read-only structural validator for Coder Assignments (v1)."""

import re
import sys


SECTIONS = (
    "Objective",
    "Relevant Specification",
    "Relevant Architecture",
    "Ticket Scope",
    "Acceptance Criteria",
    "Test Strategy",
    "Focused Checks",
    "Repository Snapshot",
    "Dependency Outputs",
    "Test-First Evidence",
)
SCOPE_FIELDS = ("Ticket", "Dependencies", "Allowed", "Forbidden", "Approach")
SNAPSHOT_FIELDS = (
    "Branch",
    "Baseline",
    "Expected HEAD",
    "Expected candidate",
    "Additional allowed scope",
)
CHECK_FIELDS = ("Command", "Working directory", "Prerequisites", "Expected")


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


def validate(text):
    """Return every structural finding without changing the supplied text."""
    errors = []
    if re.findall(r"^status:\s*(\S.*)$", text, re.MULTILINE) != ["ASSIGNMENT_READY"]:
        errors.append("requires exactly one ASSIGNMENT_READY status")
    if re.search(r"\b(?:TBD|TODO)\b|\{\{[^{}\n]+\}\}", text, re.IGNORECASE):
        errors.append("contains a placeholder or unresolved TODO/TBD")

    headings = list(re.finditer(r"^## (.+?)\s*$", text, re.MULTILINE))
    found = {}
    for heading, body in _parts(text, headings):
        name = heading.group(1)
        if name in found:
            errors.append(f"duplicate section: {name}")
        found[name] = body
    for name in SECTIONS:
        if not found.get(name):
            errors.append(f"missing or empty section: {name}")
    for name in found.keys() - set(SECTIONS):
        errors.append(f"unexpected section: {name}")

    scope = _fields(found.get("Ticket Scope", ""), SCOPE_FIELDS, "Ticket Scope", errors)
    if scope.get("Allowed", "").lower() == "none":
        errors.append("Ticket Scope: Allowed requires concrete scope")
    if scope.get("Approach", "").lower() == "none":
        errors.append("Ticket Scope: Approach requires implementation detail")
    _fields(found.get("Repository Snapshot", ""), SNAPSHOT_FIELDS, "Repository Snapshot", errors)

    checks = found.get("Focused Checks", "")
    check_headings = list(re.finditer(r"^### (C\d+)\s+[—-]\s+(.+)$", checks, re.MULTILINE))
    if not check_headings:
        errors.append("Focused Checks requires at least one C check")
    for check, body in _parts(checks, check_headings):
        _fields(body, CHECK_FIELDS, check.group(1), errors)

    criteria = found.get("Acceptance Criteria", "")
    if not re.search(r"^- AC\d+:\s*\S", criteria, re.MULTILINE):
        errors.append("Acceptance Criteria requires at least one verbatim AC criterion")
    relevant = found.get("Relevant Specification", "") + found.get("Relevant Architecture", "")
    if re.search(r"\bblocking\b", relevant, re.IGNORECASE):
        errors.append("blocking unknowns must be resolved before coder dispatch")
    return errors


def main():
    errors = validate(sys.stdin.read())
    if errors:
        for error in errors:
            print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print("VALID: Coder Assignment v1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
