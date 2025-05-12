import unittest

from src.common.rand import Random


class TestRandom(unittest.TestCase):
    def setUp(self):
        self.random = Random(seed=123)

    def test_integer(self):
        result = self.random.integer(1, 10)
        self.assertTrue(1 <= result < 10)

    def test_boolean(self):
        result = self.random.boolean()
        self.assertIn(result, [True, False])

    def test_choice(self):
        seq = [1, 2, 3, 4, 5]
        result = self.random.choice(seq)
        self.assertIn(result, seq)

    def test_choice_with_weights(self):
        seq = [1, 2, 3, 4, 5]
        weights = [1, 1, 1, 1, 5]
        result = self.random.choice(seq, weights)
        self.assertIn(result, seq)

    def test_sample(self):
        seq = [1, 2, 3, 4, 5]
        result = self.random.sample(seq, 3)
        self.assertEqual(len(result), 3)
        for item in result:
            self.assertIn(item, seq)

    def test_shuffle(self):
        seq = [1, 2, 3, 4, 5]
        original_seq = seq.copy()
        self.random.shuffle(seq)
        self.assertNotEqual(seq, original_seq)
        self.assertCountEqual(seq, original_seq)


if __name__ == '__main__':
    unittest.main()