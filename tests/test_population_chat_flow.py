import time
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


class DelayedFitnessModel:
    def __init__(self):
        self.num_workers = 1

    def chat(self, message=None, **kwargs):
        if message.startswith("slow"):
            time.sleep(0.05)
            return FakeResponse("The answer is 2")

        if message.startswith("fast"):
            return FakeResponse("The answer is 999")

        return FakeResponse("seeded prompt")


class EliteTrackingModel:
    def __init__(self):
        self.num_workers = 1

    def chat(self, message=None, **kwargs):
        if message.startswith("fast-wrong"):
            return FakeResponse("The answer is 999")

        if message.startswith("slow-correct"):
            time.sleep(0.05)
            return FakeResponse("The answer is 2")

        return FakeResponse("seeded prompt")


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

    def test_evaluate_fitness_keeps_results_aligned_with_unit_order(self):
        original_examples = pb_module.gsm8k_examples
        pb_module.gsm8k_examples = [{"question": "What is 1 + 1?", "answer": "#### 2"}]

        try:
            population = create_population(["style"], ["mutator-a", "mutator-b"], "Solve the problem.")
            population.units[0].P = "slow"
            population.units[1].P = "fast"

            pb_module._evaluate_fitness(population, DelayedFitnessModel(), 1)

            self.assertEqual(population.units[0].fitness, 1.0)
            self.assertEqual(population.units[1].fitness, 0.0)
        finally:
            pb_module.gsm8k_examples = original_examples

    def test_evaluate_fitness_tracks_the_highest_fitness_elite(self):
        original_examples = pb_module.gsm8k_examples
        pb_module.gsm8k_examples = [{"question": "What is 1 + 1?", "answer": "#### 2"}]

        try:
            population = create_population(["style"], ["mutator-a", "mutator-b"], "Solve the problem.")
            population.units[0].P = "fast-wrong"
            population.units[1].P = "slow-correct"

            pb_module._evaluate_fitness(population, EliteTrackingModel(), 1)

            self.assertEqual(population.units[0].fitness, 0.0)
            self.assertEqual(population.units[1].fitness, 1.0)
            self.assertEqual(population.elites[-1].P, "slow-correct")
        finally:
            pb_module.gsm8k_examples = original_examples
