import unittest

from _.language.regex_gen.exploder import CharacterRange, CharacterSet, Repeat

class CharacterTests(unittest.TestCase):
  def test_range_regex(self):
    self.assertEqual(CharacterRange("a", "z").regex(), "[a-z]")

  def test_set(self):
    def regex(cs):
      r = cs.regex()
      self.assertTrue(r.startswith("["))
      self.assertTrue(r.endswith("]"))
      return r[1:-1]

    self.assertEqual(set(regex(CharacterSet("abcdefg"))), set("abcdefg"))
    self.assertEqual(set(regex(CharacterSet("^-abcdefg"))), set("abcdefg^-"))

    self.assertTrue(regex(CharacterSet("abcdefg", negated=True)).startswith("^"))

    self.assertFalse(regex(CharacterSet("^-abcdefg")).startswith("^"))
    self.assertTrue(regex(CharacterSet("^-abcdefg")).endswith("-^"))


class RepeatTests(unittest.TestCase):
  def test_constructor(self):
    self.assertEqual(Repeat.any(), Repeat(0, None))
    self.assertEqual(Repeat.more(), Repeat(1, None))
    self.assertEqual(Repeat.upto(3), Repeat(0, 3))
    self.assertEqual(Repeat.atleast(3), Repeat(3, None))
    self.assertEqual(Repeat.between(3, 7), Repeat(3, 7))

  def test_regex(self):
    self.assertEqual(Repeat.any().regex(), "*")
    self.assertEqual(Repeat.more().regex(), "+")
    self.assertEqual(Repeat.upto(3).regex(), "{0,3}")
    self.assertEqual(Repeat.atleast(3).regex(), "{3,}")
    self.assertEqual(Repeat.between(3, 7).regex(), "{3,7}")
    self.assertEqual(Repeat.between(3, 3).regex(), "{3}")

