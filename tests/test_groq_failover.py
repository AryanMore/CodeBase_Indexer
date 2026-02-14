from types import SimpleNamespace

import AI_Agent.infra.llm as agent_llm
import backend.infra.llm as backend_llm


class RateLimitError(Exception):
    def __init__(self, message="rate limit"):
        super().__init__(message)
        self.status_code = 429


class FakeClient:
    def __init__(self, outcomes):
        self.outcomes = outcomes
        self.call_idx = 0
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        outcome = self.outcomes[self.call_idx]
        self.call_idx += 1
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=outcome))])


def test_backend_groq_failover_to_second_key(monkeypatch):
    monkeypatch.setattr(backend_llm, "USE_GROQ", True)
    monkeypatch.setattr(backend_llm, "_GROQ_START_INDEX", 0)
    monkeypatch.setattr(
        backend_llm,
        "_GROQ_CLIENTS",
        [FakeClient([RateLimitError()]), FakeClient(["ok-from-second"])],
    )

    result = backend_llm.chat("hi", max_tokens=50)
    assert result == "ok-from-second"


def test_agent_groq_failover_to_second_key(monkeypatch):
    monkeypatch.setattr(agent_llm, "USE_GROQ", True)
    monkeypatch.setattr(agent_llm, "_GROQ_START_INDEX", 0)
    monkeypatch.setattr(
        agent_llm,
        "_GROQ_CLIENTS",
        [FakeClient([RateLimitError()]), FakeClient(["ok-agent-second"])],
    )

    result = agent_llm.chat("hi", max_tokens=50)
    assert result == "ok-agent-second"
