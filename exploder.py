from dataclasses import dataclass

class RegexType:
  def regex(self) -> str:
    "To construct a regex"
    # Needs to be implmented
    raise Exception(NotImplemented)

  def __add__(self, other):
    if isinstance(other, str):
      other = Value(other)
    return Product(self, other)

  def __mul__(self, other):
    if isinstance(other, int):
      other = Repeat(other, other)

    if not isinstance(other, Repeat):
      return NotImplemented

    return Repeated(self, other)

  def __or__(self, other):
    if isinstance(other, str):
      other = Value(other)
    return Sum(self, other)


class Value(RegexType, str):
  def __mul__(self, other):
    if isinstance(other, int):
      return Value(str(self) * other)
    return super().__mul__(other)

  def __add__(self, other):
    if isinstance(other, (str, Value)):
      return Value(str(self) + str(other))
    return super().__add__(other)

  def regex(self):
    return "(" + str(self) + ")"


class CharacterRange(RegexType):
  def __init__(self, start, end):
    self.start = start
    self.end = end

  def regex(self):
    return "[" + self.start + "-" + self.end + "]"


class CharacterSet(RegexType):
  # Special meta characters to move to the end
  __to_remove = list("-^")

  # For both value and character sets.
  def __init__(self, values, negated=False):
    values = set(values)
    bad = [c for c in CharacterSet.__to_remove if c in values]
    values.difference_update(set(bad))

    self.values = ''.join(values) + ''.join(bad)
    self.negated = negated

  def regex(self):
    n = ''
    if self.negated:
      n = '^'
    return '[' + n + self.values + ']'


class Product(RegexType):
  def __init__(self, *values):
    self.values = values

  def regex(self):
    parts = [p.regex() for p in self.values]
    return "(" + "".join(parts) + ")"

  def __add__(self, other):
    if isinstance(other, str):
      other = Value(other)
    if isinstance(other, Product):
      return Product(*self.values, *other.values)
    return Product(*self.values, other)


class Sum(RegexType):
  def __init__(self, *values):
    self.values = values

  def regex(self):
    parts = [p.regex() for p in self.values]
    return "(" + "|".join(parts) + ")"

  def __or__(self, other):
    if isinstance(other, str):
      other = Value(other)
    if isinstance(other, Sum):
      return Sum(*self.values, *other.values)
    return Sum(*self.values, other)


@dataclass
class Repeat:
  min: int
  max: int

  @staticmethod
  def any():
    "Zero or more"
    return Repeat(0, None)

  @staticmethod
  def more():
    "One or more"
    return Repeat(1, None)

  @staticmethod
  def upto(x):
    "zero to x matches"
    return Repeat(0, x)

  @staticmethod
  def atleast(x):
    "x or more matches"
    return Repeat(x, None)

  @staticmethod
  def between(x, y):
    return Repeat(x, y)

  def regex(self):
    if self.max:
      if self.max == self.min:
        return "{" + str(self.min) + "}"
      return "{" + str(self.min) + "," + str(self.max) + "}"
    elif self.min > 1:
      return "{" + str(self.min) + ",}"
    elif self.min == 1:
      return "+"
    else:
      return "*"


class Repeated(RegexType):
  def __init__(self, value: RegexType, repeat: Repeat):
    self.value = value
    self.repeat = repeat

  def regex(self):
    return self.value.regex() + self.repeat.regex()


