from flang.flang_parser3 import FlangXMLParser, FlangTextProcessor, MatchNotFound
from unittest import TestCase

class TestFlang(TestCase):
    def setUp(self) -> None:
        self.parser = FlangXMLParser()
    
    def test_basic(self):
        ...
    
    def test_failure(self):
        ...
    
    def test_choice(self):
        ...

    def test_multi(self):
        ...

    def test_optional(self):
        ...