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
        self.assertAlmostEqual(hypergeometric_pmf(7, 5, [3], [2]), 0.5714285714285714, places=16, msg="Pärchen in 5 Handkarten")
        self.assertAlmostEqual(hypergeometric_pmf(20, 5, (8, 5), (2, 1)), 0.18962848297213622, places=16, msg="aus 20 Kugeln 2 rote und 1 grüne ziehen")

        self.assertAlmostEqual(probability_of_sample(7, 5, (2, 2, 2), [(2, 1, None), (2, None, 2)]), 0.3333333333333333, places=16, msg="aus 7 Kugeln (2 rote und 1 grüne) oder (2 rote und 2 blaue) ziehen")
        #self.assertAlmostEqual(hypergeometric_pmf_ext(20, 5, (8, 5, 3), [(2, 1, None), (2, None, 2)]), 0.21130030959752322, places=16, msg="aus 20 Kugeln (2 rote und 1 grüne) oder (2 rote und 2 blaue) ziehen")

        self.assertAlmostEqual(hypergeometric_pmf(49, 6, (6, ), (6, )), 0.000000071511, places=12, msg="6/49, 6 Richtig")
        self.assertAlmostEqual(hypergeometric_pmf(49, 6, (6, ), (3, )), 0.017650, places=6, msg="6/49, 3 Richtig")
        self.assertAlmostEqual(hypergeometric_pmf(7, 5, [2,2], [3,1]), 0.0, msg="k_features[0] > n_features[0]")
        with self.assertRaises(AssertionError, msg="k > n"):
            hypergeometric_pmf(7, 8, (3,), (2,))
        with self.assertRaises(AssertionError, msg="n < sum(n_features)"):
            hypergeometric_pmf(7, 5, (8,), (2,))

    def test_hypergeometric_cdf(self):
        self.assertAlmostEqual(hypergeometric_cdf(7, 5, [3], [2]), 0.7142857142857142, places=16, msg="Pärchen in 5 Handkarten")
        self.assertAlmostEqual(hypergeometric_cdf(20, 5, (8, 5), (2, 1)), 0.3738390092879257, places=16, msg="aus 20 Kugeln 2 rote und 1 grüne ziehen")
        #self.assertAlmostEqual(hypergeometric_cdf_ext(20, 5, (8, 5, 3), [(2, 1, None), (2, None, 2)]), 0.23796222217296562, places=16, msg="aus 20 Kugeln (2 rote und 1 grüne) oder (2 rote und 2 blaue) ziehen")
        self.assertAlmostEqual(hypergeometric_cdf(7, 5, [2, 2], [3, 1]), 0.5238095238095237, places=16, msg="k_features[0] > n_features[0]")
        with self.assertRaises(AssertionError, msg="k > n"):
            hypergeometric_cdf(7, 8, (3,), (2,))
        with self.assertRaises(AssertionError, msg="n < sum(n_features)"):
            hypergeometric_cdf(7, 5, (8,), (2,))

    def test_hypergeometric_ucdf(self):
        self.assertAlmostEqual(hypergeometric_ucdf(7, 5, [3], [2]), 0.8571428571428571, places=16, msg="Pärchen in 5 Handkarten")
        self.assertAlmostEqual(hypergeometric_ucdf(20, 5, (8, 5), (2, 1)), 0.5192208462332302, places=16, msg="aus 20 Kugeln 2 rote und 1 grüne ziehen")
        #self.assertAlmostEqual(hypergeometric_ucdf_ext(20, 5, (8, 5, 3), [(2, 1, None), (2, None, 2)]), 0.367014378126461, places=16, msg="aus 20 Kugeln (2 rote und 1 grüne) oder (2 rote und 2 blaue) ziehen")
        self.assertAlmostEqual(hypergeometric_ucdf(7, 5, [2, 2], [3, 1]), 0.0, msg="k_features[0] > n_features[0]")
        with self.assertRaises(AssertionError, msg="k > n"):
            hypergeometric_ucdf(7, 8, (3,), (2,))
        with self.assertRaises(AssertionError, msg="n < sum(n_features)"):
            hypergeometric_ucdf(7, 5, (8,), (2,))

    # def test_calculate_union_probability(self):
    #     probabilities = [0.3, 0.4, 0.2]
    #     expected_union = 0.7
    #     result = calculate_union_probability(probabilities)
    #     self.assertAlmostEqual(result, expected_union, places=3, msg="3 Ereignisse")
    #
    #     probabilities = [0.3, 0.4, 0.2, 0.1]
    #     expected_union = 0.784
    #     result = calculate_union_probability(probabilities)
    #     self.assertAlmostEqual(result, expected_union, places=3, msg="4 Ereignisse")
    #
    #     probabilities = [0.3, 0.4, 0.2, 0.1, 0.15]
    #     expected_union = 0.819
    #     result = calculate_union_probability(probabilities)
    #     self.assertAlmostEqual(result, expected_union, places=3, msg="5 Ereignisse")

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
        self.assertAlmostEqual(sum(matches) / len(samples), 0.5714285714285714, places=16)
        # k_features[0] > n_features[0]
        matches, samples = hypergeometric_pmf_samples(["g1", "g2", "g3", "r1", "r2", "r3", "r4"], 5, {"g": 4, "r": 2})
        self.assertEqual(21, len(samples))
        self.assertEqual(0, sum(matches))

        # aus 7 Kugeln (2 rote und 1 grüne) oder (2 rote und 2 blaue) ziehen
        matches, samples = hypergeometric_pmf_samples(["r1", "r2", "g1", "g2", "b1", "b2", "s1"], 5, [{"r": 2, "g": 1},{"r": 2, "b": 2}])
        for s in zip(samples, matches):
            print(s)
        self.assertEqual(21, len(samples))
        self.assertEqual(7, sum(matches))
        self.assertAlmostEqual(sum(matches) / len(samples), 0.3333333333333333, places=16)

        # aus 20 Kugeln (2 rote und 1 grüne) oder (2 rote und 2 blaue) ziehen
        matches, samples = hypergeometric_pmf_samples([ "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8",
            "g1", "g2", "g3", "g4", "g5", "b1", "b2", "b3", "s1", "s2", "s3", "s4"], 5, [{"r": 2, "g": 1},{"r": 2, "b": 2}])
        self.assertEqual(15504, len(samples))
        self.assertEqual(3276, sum(matches))
        self.assertAlmostEqual(sum(matches) / len(samples), 0.21130030959752322, places=16)

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
        self.assertAlmostEqual(sum(matches) / len(samples), 0.7142857142857143, places=16)
        # k_features[0] > n_features[0]
        matches, samples = hypergeometric_cdf_samples(["g1", "g2", "g3", "r1", "r2", "r3", "r4"], 5, {"g": 4, "r": 2})
        self.assertEqual(21, len(samples))
        self.assertEqual(6, sum(matches))

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
        self.assertAlmostEqual(sum(matches) / len(samples), 0.8571428571428571, places=16)
        # k_features[0] > n_features[0]
        matches, samples = hypergeometric_ucdf_samples(["g1", "g2", "g3", "r1", "r2", "r3", "r4"], 5, {"g": 4, "r": 2})
        self.assertEqual(21, len(samples))
        self.assertEqual(0, sum(matches))

    def test_boundary_conditions_pmf(self):
        # Randbedingungen
        g = ["g1", "g2", "g3"]
        r = ["r1", "r2", "r3"]
        for n in range(3):
            for k in range(3):
                for nf in range(3):
                    for kf in range(3):
                        try:
                            hy1 = hypergeometric_pmf(n, k, [nf], [kf])
                        except AssertionError as _e:
                            hy1 = ""
                        if k <= n and nf <= n:
                            elements = g[:nf] + r[:n - nf]
                            matches, samples = hypergeometric_pmf_samples(elements, k, {"g": kf})
                            hy2 = sum(matches) / len(samples)
                        else:
                            hy2 = ""
                        self.assertEqual(hy2, hy1)

    def test_boundary_conditions_cdf(self):
        # Randbedingungen
        g = ["g1", "g2", "g3"]
        r = ["r1", "r2", "r3"]
        for n in range(3):
            for k in range(3):
                for nf in range(3):
                    for kf in range(3):
                        try:
                            hy1 = hypergeometric_cdf(n, k, [nf], [kf])
                        except AssertionError as _e:
                            hy1 = ""
                        if k <= n and nf <= n:
                            elements = g[:nf] + r[:n - nf]
                            matches, samples = hypergeometric_cdf_samples(elements, k, {"g": kf})
                            hy2 = sum(matches) / len(samples)
                        else:
                            hy2 = ""
                        self.assertEqual(hy2, hy1)

    def test_boundary_conditions_ucdf(self):
        # Randbedingungen
        g = ["g1", "g2", "g3"]
        r = ["r1", "r2", "r3"]
        for n in range(3):
            for k in range(3):
                for nf in range(3):
                    for kf in range(3):
                        try:
                            hy1 = hypergeometric_ucdf(n, k, [nf], [kf])
                        except AssertionError as _e:
                            hy1 = ""
                        if k <= n and nf <= n:
                            elements = g[:nf] + r[:n - nf]
                            matches, samples = hypergeometric_ucdf_samples(elements, k, {"g": kf})
                            hy2 = sum(matches) / len(samples)
                        else:
                            hy2 = ""
                        self.assertEqual(hy2, hy1)


if __name__ == '__main__':
    unittest.main()
