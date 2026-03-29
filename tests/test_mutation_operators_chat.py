import unittest

import pb.mutation_operators as mutation_ops
from pb.types import EvolutionUnit


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeChatModel:
    def chat(self, message=None, **kwargs):
        if "An ordered list of 100 hints" in message:
            return FakeResponse("1. First hint 2. Second hint")

        if message.startswith("GENOTYPES FOUND IN ASCENDING ORDER OF QUALITY"):
            return FakeResponse("Lineage prompt")

        if message.startswith("Please summarize and improve the following instruction: "):
            return FakeResponse("Improved mutation")

        if message.startswith("I gave a friend an instruction and some advice."):
            return FakeResponse("Recovered instruction")

        if message.startswith("Solve the problem. "):
            return FakeResponse("Fresh mutation")

        return FakeResponse(f"rewritten:{message}")


class MutationOperatorsChatTests(unittest.TestCase):
    def make_unit(self):
        return EvolutionUnit(
            T="Think step by step.",
            M="Rewrite clearly.",
            P="Old prompt",
            fitness=0,
            history=[],
        )

    def test_mutators_use_chat_compatible_model(self):
        model = FakeChatModel()
        original_examples = mutation_ops.gsm8k_examples
        mutation_ops.gsm8k_examples = [{"question": "What is 1 + 1?", "answer": "#### 2"}]

        try:
            unit = self.make_unit()
            mutation_ops.zero_order_prompt_gen(unit, "Solve the problem.", model)
            self.assertEqual(unit.P, "First hint")

            unit = self.make_unit()
            mutation_ops.first_order_prompt_gen(unit, model)
            self.assertEqual(unit.P, "rewritten:Rewrite clearly. Old prompt")

            unit = self.make_unit()
            mutation_ops.lineage_based_mutation(unit, [self.make_unit()], model)
            self.assertEqual(unit.P, "Lineage prompt")

            unit = self.make_unit()
            mutation_ops.zero_order_hypermutation(unit, "Solve the problem.", model)
            self.assertEqual(unit.M, "Fresh mutation")

            unit = self.make_unit()
            mutation_ops.first_order_hypermutation(unit, model)
            self.assertEqual(unit.M, "Improved mutation")
            self.assertEqual(unit.P, "rewritten:Improved mutation Old prompt")

            unit = self.make_unit()
            mutation_ops.working_out_task_prompt(unit, model)
            self.assertEqual(unit.P, "Recovered instruction")
        finally:
            mutation_ops.gsm8k_examples = original_examples
