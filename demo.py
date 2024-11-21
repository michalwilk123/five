from flang.interactive_flang_object import InteractiveFlangObject
from flang.parsers.xml import parse_text
from flang.structures import BaseUserAST, FlangAST, UserLeaf, UserRoot
# from flang.structures.ast import UserASTRootContainerNode

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
    <text regex="true" name="wspace">\s+</text>
    <sequence name="xml-node" multi="true">
        <text regex="true" name="open-tag" value="{xml_open_tag}"/>
        <choice name="xml-content" multi="true">
            <text regex="true" name="raw-content" not="true" value="{lt}|{gt}"/>
            <use ref="....xml-body"/>
        </choice>
        <text regex="true" name="close-tag" value="{xml_close_tag}"/>
    </sequence>
</choice>
"""


def generate_patches(user_ast:BaseUserAST, flang_ast: FlangAST):
    if not isinstance(user_ast, UserRoot):
        flast = flang_ast.full_search(user_ast.flang_ast_path)

        if flast.type == "choice":
            print("WYBOR: {}")

        if flast.get_bool_attrib("optional"):
            print("optional")

        if flast.get_bool_attrib("multi"):
            print("multi")

    if isinstance(user_ast, UserLeaf):
        print(f"TEXT location: {user_ast.location} content: {repr(user_ast.content)}")
        return user_ast.content


    if isinstance(user_ast.children, list):
         return "".join(generate_patches(child, flang_ast) for child in user_ast.children)
    
    return ""


if __name__ == "__main__":
    template = TEST_TEMPLATE_RECURSIVE

    flang_ast = parse_text(template, validate_attributes=True)
    interactive_object = InteractiveFlangObject.from_string(flang_ast, TEST_SAMPLE_RECURSIVE_3)

    generated = generate_patches(interactive_object.user_ast, interactive_object.flang_ast)
    # print()

# def rewrite_language(from_obj, target_obj, )


def rewrite():
    flang_ast_python = parse_text("some")
    flang_ast_javascript = parse_text("some")

    python_user_ast = InteractiveFlangObject.from_string(flang_ast, TEST_SAMPLE_RECURSIVE_3).user_ast
    rewrite_language()



