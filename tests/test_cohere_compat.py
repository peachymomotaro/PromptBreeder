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
