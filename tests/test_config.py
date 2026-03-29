import unittest

from pb.config import resolve_cohere_api_key, resolve_requests_per_minute


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

    def test_resolve_requests_per_minute_parses_positive_integer(self):
        self.assertEqual(
            resolve_requests_per_minute("20"),
            20,
        )

    def test_resolve_requests_per_minute_rejects_blank_or_invalid_values(self):
        self.assertIsNone(resolve_requests_per_minute(""))
        self.assertIsNone(resolve_requests_per_minute(None))
        self.assertIsNone(resolve_requests_per_minute("0"))
        self.assertIsNone(resolve_requests_per_minute("-1"))
        self.assertIsNone(resolve_requests_per_minute("abc"))
