# OpenCode configuration

This repository provides nine standalone skills and a Playwright MCP config:

- `codebase-design`
- `domain-modeling`
- `github`
- `grill-me`
- `grill-with-docs` (uses `grilling` and `domain-modeling`)
- `grilling`
- `setup-skills` (invoked with `/setup-skills`)
- `to-spec`
- `to-tickets`

The Matt Pocock skills are adapted from
[mattpocock/skills](https://github.com/mattpocock/skills) at
`49dd158d1076134a641b33efb035946536778336` (MIT; see
`LICENSE-MATT-POCOCK-SKILLS`).

Install the configuration as symlinks with:

```sh
python3 scripts/install.py
```

Use `--dry-run` to preview the links. Existing destination files are left
untouched.
