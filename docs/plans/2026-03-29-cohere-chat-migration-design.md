# Cohere Chat Migration Design

## Summary

PromptBreeder currently relies on Cohere's deprecated Generate API through direct calls to `model.generate(...)` and `model.batch_generate(...)`. The approved approach is a minimal compatibility pass that preserves the current algorithm, SDK version, CLI flow, and Streamlit flow while swapping generation calls to `Client.chat(...)` under a thin adapter layer.

## Goals

- Remove direct use of Cohere Generate endpoints from the codebase.
- Preserve current mutation and fitness evaluation behavior as closely as possible.
- Keep the migration tightly scoped so it can be verified quickly.

## Non-goals

- No broader SDK refresh or `ClientV2` migration.
- No model-selection cleanup or prompt redesign.
- No new fallback behavior, retry policy, or UI changes.

## Current State

The current Cohere touchpoints are concentrated in three places:

- `pb/__init__.py` uses `batch_generate(...)` to initialize prompts and evaluate fitness.
- `pb/mutation_operators.py` uses `generate(...)` for each mutation operator.
- `main.py` and `sl_main.py` construct the existing `cohere.Client(...)` instance.

The pinned SDK, `cohere==4.37`, already exposes `Client.chat(...)`, so a compatibility layer can be added without a package upgrade.

## Proposed Approach

Add a small adapter module, `pb/cohere_compat.py`, with two helper functions:

- `chat_text(model, prompt, **kwargs) -> str`
- `batch_chat_text(model, prompts, **kwargs) -> list[str]`

`chat_text(...)` will call `model.chat(message=prompt, ...)` and return `response.text`.

`batch_chat_text(...)` will preserve the current batch-style interface by running `chat_text(...)` across prompts in a thread pool and returning plain text results in input order. This matches the existing use of `batch_generate(...)` closely enough for a minimal migration.

## File Changes

### `pb/cohere_compat.py`

New module that centralizes all Cohere chat interaction. It should:

- accept the existing `cohere.Client` instance
- support forwarding keyword arguments such as `temperature`
- return strings instead of Cohere generation objects
- preserve prompt ordering for batch results

### `pb/__init__.py`

Replace:

- initial population creation via `model.batch_generate(prompts)`
- fitness evaluation via threaded `model.batch_generate(...)`

With:

- `batch_chat_text(model, prompts, ...)`

The surrounding population and regex-scoring logic should stay intact. The only response-shape change is that the code will consume plain text strings instead of indexing into generation objects.

### `pb/mutation_operators.py`

Replace every `model.generate(...)[0].text` call with `chat_text(model, ...)`.

This keeps each mutator's prompt construction unchanged while moving the actual API call to the adapter.

### `main.py` and `sl_main.py`

No planned logic changes beyond keeping the existing `cohere.Client(...)` construction as-is.

## Behavior and Data Flow

Each existing prompt will become a one-shot chat message:

- no conversation state
- no chat history
- no preamble override
- no new model defaults

This follows Cohere's migration guidance while keeping semantics as close as possible to today's raw-prompt usage.

## Error Handling

The migration should preserve current failure behavior:

- single-call failures should still raise through the mutator path
- batch failures during fitness evaluation should still surface through the existing executor path

The adapter should not add silent fallbacks or retries beyond what the SDK already does.

## Testing Strategy

This repo does not currently have a test suite, so the migration should add a small adapter-focused test using the standard library:

- create a fake model whose `chat(...)` returns an object with `.text`
- verify `chat_text(...)` returns that text and forwards kwargs
- verify `batch_chat_text(...)` preserves prompt order

Then run lightweight smoke verification:

- a targeted unit test for the adapter
- a short CLI run or import check to confirm the updated call paths still load

## Risks

- Chat responses may differ slightly from Generate responses because Cohere now treats prompts as chat messages.
- Any code that depends on Generate's object shape must be fully converted to plain-text handling.
- Fitness evaluation currently appends executor results as they complete, which may already risk unit/result misalignment; this migration should avoid making that worse and ideally preserve input ordering in the adapter.

## Approved Direction

The approved implementation path is:

1. Add a thin compatibility adapter around `Client.chat(...)`.
2. Update internal callsites to consume plain text from that adapter.
3. Verify the minimal migration without broader SDK or product changes.
