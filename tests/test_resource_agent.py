import pytest

from agents.resource_agent import ResourceAgent


def test_resource_agent_imports_cleanly():
    assert ResourceAgent.name == "resource_agent"
