import { execFileSync, spawnSync } from "node:child_process"
import { readFileSync } from "node:fs"
import { fileURLToPath } from "node:url"
import { resolve as resolvePath } from "node:path"

const validator = fileURLToPath(new URL("../scripts/validate_implementation_package.py", import.meta.url))
const issueReference = /^([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)#([1-9]\d*)$/

function loadIssue(reference, issue, directory) {
  let response
  try {
    response = execFileSync("gh", ["issue", "view", issue[2], "--repo", issue[1], "--json", "body,state"], {
      cwd: directory,
      encoding: "utf8",
    })
  } catch (error) {
    const detail = typeof error.stderr === "string" ? error.stderr.trim() : ""
    throw new Error(
      `BLOCKED_SPEC: GitHub issue ${reference} does not exist or is inaccessible${detail ? `: ${detail}` : ""}`,
      { cause: error },
    )
  }

  const payload = JSON.parse(response)
  if (payload.state !== "OPEN" && payload.state !== "CLOSED") {
    throw new Error(
      `BLOCKED_SPEC: GitHub issue ${reference} has unsupported state ${JSON.stringify(payload.state)}.`,
    )
  }
  if (typeof payload.body !== "string") throw new Error(`GitHub issue ${reference} has no text body`)
  return {
    text: payload.body,
    clarification:
      payload.state === "CLOSED"
        ? `CLOSED_ISSUE_CLARIFICATION_REQUIRED: GitHub issue ${reference} is closed. ` +
          "Ask the user whether to proceed with this closed issue or stop. Do not begin implementation until the user explicitly confirms."
        : undefined,
  }
}

function loadPackage(source, directory) {
  const reference = source.trim()
  if (!reference) throw new Error("Usage: /implement owner/repo#number or /implement path/to/package.md")

  const issue = issueReference.exec(reference)
  let text
  let clarification
  if (issue) {
    const issuePackage = loadIssue(reference, issue, directory)
    text = issuePackage.text
    clarification = issuePackage.clarification
  } else {
    try {
      text = readFileSync(resolvePath(directory, reference), "utf8")
    } catch (error) {
      throw new Error(`Cannot read package file ${reference}: ${error.message}`, { cause: error })
    }
  }

  const result = spawnSync("python3", [validator], { input: text, encoding: "utf8" })
  if (result.error) throw new Error(`Cannot run package validator: ${result.error.message}`, { cause: result.error })
  if (result.status !== 0) {
    throw new Error(`Invalid Implementation Package in ${reference}:\n${result.stderr.trim() || `validator exited ${result.status}`}`)
  }
  return { text, clarification }
}

export default async ({ directory }) => ({
  "command.execute.before": async (input, output) => {
    if (input.command !== "implement") return
    const packageInput = loadPackage(input.arguments, directory)
    const parts = packageInput.clarification
      ? [
          { type: "text", text: packageInput.clarification },
          { type: "text", text: packageInput.text },
        ]
      : [{ type: "text", text: packageInput.text }]
    output.parts.splice(0, output.parts.length, ...parts)
  },
})
