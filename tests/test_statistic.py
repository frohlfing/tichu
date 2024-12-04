import unittest
from src.common.statistic import *


class TestHypergeometricFunctions(unittest.TestCase):

    def test_binomial_coefficient(self):
        self.assertEqual(binomial_coefficient(3, 2), 3)
        self.assertEqual(binomial_coefficient(5, 2), 10)
        self.assertEqual(binomial_coefficient(10, 10), 1)
        self.assertEqual(binomial_coefficient(10, 0), 1, "Randbedingung k == 0")
        self.assertEqual(binomial_coefficient(0, 0), 1, "Randbedingung k == 0")
        self.assertEqual(binomial_coefficient(3, 10), 0, "Randbedingung k > n")
        self.assertEqual(binomial_coefficient(0, 10), 0, "Randbedingung k > n")
        self.assertEqual(binomial_coefficient(49, 6), 13983816, "6/49, 6 Richtige")

    def test_possible_samples(self):
        elements = ['A', 'B', 'C']
        self.assertEqual(possible_samples(elements, 2), [('A', 'B'), ('A', 'C'), ('B', 'C')])
        self.assertEqual(possible_samples(elements, 1), [('A',), ('B',), ('C',)])
        self.assertEqual(possible_samples(elements, 3), [('A', 'B', 'C')])
        self.assertEqual(possible_samples(elements, 0), [()], "Randbedingung k == 0")
        self.assertEqual(possible_samples([], 0), [()],"Randbedingung k == 0")
        self.assertEqual(possible_samples(elements, 10), [], "Randbedingung k > n")
        self.assertEqual(possible_samples([], 10), [], "Randbedingung k > n")

    def test_hypergeometric_pmf(self):
        self.assertAlmostEqual(hypergeometric_pmf(7, 5, [3], [2]), 0.5714285714285714, msg="Pärchen in 5 Handkarten")
        self.assertAlmostEqual(hypergeometric_pmf(20, 5, (8, 5), (2, 1)), 0.18962848297213622, msg="8 rote und 5 grüne Kugeln")
        self.assertAlmostEqual(hypergeometric_pmf(49, 6, (6, ), (6, )), 0.000000071511, places=12, msg="6/49, 6 Richtig")
        self.assertAlmostEqual(hypergeometric_pmf(49, 6, (6, ), (3, )), 0.017650, places=6, msg="6/49, 3 Richtig")
        self.assertAlmostEqual(hypergeometric_pmf(7, 7, [3], [2]), 0.0, msg="k == n")
        self.assertAlmostEqual(hypergeometric_pmf(7, 8, (3,), (2,)), 0.0, msg="k > n")
        self.assertAlmostEqual(hypergeometric_pmf(7, 0, [3], []), 1.0, msg="k == 0 und sum(k_features) == 0")
        self.assertAlmostEqual(hypergeometric_pmf(0, 0, [], []), 1.0, msg="k == 0 und n== 0 und sum(k_features) == 0")
        self.assertAlmostEqual(hypergeometric_pmf(3, 2, [3,], [2]), 1.0, msg="k == sum(k_features)")
        self.assertAlmostEqual(hypergeometric_pmf(7, 1, (3,), (2,)), 0.0, msg="k < sum(k_features)")
        self.assertAlmostEqual(hypergeometric_pmf(7, 5, [7], [2]), 0.0, msg="n == sum(n_features)")
        with self.assertRaises(AssertionError, msg="n < sum(n_features)"):
            hypergeometric_pmf(7, 5, (8,), (2,))

    def test_hypergeometric_cdf(self):
        self.assertAlmostEqual(hypergeometric_cdf(7, 5, [3], [2]), 0.7142857142857143, msg="Pärchen in 5 Handkarten")
        self.assertAlmostEqual(hypergeometric_cdf(20, 5, (8, 5), (2, 1)), 0.3738390092879257, msg="8 rote und 5 grüne Kugeln")
        self.assertAlmostEqual(hypergeometric_cdf(7, 7, [3], [2]), 0.0, msg="k == n")
        self.assertAlmostEqual(hypergeometric_cdf(7, 8, (3,), (2,)), 0.0, msg="k > n")
        self.assertAlmostEqual(hypergeometric_cdf(7, 0, [3], []), 1.0, msg="k == 0")
        self.assertAlmostEqual(hypergeometric_cdf(0, 0, [], []), 1.0, msg="k == 0 und n== 0")
        self.assertAlmostEqual(hypergeometric_cdf(3, 2, [3,], [2]), 1.0, msg="k == sum(k_max_features)")
        self.assertAlmostEqual(hypergeometric_cdf(7, 1, [3], [2]), 1.0, msg="k < sum(k_max_features)")
        self.assertAlmostEqual(hypergeometric_cdf(7, 5, [7], [2]), 0.0, msg="n == sum(k_max_features)")
        with self.assertRaises(AssertionError, msg="n < sum(n_features)"):
            hypergeometric_cdf(7, 5, (8,), (2,))

    def test_hypergeometric_ucdf(self):
        self.assertAlmostEqual(hypergeometric_ucdf(7, 5, [3], [2]), 0.8571428571428571, msg="Pärchen in 5 Handkarten")
        self.assertAlmostEqual(hypergeometric_ucdf(20, 5, (8, 5), (2, 1)), 0.5192208462332302, msg="8 rote und 5 grüne Kugeln")
        self.assertAlmostEqual(hypergeometric_ucdf(7, 7, [3], [2]), 1.0, msg="k == n")
        self.assertAlmostEqual(hypergeometric_ucdf(7, 8, (3,), (2,)), 0.0, msg="k > n")
        self.assertAlmostEqual(hypergeometric_ucdf(7, 0, [3], []), 1.0, msg="k == 0")
        self.assertAlmostEqual(hypergeometric_ucdf(0, 0, [], []), 1.0, msg="k == 0 und n== 0")
        self.assertAlmostEqual(hypergeometric_ucdf(3, 2, [3,], [2]), 1.0, msg="k == sum(k_min_features)")
        self.assertAlmostEqual(hypergeometric_ucdf(7, 1, [3], [2]), 0.0, msg="k < sum(k_min_features)")
        self.assertAlmostEqual(hypergeometric_ucdf(7, 5, [7], [2]), 1.0, msg="n == sum(n_features)")
        with self.assertRaises(AssertionError, msg="n < sum(n_features)"):
            hypergeometric_ucdf(7, 5, (8,), (2,))

    def test_hypergeometric_pmf_samples(self):
        # Pärchen in 5 Handkarten
        matches, samples = hypergeometric_pmf_samples(["g1", "g2", "g3", "r1", "r2", "r3", "r4"], 5, {"g": 2})
        self.assertEqual(21, len(samples))
        self.assertEqual(12, sum(matches))
        self.assertEqual([
            (False, ('g1', 'g2', 'g3', 'r1', 'r2')),
            (False, ('g1', 'g2', 'g3', 'r1', 'r3')),
            (False, ('g1', 'g2', 'g3', 'r1', 'r4')),
            (False, ('g1', 'g2', 'g3', 'r2', 'r3')),
            (False, ('g1', 'g2', 'g3', 'r2', 'r4')),
            (False, ('g1', 'g2', 'g3', 'r3', 'r4')),
            (True,  ('g1', 'g2', 'r1', 'r2', 'r3')),
            (True,  ('g1', 'g2', 'r1', 'r2', 'r4')),
            (True,  ('g1', 'g2', 'r1', 'r3', 'r4')),
            (True,  ('g1', 'g2', 'r2', 'r3', 'r4')),
            (True,  ('g1', 'g3', 'r1', 'r2', 'r3')),
            (True,  ('g1', 'g3', 'r1', 'r2', 'r4')),
            (True,  ('g1', 'g3', 'r1', 'r3', 'r4')),
            (True,  ('g1', 'g3', 'r2', 'r3', 'r4')),
            (False, ('g1', 'r1', 'r2', 'r3', 'r4')),
            (True,  ('g2', 'g3', 'r1', 'r2', 'r3')),
            (True,  ('g2', 'g3', 'r1', 'r2', 'r4')),
            (True,  ('g2', 'g3', 'r1', 'r3', 'r4')),
            (True,  ('g2', 'g3', 'r2', 'r3', 'r4')),
            (False, ('g2', 'r1', 'r2', 'r3', 'r4')),
            (False, ('g3', 'r1', 'r2', 'r3', 'r4'))], list(zip(matches, samples)))
        self.assertAlmostEqual(sum(matches) / len(samples), 0.5714285714285714)
        # todo Randbedingungen
        # 1.0, wenn k == 0 und sum(k_features) == 0
        # 0.0, wenn k > n oder sum(k_features) > k

    def test_hypergeometric_cdf_samples(self):
        # Pärchen in 5 Handkarten
        matches, samples = hypergeometric_cdf_samples(["g1", "g2", "g3", "r1", "r2", "r3", "r4"], 5, {"g": 2})
        self.assertEqual(21, len(samples))
        self.assertEqual(15, sum(matches))
        self.assertEqual([
            (False, ('g1', 'g2', 'g3', 'r1', 'r2')),
            (False, ('g1', 'g2', 'g3', 'r1', 'r3')),
            (False, ('g1', 'g2', 'g3', 'r1', 'r4')),
            (False, ('g1', 'g2', 'g3', 'r2', 'r3')),
            (False, ('g1', 'g2', 'g3', 'r2', 'r4')),
            (False, ('g1', 'g2', 'g3', 'r3', 'r4')),
            (True, ('g1', 'g2', 'r1', 'r2', 'r3')),
            (True, ('g1', 'g2', 'r1', 'r2', 'r4')),
            (True, ('g1', 'g2', 'r1', 'r3', 'r4')),
            (True, ('g1', 'g2', 'r2', 'r3', 'r4')),
            (True, ('g1', 'g3', 'r1', 'r2', 'r3')),
            (True, ('g1', 'g3', 'r1', 'r2', 'r4')),
            (True, ('g1', 'g3', 'r1', 'r3', 'r4')),
            (True, ('g1', 'g3', 'r2', 'r3', 'r4')),
            (True, ('g1', 'r1', 'r2', 'r3', 'r4')),
            (True, ('g2', 'g3', 'r1', 'r2', 'r3')),
            (True, ('g2', 'g3', 'r1', 'r2', 'r4')),
            (True, ('g2', 'g3', 'r1', 'r3', 'r4')),
            (True, ('g2', 'g3', 'r2', 'r3', 'r4')),
            (True, ('g2', 'r1', 'r2', 'r3', 'r4')),
            (True, ('g3', 'r1', 'r2', 'r3', 'r4'))], list(zip(matches, samples)))
        self.assertAlmostEqual(sum(matches) / len(samples), 0.7142857142857142)
        # todo Randbedingungen
        # 1.0, wenn k == 0
        # 0.0, wenn k > n

    def test_hypergeometric_ucdf_samples(self):
        # Pärchen in 5 Handkarten
        matches, samples = hypergeometric_ucdf_samples(["g1", "g2", "g3", "r1", "r2", "r3", "r4"], 5, {"g": 2})
        self.assertEqual(21, len(samples))
        self.assertEqual(18, sum(matches))
        self.assertEqual([
            (True, ('g1', 'g2', 'g3', 'r1', 'r2')),
            (True, ('g1', 'g2', 'g3', 'r1', 'r3')),
            (True, ('g1', 'g2', 'g3', 'r1', 'r4')),
            (True, ('g1', 'g2', 'g3', 'r2', 'r3')),
            (True, ('g1', 'g2', 'g3', 'r2', 'r4')),
            (True, ('g1', 'g2', 'g3', 'r3', 'r4')),
            (True, ('g1', 'g2', 'r1', 'r2', 'r3')),
            (True, ('g1', 'g2', 'r1', 'r2', 'r4')),
            (True, ('g1', 'g2', 'r1', 'r3', 'r4')),
            (True, ('g1', 'g2', 'r2', 'r3', 'r4')),
            (True, ('g1', 'g3', 'r1', 'r2', 'r3')),
            (True, ('g1', 'g3', 'r1', 'r2', 'r4')),
            (True, ('g1', 'g3', 'r1', 'r3', 'r4')),
            (True, ('g1', 'g3', 'r2', 'r3', 'r4')),
            (False, ('g1', 'r1', 'r2', 'r3', 'r4')),
            (True, ('g2', 'g3', 'r1', 'r2', 'r3')),
            (True, ('g2', 'g3', 'r1', 'r2', 'r4')),
            (True, ('g2', 'g3', 'r1', 'r3', 'r4')),
            (True, ('g2', 'g3', 'r2', 'r3', 'r4')),
            (False, ('g2', 'r1', 'r2', 'r3', 'r4')),
            (False, ('g3', 'r1', 'r2', 'r3', 'r4'))], list(zip(matches, samples)))
        self.assertAlmostEqual(sum(matches) / len(samples), 0.8571428571428571)
        # todo Randbedingungen
        # 1.0, wenn k == 0 und sum(k_min_features) == 0
        # 0.0, wenn k > n oder sum(k_min_features) > k


if __name__ == '__main__':
    unittest.main()
