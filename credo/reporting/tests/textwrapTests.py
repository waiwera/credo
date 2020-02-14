from __future__ import print_function
import textwrap

inStr1 = """A test string
   where lines
   have spaces"""

inStr2 = """  A test string\n  with constant\n  indent."""

for s in [inStr1, inStr2]:
    print("str initial:")
    print(s)
    s2 = textwrap.dedent(s)
    print("str dedent:")
    print(s2)
