from types import SimpleNamespace

from AI_Agent.graph.nodes import reasoning


def chunk(content: str):
    return SimpleNamespace(
        file_path="a.py",
        start_line=1,
        end_line=3,
        code_type="py:function",
        content=content,
    )


def test_clip_truncates_large_chunk_text(monkeypatch):
    monkeypatch.setattr(reasoning, "MAX_CONTEXT_CHARS_PER_CHUNK", 20)

    text = "x" * 100
    clipped = reasoning._clip(text, reasoning.MAX_CONTEXT_CHARS_PER_CHUNK)

    assert len(clipped) > 20
    assert clipped.endswith("[truncated for latency]")


def test_build_context_uses_clipped_content(monkeypatch):
    monkeypatch.setattr(reasoning, "MAX_CONTEXT_CHARS_PER_CHUNK", 10)

    ctx = reasoning._build_context([chunk("abcdefghijklmnopqrstuvwxyz")])

    assert "FILE: a.py" in ctx
    assert "[truncated for latency]" in ctx
