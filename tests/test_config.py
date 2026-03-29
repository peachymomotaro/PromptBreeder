import unittest

from pb.config import resolve_cohere_api_key


class ConfigTests(unittest.TestCase):
    def test_explicit_key_wins_over_env_key(self):
        self.assertEqual(
            resolve_cohere_api_key("entered-key", "env-key"),
            "entered-key",
        )

    def test_blank_explicit_key_falls_back_to_env_key(self):
        self.assertEqual(
            resolve_cohere_api_key("", "env-key"),
            "env-key",
        )

    def test_missing_keys_return_empty_string(self):
        self.assertEqual(
            resolve_cohere_api_key(None, None),
            "",
        )
