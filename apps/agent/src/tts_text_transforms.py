"""TTS text transforms for Voxtral output shaping.

Wired into ``AgentSession(tts_text_transforms=[...])`` so LLM output is
normalised before it reaches the TTS plugin. This is the LiveKit-official
hook for exactly this purpose — see
https://docs.livekit.io/agents/multimodality/text/.

A text transform is a ``Callable[[AsyncIterable[str]], AsyncIterable[str]]``:
it receives the streaming text chunks produced upstream and yields
transformed chunks. Transforms are chained in order in LiveKit's
``_apply_text_transforms`` pipeline.

The two transforms here are deliberately narrow:

- ``NumberTransform`` only handles ``HH:MM`` time patterns (``14:30`` →
  ``14 Uhr 30``). Voxtral renders plain digits well in German; we only
  intercept the patterns that reliably confuse TTS.
- ``PronunciationTransform`` is a dict-driven substring replacer for
  proper nouns Voxtral mispronounces (e.g. ``Frappe`` → ``Frapp``).

Both classes are callable instances whose ``__call__`` is an async
generator, which satisfies LiveKit's ``TextTransforms`` callable-protocol
contract at runtime.
"""
from __future__ import annotations

import re
from typing import AsyncIterable


class PronunciationTransform:
    """Replace substrings according to a fixed mapping before TTS.

    The mapping is case-sensitive. Keys are sorted by length descending
    so that longer keys match before their prefixes (e.g. ``ERPNext``
    wins over ``ERP``). An empty mapping is a no-op passthrough.
    """

    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = dict(mapping)
        keys_sorted = sorted(self._mapping.keys(), key=len, reverse=True)
        if keys_sorted:
            self._pattern: re.Pattern[str] | None = re.compile(
                "|".join(re.escape(k) for k in keys_sorted)
            )
        else:
            self._pattern = None

    async def __call__(self, text: AsyncIterable[str]) -> AsyncIterable[str]:
        pattern = self._pattern
        mapping = self._mapping
        if pattern is None:
            async for chunk in text:
                yield chunk
            return
        async for chunk in text:
            yield pattern.sub(lambda m: mapping[m.group(0)], chunk)


class NumberTransform:
    """Expand selected numeric patterns to spoken German form.

    Current scope (MVP):

    - ``HH:MM`` time → ``<H> Uhr <MM>`` (``14:30`` → ``14 Uhr 30``).

    Extend this transform when a specific misrendering is observed in
    production logs and the TTS output is reproducibly wrong. Avoid
    broad digit-to-word conversions — Voxtral handles natural-sounding
    numbers already; over-eager rewriting causes more regressions than
    it fixes.
    """

    _TIME_RE = re.compile(r"\b(\d{1,2}):(\d{2})\b")

    async def __call__(self, text: AsyncIterable[str]) -> AsyncIterable[str]:
        time_re = self._TIME_RE
        async for chunk in text:
            yield time_re.sub(
                lambda m: f"{m.group(1)} Uhr {m.group(2)}", chunk
            )
