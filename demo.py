from flang.flang_object import FlangObject
from flang.parsers.xml import parse_text
from flang.structures import FlangAST, TemplateTree, FlangLeaf, FlangRoot
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


def generate_patches(flang_tree:FlangAST, template_tree: TemplateTree):
    if not isinstance(flang_tree, FlangRoot):
        flast = template_tree.full_search(flang_tree.template_id)

        if flast.type == "choice":
            print("WYBOR: {}")

        if flast.get_bool_attrib("optional"):
            print("optional")

        if flast.get_bool_attrib("multi"):
            print("multi")

    if isinstance(flang_tree, FlangLeaf):
        print(f"TEXT location: {flang_tree.location} content: {repr(flang_tree.content)}")
        return flang_tree.content


    if isinstance(flang_tree.children, list):
         return "".join(generate_patches(child, template_tree) for child in flang_tree.children)
    
    return ""


if __name__ == "__main__":
    template = TEST_TEMPLATE_RECURSIVE

    template_tree = parse_text(template, validate_attributes=True)
    interactive_object = FlangObject.from_string(template_tree, TEST_SAMPLE_RECURSIVE_3)

    generated = generate_patches(interactive_object.flang_tree, interactive_object.template_tree)
    # print()

# def rewrite_language(from_obj, target_obj, )


def rewrite():
    template_tree_python = parse_text("some")
    template_tree_javascript = parse_text("some")

    python_flang_tree = FlangObject.from_string(template_tree, TEST_SAMPLE_RECURSIVE_3).flang_tree
    rewrite_language()



