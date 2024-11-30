"""
This is a system test that thoughoutly tests if 
all features combined can recreate the same input as was provided

In short, this is combined into steps:

1. We get FlangAST and a sample of code that should be valid
2. Text sample is parsed and UserAST is produced
3. UserAST is transformed into key-value specification
"""

import unittest


class GenerationPipelineTestCase(unittest.TestCase): ...
