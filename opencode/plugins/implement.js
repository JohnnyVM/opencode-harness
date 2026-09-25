import { execFileSync, spawnSync } from "node:child_process"
import { readFileSync } from "node:fs"
import { fileURLToPath } from "node:url"
import { resolve as resolvePath } from "node:path"

const validator = fileURLToPath(new URL("../scripts/validate_implementation_package.py", import.meta.url))
const issueReference = /^([A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+)#([1-9]\d*)$/

function loadPackage(source, directory) {
  const reference = source.trim()
  if (!reference) throw new Error("Usage: /implement owner/repo#number or /implement path/to/package.md")

  const issue = issueReference.exec(reference)
  let text
  if (issue) {
    let response
    try {
      response = execFileSync("gh", ["issue", "view", issue[2], "--repo", issue[1], "--json", "body"], {
        cwd: directory,
        encoding: "utf8",
      })
      text = JSON.parse(response).body
    } catch (error) {
      throw new Error(`Cannot read GitHub issue ${reference}: ${error.message}`, { cause: error })
    }
    if (typeof text !== "string") throw new Error(`GitHub issue ${reference} has no text body`)
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
  return text
}

export default async ({ directory }) => ({
  "command.execute.before": async (input, output) => {
    if (input.command !== "implement") return
    const text = loadPackage(input.arguments, directory)
    output.parts.splice(0, output.parts.length, { type: "text", text })
  },
})
