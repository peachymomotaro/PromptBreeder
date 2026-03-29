# Cohere Chat Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace direct Cohere Generate API usage with a thin Chat-based compatibility layer while preserving the current PromptBreeder workflow.

**Architecture:** Add a small adapter module that wraps `cohere.Client.chat(...)` for single and batched text generation, then update the existing population initialization, mutation, and fitness evaluation code to consume plain text from that adapter. Keep the current SDK, client construction, and application entrypoints unchanged.

**Tech Stack:** Python, Cohere Python SDK 4.37, Streamlit, Pydantic, `unittest`, `concurrent.futures`

---

### Task 1: Add a focused adapter test

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_cohere_compat.py`

**Step 1: Write the failing test**

```python
import unittest

from pb.cohere_compat import batch_chat_text, chat_text


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModel:
    def __init__(self):
        self.calls = []

    def chat(self, message=None, **kwargs):
        self.calls.append((message, kwargs))
        return FakeResponse(f"reply:{message}")


class CohereCompatTests(unittest.TestCase):
    def test_chat_text_returns_response_text(self):
        model = FakeModel()
        result = chat_text(model, "hello", temperature=0)
        self.assertEqual(result, "reply:hello")
        self.assertEqual(model.calls[0], ("hello", {"temperature": 0}))

    def test_batch_chat_text_preserves_prompt_order(self):
        model = FakeModel()
        result = batch_chat_text(model, ["a", "b", "c"], max_workers=2, temperature=0)
        self.assertEqual(result, ["reply:a", "reply:b", "reply:c"])
```

**Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_cohere_compat -v`
Expected: FAIL with `ModuleNotFoundError` for `pb.cohere_compat`

**Step 3: Commit**

```bash
git add tests/__init__.py tests/test_cohere_compat.py
git commit -m "test: add coverage for cohere chat adapter"
```

### Task 2: Implement the chat compatibility adapter

**Files:**
- Create: `pb/cohere_compat.py`
- Test: `tests/test_cohere_compat.py`

**Step 1: Write minimal implementation**

```python
from concurrent.futures import ThreadPoolExecutor


def chat_text(model, prompt, **kwargs):
    response = model.chat(message=prompt, **kwargs)
    return response.text


def batch_chat_text(model, prompts, max_workers=None, **kwargs):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(lambda prompt: chat_text(model, prompt, **kwargs), prompts))
```

**Step 2: Run test to verify it passes**

Run: `python -m unittest tests.test_cohere_compat -v`
Expected: PASS

**Step 3: Commit**

```bash
git add pb/cohere_compat.py tests/test_cohere_compat.py
git commit -m "feat: add cohere chat compatibility adapter"
```

### Task 3: Migrate population initialization and fitness evaluation

**Files:**
- Modify: `pb/__init__.py`
- Test: `tests/test_cohere_compat.py`

**Step 1: Replace Generate-specific helpers**

Update imports and callsites so `init_run(...)` and `_evaluate_fitness(...)` use `batch_chat_text(...)` and consume plain strings.

```python
from pb.cohere_compat import batch_chat_text

results = batch_chat_text(model, prompts, max_workers=model.num_workers)

for i, item in enumerate(results):
    population.units[i].P = item
```

```python
future_to_fit = {
    executor.submit(
        batch_chat_text,
        model,
        example_batch,
        model.num_workers,
        temperature=0,
    ): example_batch
    for example_batch in examples
}
```

```python
valid = re.search(gsm.gsm_extract_answer(batch[i]['answer']), x)
```

**Step 2: Run the adapter test and a lightweight import check**

Run: `python -m unittest tests.test_cohere_compat -v`
Expected: PASS

Run: `python -c "from pb import create_population"`
Expected: command exits successfully

**Step 3: Commit**

```bash
git add pb/__init__.py
git commit -m "refactor: use cohere chat in population evaluation"
```

### Task 4: Migrate mutation operators to the adapter

**Files:**
- Modify: `pb/mutation_operators.py`

**Step 1: Replace direct generate calls**

Import `chat_text` and convert each mutator:

```python
from pb.cohere_compat import chat_text

result = chat_text(model, problem_description + " An ordered list of 100 hints: ")
unit.P = chat_text(model, unit.M + " " + unit.P)
unit.M = chat_text(model, HYPER_MUTATION_PROMPT + unit.M)
```

Keep prompt assembly unchanged; only swap the Cohere call and response extraction.

**Step 2: Run a lightweight import check**

Run: `python -c "from pb.mutation_operators import mutate"`
Expected: command exits successfully

**Step 3: Commit**

```bash
git add pb/mutation_operators.py
git commit -m "refactor: route mutation operators through cohere chat"
```

### Task 5: Verify runtime behavior and update docs

**Files:**
- Modify: `README.md`

**Step 1: Add a short note to the setup or usage docs**

Document that the app now uses Cohere chat under the hood and still expects `COHERE_API_KEY` in `.env`.

**Step 2: Run smoke verification**

Run: `python -m unittest tests.test_cohere_compat -v`
Expected: PASS

Run: `python main.py -mp 1 -ts 1 -e 1 -n 1 -p "Solve the math word problem, giving your answer as an arabic numeral."`
Expected: program starts, initializes the population, and reaches Cohere-backed execution without `generate` endpoint calls

Optional: `streamlit run sl_main.py`
Expected: app starts and accepts a Cohere key in the UI

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: note cohere chat migration"
```
