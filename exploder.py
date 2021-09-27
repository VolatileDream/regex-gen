from dataclasses import dataclass
from functools import reduce
from itertools import accumulate

from _.command_line.flags import Flag

FLAG_max_repeat = Flag.int('max-repeat', default=5,
                           description="For infinitely repeating regex values (*, +) caps the number of repeats.")


class RegexType:
  def regex(self) -> str:
    "To construct a regex"
    # Needs to be implmented by subclass
    raise Exception(NotImplemented)

  def __iter__(self):
    return RegexIter(self)

  def _range_check(self, index):
    if index >= self.choices():
      raise IndexError("Index out of bounds for {}: {}".format(type(self), index))

  def choices(self):
    """Number of possible outputs for this regex type."""
    # Needs to be implmented by subclass
    raise Exception(NotImplemented)

  def __getitem__(self, index):
    """Used for iteration and random values."""
    # Needs to be implmented by subclass
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


class RegexIter:
  def __init__(self, regex):
    self.__regex = regex
    self.__index = 0

  def __next__(self):
    i = self.__index
    self.__index += 1
    try:
      return self.__regex[i]
    except IndexError:
      raise StopIteration


class Value(RegexType, str):
  def __mul__(self, other):
    if isinstance(other, int):
      return Value(str(self) * other)
    return super().__mul__(other)

  def __add__(self, other):
    if isinstance(other, (str, Value)):
      return Value(str(self) + str(other))
    return super().__add__(other)

  def choices(self):
    return 1

  def __getitem__(self, index):
    super()._range_check(index)
    return str(self)

  def regex(self):
    return "(" + str(self) + ")"


class CharacterRange(RegexType):
  def __init__(self, start, end):
    if ord(start) > ord(end):
      raise ValueError(
          "start of range must be smaller than the end of range: {} ({}) > {} ({})".format(
              start, ord(start), end, ord(end)))
    self.start = ord(start)
    self.end = ord(end)

  def choices(self):
    # inclusive range
    return self.end - self.start + 1

  def __getitem__(self, index):
    super()._range_check(index)
    return chr(self.start + index)

  def regex(self):
    return "[" + chr(self.start) + "-" + chr(self.end) + "]"


# TODO: Remove negation support.
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

  def choices(self):
    if self.negated:
      raise Exception(NotImplemented)
    return len(self.values)

  def __getitem__(self, index):
    super()._range_check(index)
    return self.values[index]

  def regex(self):
    n = ''
    if self.negated:
      n = '^'
    return '[' + n + self.values + ']'


class Product(RegexType):
  def __init__(self, *values):
    self.values = values
    self.__c = None

  def __choices(self):
    if self.__c is None:
      self.__c = [v.choices() for v in self.values]
    return self.__c

  def regex(self):
    parts = [p.regex() for p in self.values]
    return "(" + "".join(parts) + ")"

  def __add__(self, other):
    if isinstance(other, str):
      other = Value(other)
    if isinstance(other, Product):
      return Product(*self.values, *other.values)
    return Product(*self.values, other)

  def __getitem__(self, index):
    super()._range_check(index)
    outputs = []
    for i, weight in enumerate(self.__choices()):
      option = index % weight
      index = index // weight
      outputs.append(self.values[i][option])

    return ''.join(outputs)

  def choices(self):
    return reduce(lambda x, y: x * y, self.__choices(), 1)


class Sum(RegexType):
  def __init__(self, *values):
    self.values = values
    self.__c = None

  def __choices(self):
    if self.__c is None:
      self.__c = [v.choices() for v in self.values]
    return self.__c

  def regex(self):
    parts = [p.regex() for p in self.values]
    return "(" + "|".join(parts) + ")"

  def __or__(self, other):
    if isinstance(other, str):
      other = Value(other)
    if isinstance(other, Sum):
      return Sum(*self.values, *other.values)
    return Sum(*self.values, other)

  def __getitem__(self, index):
    super()._range_check(index)
    weights = self.__choices()
    option = 0
    while index >= weights[option]:
      index -= weights[option]
      option += 1

    return self.values[option][index]

  def choices(self):
    return sum(self.__choices())


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

  def __count(self):
    count = self.repeat.max
    if count is None:
      count = max(FLAG_max_repeat.value, self.repeat.min)
    # Max is inclusive.
    return count - self.repeat.min + 1

  def regex(self):
    return self.value.regex() + self.repeat.regex()

  def __getitem__(self, index):
    super()._range_check(index)
    choices = self.value.choices()

    # Handle 1 differently
    if choices == 1:
      val = self.value[0]
      return val * self.repeat.min + val * index

    outputs = []
    # Mandatory repeats, just like Product.
    for _i in range(self.repeat.min):
      option = index % choices
      index = index // choices
      outputs.append(self.value[option])

    # Optional repeats.
    while index > 0:
      option = index % choices
      index = index // choices

      outputs.append(self.value[option])

    return ''.join(outputs)

  def choices(self):
    return self.value.choices() * self.__count()
