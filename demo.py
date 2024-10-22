from flang.interactive_flang_object import InteractiveFlangObject
from flang.parsers.xml import parse_text
from pprint import pprint
from flang.structures import BaseUserAST, FlangAST, UserASTRootContainerNode, UserASTTextNode
import itertools

TEST_SAMPLE_RECURSIVE_3 = """\
<html>
<head><link some="attribute">some link</link><link>some other link</link></head>
<body>
<script>console.log("hello")</script>
some <em>fancy</em> text
<div>
<div>
    nested
</div>
</div>
</body>
</html>\
"""

TEST_TEMPLATE_RECURSIVE = r"""
<choice name="xml-body" multi="true">
    <regex name="wspace">\s+</regex>
    <sequence name="xml-node" multi="true">
        <regex name="open-tag" value="{xml_open_tag}"/>
        <choice name="xml-content" multi="true">
            <regex name="raw-content" not="true" value="{lt}|{gt}"/>
            <use ref="....xml-body"/>
        </choice>
        <regex name="close-tag" value="{xml_close_tag}"/>
    </sequence>
</choice>
"""


def generate_patches(user_ast:BaseUserAST, flang_ast: FlangAST):
    if isinstance(user_ast, UserASTTextNode):
        return user_ast.content

    if isinstance(user_ast.children, list):
         return "".join(generate_patches(child, flang_ast) for child in user_ast.children)
    
    return ""


if __name__ == "__main__":
    template = TEST_TEMPLATE_RECURSIVE

    flang_ast = parse_text(template, validate_attributes=True)
    interactive_object = InteractiveFlangObject.from_string(flang_ast, TEST_SAMPLE_RECURSIVE_3)

    print(gen := generate_patches(interactive_object.user_ast, interactive_object.flang_ast))
    print(gen == TEST_SAMPLE_RECURSIVE_3)
