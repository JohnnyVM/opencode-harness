import { execFileSync, spawnSync } from "node:child_process"
import { readFileSync } from "node:fs"
import { fileURLToPath } from "node:url"
import { extname, resolve as resolvePath } from "node:path"

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

function architectArguments(value) {
  const usage = "Usage: /architect <source> [<local-path> | --output <local-path>]"
  let text = value.trim()
  // Preserve the legacy form where the entire flagged command is quoted.
  if (/^("[^"]*"|'[^']*')$/.test(text) && /\s--output(?:\s|$)/.test(text)) {
    text = commandArguments(text)
  }
  const flagged = text.split(/\s+--output(?:\s+|$)/)
  if (flagged.length > 1) {
    if (flagged.length !== 2 || !flagged[0].trim() || !flagged[1].trim()) throw new Error(usage)
    return { source: commandArguments(flagged[0]), destination: commandArguments(flagged[1]) }
  }

  const tokens = []
  const token = /\s*(?:"([^"]*)"|'([^']*)'|([^\s"']+))(?=\s|$)/gy
  while (token.lastIndex < text.length) {
    const match = token.exec(text)
    if (!match) throw new Error(usage)
    tokens.push(match[1] ?? match[2] ?? match[3])
  }
  if (tokens.length < 1 || tokens.length > 2 || tokens.some(part => !part || part.startsWith("--"))) {
    throw new Error(usage)
  }
  const [source, explicitDestination] = tokens
  const extension = extname(source)
  const stem = extension ? source.slice(0, -extension.length) : source
  return { source, destination: explicitDestination ?? `${stem}-architecture${extension}` }
}

export default async ({ directory }) => ({
  "command.execute.before": async (input, output) => {
    if (input.command === "architect") {
      const { source, destination } = architectArguments(input.arguments)
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
