import { execFileSync, spawnSync } from "node:child_process"
import { readFileSync } from "node:fs"
import { fileURLToPath } from "node:url"
import { resolve as resolvePath } from "node:path"

const implementationValidator = fileURLToPath(new URL("../scripts/validate_architecture_package.py", import.meta.url))
const specificationValidator = fileURLToPath(new URL("../scripts/validate_specification_package.py", import.meta.url))
const assignmentValidator = fileURLToPath(new URL("../scripts/validate_coder_assignment.py", import.meta.url))
const issueReference = /^([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)#([1-9]\d*)$/
const issueURL = /^https:\/\/github\.com\/([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)\/issues\/([1-9]\d*)\/?$/

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

function loadSource(source, directory, validator, label) {
  const reference = source.trim()
  if (!reference) throw new Error("Usage: source must be owner/repo#number, a GitHub issue URL, or a local file path")

  const issue = issueReference.exec(reference) ?? issueURL.exec(reference)
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
    throw new Error(`Invalid ${label} in ${reference}:\n${result.stderr.trim() || `validator exited ${result.status}`}`)
  }
  return { text, clarification }
}

function commandArguments(value) {
  const argumentsText = value.trim()
  const quote = argumentsText[0]
  if ((quote === '"' || quote === "'") && argumentsText.at(-1) === quote) {
    return argumentsText.slice(1, -1)
  }
  return argumentsText
}

export default async ({ directory }) => ({
  "command.execute.before": async (input, output) => {
    if (input.command === "architect") {
      const argumentsText = commandArguments(input.arguments)
      const marker = " --output "
      const index = argumentsText.indexOf(marker)
      if (index < 0 || argumentsText.indexOf(marker, index + marker.length) >= 0) {
        throw new Error("Usage: /architect <source> --output <local-path>")
      }
      const source = argumentsText.slice(0, index)
      const destination = argumentsText.slice(index + marker.length).trim()
      if (!destination) throw new Error("Usage: /architect <source> --output <local-path>")
      const packageInput = loadSource(source, directory, specificationValidator, "Specification Package")
      const normalized = resolvePath(directory, destination)
      output.parts.splice(0, output.parts.length,
        { type: "text", text: `Create an Architecture Package and write it to this output path: ${normalized}` },
        { type: "text", text: packageInput.text },
        ...(packageInput.clarification ? [{ type: "text", text: packageInput.clarification }] : []),
      )
      return
    }
    if (input.command === "implement") {
      const packageInput = loadSource(commandArguments(input.arguments), directory, implementationValidator, "Architecture Package")
      const parts = packageInput.clarification
        ? [
            { type: "text", text: packageInput.clarification },
            { type: "text", text: packageInput.text },
          ]
        : [{ type: "text", text: packageInput.text }]
      output.parts.splice(0, output.parts.length, ...parts)
    }
  },
  "tool.execute.before": async (input, output) => {
    if (input.tool !== "task") return
    if (!["coder-light", "coder-heavy"].includes(output.args?.subagent_type)) return
    const result = spawnSync("python3", [assignmentValidator], { input: output.args.prompt, encoding: "utf8" })
    if (result.error) throw new Error(`Cannot run coder assignment validator: ${result.error.message}`, { cause: result.error })
    if (result.status !== 0) {
      throw new Error(`Invalid coder assignment; refusing task dispatch:\n${result.stderr.trim() || `validator exited ${result.status}`}`)
    }
  },
})
