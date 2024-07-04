TEST_BASIC_TEMPLATE = """
<component>
    <text value="hello "/><regex name="subject" value="{vname}"/>
</component>
"""

TEST_BASIC_SAMPLE = "hello world"
TEST_BASIC_SAMPLE_FAILURE_1 = "goodbye world"
TEST_BASIC_SAMPLE_FAILURE_2 = "hello cruel world"
TEST_CHOICE_NESTED_SAMPLE = r"""
Lorem ipsum, dolor sit amet...
end"""
TEST_OPTIONAL_SAMPLE_1 = "this is a number: 123"
TEST_OPTIONAL_SAMPLE_2 = 'this is a text: "some text"'
TEST_OPTIONAL_SAMPLE_3 = "this is a text: 111"

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

# Lorem ipsum dolor sit amet
# this would be useful with combination of "use" construct
# f.e.: choice of variable declaration or types or raw values
TEST_TEMPLATE_CHOICE_NESTED = r"""
<component name="nested">
<choice name="all-pieces" multi="true">
<choice name="text-pieces">
<text value="ipsum"/>
<text value="Lorem"/>
<text name="wrong" value="wrong!"/>
<text value="dolor"/>
<text value="amet"/>
<text value="sit"/>
</choice>
<choice name="my-regexes">
<regex name="whitespace">\s</regex>
<regex name="separators">[,.]</regex>
<regex name="wrong">[:;%$]+</regex>
<regex name="number">{number}</regex>
</choice>
<text name="wrong">wrong</text>
</choice>
<text value="end"/>
</component>
"""

TEST_TEMPLATE_OPTIONAL = """
<component name="opt">
<text value="this is a "/>
<component name="num" optional="true">
<text value="number: "/><regex value="{number}"/>
</component>
<component name="txt" optional="true">
<text value="text: "/><regex value="{string}"/>
</component>
</component>
"""

TEST_TEMPLATE_CHOICE_AND_MULTI = r"""
<component name="test">
<component name="test-multi" multi="true">
<choice>
</choice>
<regex value="\s" />
<text value="the end"/>
</component>
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

"""
Wiadomo ze jezeli chcialbys sparsowac cokolwiek to wszystko mozna owinac
w regexy i sobie znacznie ulatwic sprawe.
Zapominasz tylko po co tak naprawde istnieje ta klazura multi

bardziej w tym chodzi o to aby okreslic ze zwracana jest lista jakis
obiektow, np componentow ze zmatchowanym tekstem. Jakby musisz wciaz o tym
pamietac
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

DUMMY_TEST_TEMPLATE_EVENT = r"""
<component name="code">
<component name="import" multi="true">
<text value="import "/><regex name="import_name" value="{vname}"/><text value="\n"/>
</component>
<component name="function-call" on-create=".">
<event args="tree">
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

DUMMY_TEST_TEMPLATE_EVENT = r"""
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

DUMMY_TEST_TEMPLATE_EVENT = r"""
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
