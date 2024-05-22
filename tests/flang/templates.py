TEST_BASIC_TEMPLATE = """
<component>
    <text value="hello "/><regex name="subject" value="{vname}"/>
</component>
"""

TEST_BASIC_SAMPLE = "hello world"
TEST_BASIC_SAMPLE_FAILURE_1 = "goodbye world"
TEST_BASIC_SAMPLE_FAILURE_2 = "hello my world"

TEST_TEMPLATE_CHOICE = """
<component name="import">
<choice>
<text name="text">AAA</text>
<regex name="regex">{vname}</regex>
<text name="wrong">
THIS IS WRONG
</text>
</choice>
</component>
"""

TEST_TEMPLATE_USE = """
<component name="import">
<component name="foo" visible="false">
<text>foo</text>
</component>
<component name="bar">
<use ref="..foo"/>
</component>
</component>
"""

TEST_TEMPLATE_MULTI = r"""
<component name="import">
<component name="header" multi="true">
<text multi="true">AAA</text>
<regex>\s</regex>
</component>
<component name="variable" multi="true">
<text value="variable: "/><regex name="name" value="{vname}"/><regex value=";\n?"/>
</component>
</component>
"""

TEST_SAMPLE_MULTI = """\
AAAAAAAAAAAA
AAA
AAAAAA
variable: somevalue;
variable: someothervalue;
"""

TEST_TEMPLATE_FILE = r"""\
<component name="text-file">
<file type="dir" filename="{vname}_app" name="app">
<component name="app-file" multi="true">
<choice>
<file name="css" filename="{vname}\.css">
    <component name="assignment" multi="true">
        <regex name="property" value="{vname}"/><text value=": "/>
        <regex name="value" value="{vname}|{number}|{string}"/>
    </component>
</file>
<file name="javascript" filename="{vname}\.js">
<regex name="code" value=".*"/>
</file>
<file name="ignored" type="any" filename="\.gitignore|\.git">
<regex name="code" value=".*"/>
</file>
</choice>
</component>
</file>
</component>
"""

DUMMY_TEST_TEMPLATE_EVENT = """
<component name="code">
<component name="import" multi="true">
<text value="import "/><regex name="import_name" value="{vname}"/><text value="\\n"/>
</component>
<component name="function-call" on-create=".">
<event args="tree,component">
function_name = tree.get("name")
tree.parent().get("import").insert(name=function_name)
</event>
<regex name="name" value="({vname}(\.{vname}))"/><text value="("/>
<regex name="arguments" value="[^)]*"/>
<text value=")"/>
</component>
</component>
"""

# END
## END
### END
#### END
##### END
###### END
####### END
######## END
######### END
########## END
########### END
############ END
############# END
############## END
############### END
################ END
################# END
################## END
################### END
#################### END
########### END
############ END
############# END
############## END
############### END
################ END
################# END
################## END
################### END
#################### END
##################### END
###################### END
####################### END
######################## END
######################### END
########################## END
########################### END
################## END
################### END
#################### END
##################### END
###################### END
####################### END
######################## END
######################### END
########################## END
########################### END
############################ END
############################# END
############################## END
############################### END
################################ END
################################# END
################################## END
################################### END
#################################### END
##################################### END

DUMMY_TEST_TEMPLATE_EVENT = """
<component name="code">
<component name="import">
<text value="import "/><regex value="{vname}"/><text value="\\n"/>
</component>
<component name="function-call" on-create=".">
<event args="tree">
print("hello world")
</event>
<regex name="name" value="({vname}(\.{vname}))"/><text value="("/>
<regex name="arguments" value="[^)]*"/>
<text value=")"/>
</component>
</component>
"""

SAMPLE_CHOICE = "AAAAAA"
SPEC_EVENT = None

DUMMY_TEST_TEMPLATE_EVENT = """
<component name="code">
<component name="import">
<text value="import "/><regex value="{vname}"/><text value="\\n"/>
</component>
<component name="function-call" on-create=".">
<event args="tree">
print("hello world")
</event>
<regex name="name" value="({vname}(\.{vname}))"/><text value="("/>
<regex name="arguments" value="[^)]*"/>
<text value=")"/>
</component>
</component>
"""


# def main():
#     parser = FlangXMLParser()
#     # flang_object = parser.parse_text(DUMMY_TEST_TEMPLATE_CHOICE_1)
#     # print(flang_object)
#     # processor = FlangTextProcessor(flang_object)
#     # match_obj = processor.backward(SAMPLE_CHOICE)
#     # print()
#     # print(match_obj)
#     # generated = processor.forward(match_obj)
#     # print()
#     # print(generated)

#     # flang_object = parser.parse_text(DUMMY_TEST_TEMPLATE_EVENT)
#     # processor = FlangTextProcessor(flang_object)
#     # print(processor.forward)
#     # generated = processor.forward(SPEC_EVENT)
#     # print(generated)

#     # print()
#     # parser.clear()
#     flang_object = parser.parse_text(DUMMY_TEST_TEMPLATE_MULTI)
#     processor = FlangTextProcessor(flang_object)
#     match_obj = processor.forward(SAMPLE_MULTI)
#     print(match_obj)
#     generated = processor.backward(match_obj)
#     print(generated)
