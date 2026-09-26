"""Tests for specification agent guidance and behavior."""

import unittest
from pathlib import Path


class SpecAgentGuidanceTests(unittest.TestCase):
    def test_test_investigation_agent_has_correct_structure(self):
        """Test that the test-investigation agent has the expected structure."""
        # Read the agent file
        test_investigation_path = Path("opencode/agents/test-investigation.md")
        self.assertTrue(test_investigation_path.exists(), 
                       "test-investigation.md should exist")
        
        test_investigation_content = test_investigation_path.read_text()
        
        # Check that the agent has the expected goal
        self.assertIn("Analyze test coverage", test_investigation_content)
        
        # Check that the agent has the expected investigation method
        self.assertIn("Map behaviors, acceptance criteria", test_investigation_content)
        
        # Check that the agent has the expected output format
        self.assertIn("Coverage analysis", test_investigation_content)
        self.assertIn("Recommended action", test_investigation_content)
        self.assertIn("Duplicate check", test_investigation_content)
        self.assertIn("Red plan or prerequisite", test_investigation_content)
        
        # Check that it's a subagent with readonly permissions
        self.assertIn("mode: subagent", test_investigation_content)
        self.assertIn("edit: deny", test_investigation_content)
        self.assertIn("question: deny", test_investigation_content)
        self.assertIn("skill: deny", test_investigation_content)

    def test_code_pattern_agent_has_correct_structure(self):
        """Test that the code-pattern agent has the expected structure."""
        # Read the agent file
        code_pattern_path = Path("opencode/agents/code-pattern.md")
        self.assertTrue(code_pattern_path.exists(), 
                       "code-pattern.md should exist")
        
        code_pattern_content = code_pattern_path.read_text()
        
        # Check that the agent has the expected goal
        self.assertIn("Analyze observed constraints", code_pattern_content)
        
        # Check that the agent has the expected analysis method
        self.assertIn("Distinguish observed constraints", code_pattern_content)
        
        # Check that the agent has the expected output format
        self.assertIn("Structural guidance", code_pattern_content)
        self.assertIn("Agent-facing documentation recommendations", code_pattern_content)
        
        # Check that it's a subagent with readonly permissions
        self.assertIn("mode: subagent", code_pattern_content)
        self.assertIn("edit: deny", code_pattern_content)
        self.assertIn("question: deny", code_pattern_content)
        self.assertIn("skill: deny", code_pattern_content)

    def test_agent_documentation_recommendations(self):
        """Test that code-pattern agent includes documentation recommendations."""
        # The code-pattern agent should include agent-facing documentation recommendations
        code_pattern_content = Path("opencode/agents/code-pattern.md").read_text()
        self.assertIn("Agent-facing documentation recommendations", code_pattern_content)
        self.assertIn("Target file/location", code_pattern_content)
        self.assertIn("Proposed concrete wording/action", code_pattern_content)
        self.assertIn("Evidence", code_pattern_content)
        self.assertIn("Expected benefit", code_pattern_content)
        self.assertIn("Reason", code_pattern_content)
        self.assertIn("Applicability", code_pattern_content)
        
        # Check that test-investigation doesn't have this section
        test_investigation_content = Path("opencode/agents/test-investigation.md").read_text()
        self.assertNotIn("Agent-facing documentation recommendations", test_investigation_content)

    def test_both_agents_are_conditional_advisors(self):
        """Test that both agents are configured as conditional advisors."""
        test_investigation_content = Path("opencode/agents/test-investigation.md").read_text()
        code_pattern_content = Path("opencode/agents/code-pattern.md").read_text()
        
        # Both should be subagents and not approval stages
        self.assertIn("mode: subagent", test_investigation_content)
        self.assertIn("mode: subagent", code_pattern_content)
        
        # They should not be approval stages (they don't have approval-related permissions)
        self.assertNotIn("approve:", test_investigation_content)
        self.assertNotIn("approve:", code_pattern_content)
        
        # They should be read-only
        self.assertIn("edit: deny", test_investigation_content)
        self.assertIn("edit: deny", code_pattern_content)
        self.assertIn("question: deny", test_investigation_content)
        self.assertIn("question: deny", code_pattern_content)
        self.assertIn("skill: deny", test_investigation_content)
        self.assertIn("skill: deny", code_pattern_content)


if __name__ == "__main__":
    unittest.main()
