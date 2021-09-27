import unittest

from _.language.regex_gen.exploder import CharacterRange, CharacterSet, Repeat, Value, Sum, Product
from _.language.regex_gen.exploder import FLAG_max_repeat

class ValueTests(unittest.TestCase):
  def test_choices(self):
    v = Value("abc")
    self.assertEqual(v.choices(), 1)

  def test_iter(self):
    v = Value("abc")
    self.assertEqual(v.choices(), 1)
    self.assertEqual(v[0], "abc")
    self.assertEqual(list(v), ["abc"])


class CharacterTests(unittest.TestCase):
  def test_outoforder_range(self):
    with self.assertRaises(ValueError):
      CharacterRange("z", "a")

  def test_iter_range(self):
    self.assertEqual(set(CharacterRange("a", "d")), set(["a", "b", "c", "d"]))

  def test_range_regex(self):
    self.assertEqual(CharacterRange("a", "z").regex(), "[a-z]")

  def test_iter_set(self):
    self.assertEqual(set(CharacterSet("abcdefg")), set("abcdefg"))

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

  def test_choices(self):
    self.assertEqual(FLAG_max_repeat.value, 5, "Test prereq failed, flag (--max-repeat) value changed.")
    value = 100

    r = Value("a") * Repeat.atleast(value)
    self.assertEqual(r.choices(), 1)

    r = Value("a") * Repeat.any()
    self.assertEqual(r.choices(), 6) # 5 + 1

  def test_iter(self):
    r = Value("a") * Repeat(3, 5)
    self.assertEqual(r.choices(), 3)
    self.assertEqual(list(r), ["aaa", "aaaa", "aaaaa"])


class CombinedTests(unittest.TestCase):
  def test_iter(self):
    v = Value("a")
    p = Product(v, v, v, v)
    self.assertEqual(p.choices(), 1)
    self.assertEqual(set(p), set(["aaaa"]))

    s = Sum(v, v, v)
    self.assertEqual(s.choices(), 3)
    self.assertEqual(set(s), set(["a", "a", "a"]))

    r = (Value("a") | Value("b")) + Value("c")
    self.assertEqual(r.choices(), 2)
    self.assertEqual(set(r), set(["ac", "bc"]))

    r = (Value("a") + Value("b")) | Value("c")
    self.assertEqual(r.choices(), 2)
    self.assertEqual(set(r), set(["ab", "c"]))


