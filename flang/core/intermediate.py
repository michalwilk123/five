from __future__ import annotations
import xml.etree.ElementTree as ET

from utils.dataclasses import (
    IntermediateFlangTreeElement,
)
from utils.abstracts import (
    TextToIntermediateTreeParser,
)
from utils.helpers import interlace
import re


class FlangXMLParser(TextToIntermediateTreeParser):
    def _build_tree(
        self,
        element: ET.Element | str,
        index: int = 0,
        last_element: bool = True,
    ):
        if isinstance(element, str):
            if re.match("\s+", element):
                return None
            # if index == 0:
            #     element = element.removeprefix("\n")
            # if last_element:
            #     element = element.removesuffix("\n")

            return IntermediateFlangTreeElement("text", element) if element else None

        children_list = [item for item in interlace(element.itertext(), element)]

        children: list[IntermediateFlangTreeElement] = (
            self._build_tree(child, index=idx, last_element=idx == len(children_list) - 1)
            for idx, child in enumerate(children_list)
        )
        children = list(filter(None, children))

        return IntermediateFlangTreeElement(
            name=element.tag, value=children, attributes=element.attrib
        )

    def parse(self, text: str) -> IntermediateFlangTreeElement:
        processed_xml = ET.fromstring(text)
        return self._build_tree(processed_xml)
