"""
Mock LLM for E2E testing - provides deterministic responses.

This mock replaces the actual OpenAI LLM with predefined responses to ensure:
- Consistent test results
- No API costs
- Faster test execution
- No rate limits
"""

import json
from typing import Dict


class MockLLMResponse:
    """Mock response object that mimics LangChain's AIMessage."""

    def __init__(self, content: str):
        self.content = content

    def __str__(self):
        return self.content


class MockLLM:
    """
    Mock LLM that returns deterministic responses based on the prompt.
    Mimics the ChatOpenAI interface from LangChain.
    """

    def __init__(self, **kwargs):
        """Initialize with any kwargs to match ChatOpenAI interface."""
        self.model = kwargs.get("model", "mock-gpt-4")
        self.temperature = kwargs.get("temperature", 0)
        self.responses = self._get_mock_responses()

    def _get_mock_responses(self) -> Dict[str, str]:
        """Define mock responses for different types of prompts."""
        return {
            # Out of scope detection
            "out_of_scope": json.dumps(
                {
                    "status": "valid",
                    "keywords": ["machine learning", "healthcare", "papers"],
                }
            ),
            # Filter detection
            "filter_detection": json.dumps(
                {
                    "has_filter_instructions": False,
                    "reason": "No specific filters detected in query",
                }
            ),
            # QC decision
            "qc_decision": json.dumps(
                {
                    "qc_decision": "accept",
                    "reason": "Query is clear and specific enough for paper search",
                }
            ),
            # Paper summary
            "paper_summary": "This paper presents novel approaches to machine learning in healthcare, directly relevant to your research interests in automated diagnosis systems.",
            # Default response
            "default": json.dumps(
                {"status": "success", "message": "Mock LLM response"}
            ),
        }

    def invoke(self, prompt: str) -> MockLLMResponse:
        """
        Mock invoke method that returns deterministic responses based on prompt content.

        Args:
            prompt: The input prompt (string or list of messages)

        Returns:
            MockLLMResponse with appropriate content
        """
        # Convert prompt to string if it's a list of messages
        if isinstance(prompt, list):
            prompt_text = " ".join([str(msg) for msg in prompt])
        else:
            prompt_text = str(prompt).lower()

        # Match prompt to appropriate response
        if "out of scope" in prompt_text or "out-of-scope" in prompt_text:
            return MockLLMResponse(self.responses["out_of_scope"])
        elif "filter" in prompt_text and "detection" in prompt_text:
            return MockLLMResponse(self.responses["filter_detection"])
        elif "qc_decision" in prompt_text or "quality control" in prompt_text:
            return MockLLMResponse(self.responses["qc_decision"])
        elif "summary" in prompt_text or "relevant" in prompt_text:
            return MockLLMResponse(self.responses["paper_summary"])
        else:
            return MockLLMResponse(self.responses["default"])

    def __call__(self, *args, **kwargs):
        """Allow calling the mock like a function."""
        if args:
            return self.invoke(args[0])
        return self.invoke("")


# Create mock instances matching LLMDefinition.py structure
mock_llm_41 = MockLLM(model="mock-gpt-4.1", temperature=0.3)
mock_llm_40 = MockLLM(model="mock-gpt-4", temperature=0)
mock_llm_4o = MockLLM(model="mock-gpt-4.1", temperature=0.3)
mock_llm_mini = MockLLM(model="mock-gpt-4o-mini", temperature=0.5)

# Default mock LLM
MockedLLM = mock_llm_41
