import unittest

import pb as pb_module
from pb import create_population, init_run


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeChatModel:
    def __init__(self):
        self.num_workers = 2

    def chat(self, message=None, **kwargs):
        if "INSTRUCTION MUTANT =" in message:
            return FakeResponse("Use arithmetic.")

        return FakeResponse("The answer is 2")


class PopulationChatFlowTests(unittest.TestCase):
    def test_init_run_initializes_and_scores_population_via_chat(self):
        original_examples = pb_module.gsm8k_examples
        pb_module.gsm8k_examples = [{"question": "What is 1 + 1?", "answer": "#### 2"}]

        try:
            population = create_population(["Think step by step."], ["Rewrite clearly."], "Solve the problem.")
            population = init_run(population, FakeChatModel(), 1)

            self.assertEqual(population.units[0].P, "Use arithmetic.")
            self.assertEqual(population.units[0].fitness, 1.0)
        finally:
            pb_module.gsm8k_examples = original_examples
