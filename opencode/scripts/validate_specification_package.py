"""Read-only structural validator for Specification Packages (v1)."""

import re
import sys


SECTIONS = (
    "Problem Statement",
    "Solution",
    "User Stories",
    "Product Decisions and Constraints",
    "Testing Decisions",
    "Acceptance Criteria",
    "Risks",
    "Explicit Unknowns",
    "Out of Scope",
)
STATUS = re.compile(r"^status:\s*(\S.*)$", re.MULTILINE)
HEADING = re.compile(r"^## (.+?)\s*$", re.MULTILINE)
CRITERION = re.compile(r"^- (AC\d+):\s*(.+)$", re.MULTILINE)


def sections(text):
    """Return section bodies while reporting duplicate or unexpected headings."""
    errors = []
    result = {}
    headings = list(HEADING.finditer(text))
    for index, heading in enumerate(headings):
        name = heading.group(1)
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[heading.end():end].strip()
        if name in result:
            errors.append(f"duplicate section: {name}")
        result[name] = body
    for name in SECTIONS:
        if not result.get(name):
            errors.append(f"missing or empty section: {name}")
    for name in result.keys() - set(SECTIONS):
        errors.append(f"unexpected section: {name}")
    return result, errors


def validate(text):
    """Return every structural finding without changing the supplied text."""
    errors = []
    statuses = STATUS.findall(text)
    if len(statuses) != 1 or statuses[0] not in {
        "SPEC_APPROVED_BY_AGENT",
        "SPEC_APPROVED_BY_USER",
    }:
        errors.append("requires exactly one valid status field")
    if re.search(r"\b(?:TBD|TODO)\b|\{\{[^{}\n]+\}\}", text, re.IGNORECASE):
        errors.append("contains a placeholder or unresolved TODO/TBD")

    found, section_errors = sections(text)
    errors.extend(section_errors)
    criteria = list(CRITERION.finditer(found.get("Acceptance Criteria", "")))
    if not criteria:
        errors.append("Acceptance Criteria requires at least one AC criterion")
    criterion_ids = [match.group(1) for match in criteria]
    if len(criterion_ids) != len(set(criterion_ids)):
        errors.append("duplicate criterion")

    unknowns = found.get("Explicit Unknowns", "")
    if unknowns.lower() != "none" and re.search(r"\bblocking\b", unknowns, re.IGNORECASE):
        errors.append("Explicit Unknowns: blocking requirements must be resolved")
    return errors


def main():
    errors = validate(sys.stdin.read())
    if errors:
        for error in errors:
            print(f"INVALID: {error}", file=sys.stderr)
        return 1
    print("VALID: Specification Package v1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
