from fenv.shell import FenvShell
from flang.parsers.xml import FlangXMLParser

TEST_TEMPLATE = r"""
<component name="import">
<component name="header" multi="true">
<text multi="true">AAA</text>
<regex default="\n">\\s</regex>
</component>
<component name="variable" multi="true">
<text value="variable: "/><regex name="name" value="{vname}"/><regex value=";\n?" default=";\n"/>
</component>
</component>
"""

if __name__ == "__main__":
    parser = FlangXMLParser()
    flang_object = parser.parse_text(TEST_TEMPLATE)
    shell = FenvShell(flang_object)
    generated = shell.start().replace("\\n", "\n")
    print(generated)
