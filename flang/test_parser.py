from flang_parser3 import FlangXMLParser, FlangTextProcessor
from flang_redactor import FlangRedactor

DUMMY_TEST_TEMPLATE_EVENT = r"""
<component name="code">
<component name="import" multi="true">
<choice>
<component name="statement">
<text value="import "/><regex value="{vname}"/>
</component>
<regex value="\n"/>
</choice>
</component>
<component name="function-call" on-create=".">
<regex name="name" value="({vname}(\.{vname}))"/><text value="("/>
<regex name="arguments" value="[^)]*"/>
<text value=")"/><text value="\n" optional="true"/>
</component>
</component>
"""
# <event args="tree">
# print("hello world")
# </event>

TEST_SAMPLE = """\
import json

json.parse({"first":1})
json.parse({"second":1})
json.parse({"third":1})
"""

parser = FlangXMLParser()
obj = parser.parse_text(DUMMY_TEST_TEMPLATE_EVENT)
processor = FlangTextProcessor(obj)


spec = processor.forward(TEST_SAMPLE)

redactor = FlangRedactor()
# redactor.move(spec, "someobjectlalala", "someotherlocationlalala")
redactor.insert(somespec={"lalalal"})
redactor.delete()
