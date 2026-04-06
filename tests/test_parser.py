import unittest

from sim.model import SourceSpec
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

    def test_pwl_voltage_source_parse(self):
        text = """
R1 in out 1000
V1 in 0 PWL 0 0 1e-3 1 2e-3 1
"""
        c = parse_netlist_text(text)
        self.assertEqual(len(c.voltage_sources), 1)
        spec = c.voltage_sources[0].spec
        self.assertEqual(spec.kind, "PWL")
        self.assertEqual(spec.params, (0.0, 0.0, 1e-3, 1.0, 2e-3, 1.0))

    def test_pwl_time_order_raises(self):
        text = "V1 a 0 PWL 0 0 2 1 1 0"
        with self.assertRaises(NetlistParseError):
            parse_netlist_text(text)

    def test_pwl_value_at_ramp_jump_and_hold(self):
        spec = SourceSpec(kind="PWL", params=(0.0, 0.0, 1.0, 1.0, 1.0, 2.0, 3.0, 2.0))
        self.assertAlmostEqual(spec.value_at(-1.0), 0.0)
        self.assertAlmostEqual(spec.value_at(0.0), 0.0)
        self.assertAlmostEqual(spec.value_at(0.5), 0.5)
        self.assertAlmostEqual(spec.value_at(1.0), 2.0)
        self.assertAlmostEqual(spec.value_at(2.0), 2.0)
        self.assertAlmostEqual(spec.value_at(10.0), 2.0)


if __name__ == "__main__":
    unittest.main()
