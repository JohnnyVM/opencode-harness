"""Prepare the upstream context-analysis plugin and its tokenizer dependencies."""

from pathlib import Path
import subprocess
import sys


LEGACY_BINDING = "  const { encoding_for_model, get_encoding } = mod"
COMPATIBLE_BINDING = (
    "  const encodingForModel = mod.encoding_for_model ?? mod.encodingForModel\n"
    "  const getEncoding = mod.get_encoding ?? mod.getEncoding"
)


def patch_tokenizer_api(source):
    """Adapt the upstream tokenizer loader to old and current export spellings."""
    source = Path(source)
    text = source.read_text()
    if LEGACY_BINDING in text:
        text = text.replace(LEGACY_BINDING, COMPATIBLE_BINDING)
        text = text.replace("encoder = encoding_for_model(model)", "encoder = encodingForModel(model)")
        text = text.replace('encoder = get_encoding("cl100k_base")', 'encoder = getEncoding("cl100k_base")')
        if "encoding_for_model(model)" in text or 'get_encoding("cl100k_base")' in text:
            raise ValueError(f"Could not update tokenizer API calls in {source}")
        source.write_text(text)
        return True
    if COMPATIBLE_BINDING in text:
        return False
    raise ValueError(f"Unsupported upstream tokenizer loader in {source}")


def install_dependencies(plugin_root):
    """Install the vetted tokenizer versions into the upstream vendor directory."""
    vendor = Path(plugin_root) / ".opencode" / "plugin" / "vendor"
    return subprocess.run(
        [
            "npm", "install", "--prefix", str(vendor),
            "js-tiktoken@1.0.21", "@huggingface/transformers@4.3.1",
        ],
        check=False,
    ).returncode


def main():
    repository = Path(__file__).resolve().parents[1]
    plugin_root = repository / "opencode/plugins/context-analysis-upstream"
    source = plugin_root / ".opencode/plugin/context-usage.ts"
    if not source.is_file():
        print("Initialize submodules first: git submodule update --init --recursive", file=sys.stderr)
        return 1
    try:
        patched = patch_tokenizer_api(source)
    except (OSError, ValueError) as error:
        print(f"error: cannot prepare context-analysis plugin: {error}", file=sys.stderr)
        return 1
    if patched:
        print(f"Applied tokenizer API compatibility patch to {source}")
    try:
        return install_dependencies(plugin_root)
    except OSError as error:
        print(f"error: cannot install context-analysis dependencies: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
