import unittest

from sim.parser import NetlistParseError, parse_netlist_text


class ParserTests(unittest.TestCase):
    def test_parse_basic_elements_and_directives(self):
        text = """
# simple network
R1 in out 1000
C1 out 0 1e-6
I1 in 0 DC 1e-3
V1 in 0 STEP 0 1 1e-3
.probe in out
.ic out 0.1
"""
        c = parse_netlist_text(text)
        self.assertEqual(len(c.resistors), 1)
        self.assertEqual(len(c.capacitors), 1)
        self.assertEqual(len(c.current_sources), 1)
        self.assertEqual(len(c.voltage_sources), 1)
        self.assertIn("out", c.probes)
        self.assertAlmostEqual(c.initial_conditions["out"], 0.1)

    def test_duplicate_names_raise(self):
        text = """
R1 a b 1
R1 b 0 2
"""
        with self.assertRaises(NetlistParseError):
            parse_netlist_text(text)

    def test_invalid_resistor_value_raises(self):
        text = "R1 a b -10"
        with self.assertRaises(NetlistParseError):
            parse_netlist_text(text)


if __name__ == "__main__":
    unittest.main()
