import tempfile
from pathlib import Path
import unittest

from scripts.install_context_analysis_plugin import patch_tokenizer_api


class ContextPluginSetupTests(unittest.TestCase):
    def test_patches_legacy_and_current_tiktoken_exports_idempotently(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "context-usage.ts"
            source.write_text(
                '  const { encoding_for_model, get_encoding } = mod\n'
                '    encoder = encoding_for_model(model)\n'
                '    encoder = get_encoding("cl100k_base")\n'
            )

            self.assertTrue(patch_tokenizer_api(source))
            patched = source.read_text()
            self.assertIn("mod.encodingForModel", patched)
            self.assertIn("mod.getEncoding", patched)
            self.assertIn("encoder = encodingForModel(model)", patched)
            self.assertIn('encoder = getEncoding("cl100k_base")', patched)
            self.assertFalse(patch_tokenizer_api(source))

    def test_refuses_unrecognized_upstream_source(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "context-usage.ts"
            source.write_text("unexpected upstream implementation")
            with self.assertRaisesRegex(ValueError, "Unsupported upstream"):
                patch_tokenizer_api(source)


if __name__ == "__main__":
    unittest.main()
