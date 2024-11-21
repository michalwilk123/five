PYTHON_CODE_TEMPLATE = """
<sequence>
    <choice alias="bool-stmt" hidden="true">
        <text name="true" value="True"/>
        <text name="false" value="False"/>
        <sequence>
            <text regex="true" value="{vname}|{integer}" name="l-value"/><text value=" % "/>
            <text regex="true" value="{vname}|{integer}" name="r-value"/><text value=" == "/>
            <text regex="true" value="{vname}|{integer}" name="equality-r-value"/>
        </sequence>
    </choice>
    <text alias="tab" value="    " hidden="true"/>
    <choice name="code" multi="true" optional="false" alias="code">
        <sequence name="for-in-loop">
            <text value="for "/><text regex="true" value="{vname}" name="index"/><text value=" in range(" />
            <sequence optional="true">
                <text regex="true" value="{integer}" name="start"/><text value=", "/>
            </sequence>
            <text regex="true" value="{integer}" name="end"/>
            <text value="):&#xA;"/>
            <sequence name="for-loop-body" multi="true">
                <use ref="@tab"/>
                <use ref="@code"/>
            </sequence>
        </sequence>
        <sequence name="if-stmt">
            <text value="if "/><use ref="@bool-stmt"/><text value=":&#xA;"/>
            <choice>
                <sequence multi="true">
                    <use ref="@tab"/>
                    <use ref="@code"/>
                </sequence>
                <sequence>
                    <text value="elif "/><use ref="@bool-stmt"/><text value=":&#xA;"/>
                    <sequence multi="true">
                        <use ref="@tab"/>
                        <use ref="@code"/>
                    </sequence>
                </sequence>
            </choice>
            <sequence optional="true">
                <text value="else:&#xA;"/>
                <sequence>
                    <use ref="@tab"/>
                    <use ref="@code"/>
                </sequence>
            </sequence>
        </sequence>
        <sequence>
            <text value="print("/>
            <text regex="true" value="{integer}|{string}|{vname}"/>
            <text value=")"/>
        </sequence>
        <text value="pass"/>
        <text regex="true" name="wspace">\\s+</text>
    </choice>
</sequence>
"""


JAVASCRIPT_CODE_TEMPLATE = """
<sequence>
    <choice name="code" multi="true" optional="true" alias="code">
        <sequence name="for-in-loop">
            <text value="for(int "/><text regex="true" value="{vname}" name="index"/><text value="=" />
            <text regex="true" value="{integer}" name="start"/><text value="; "/><text regex="true" value="{vname}" name="start"/>
            <text value=" &lt; "/><text regex="true" value="{integer}" name="end"/><text value="; "/><text regex="true" value="{vname}" name="start"/>
            <text value="++) {&#xA;"/>
            <sequence name="for-loop-body" multi="true">
                <use ref="@tab"/>
                <use ref="@code"/>
            </sequence>
        </sequence>
        <sequence name="if-stmt">
            <text value="if ("/><use ref="@bool-stmt"/><text value=") {&#xA;"/>
            <choice>
                <sequence>
                    <use ref="@tab"/>
                    <use ref="@code"/>
                    <text value="}"/>
                </sequence>
                <sequence>
                    <text value="else if ("/><use ref="@bool-stmt"/><text value=") {&#xA;"/>
                    <sequence>
                        <use ref="@tab"/>
                        <use ref="@code"/>
                    <text value="}"/>
                    </sequence>
                </sequence>
            </choice>
            <sequence optional="true">
                <text value="else {&#xA;"/>
                <sequence>
                    <use ref="@tab"/>
                    <use ref="@code"/>
                    <text value="}"/>
                </sequence>
            </sequence>
        </sequence>
        <sequence>
            <text value="console.log("/>
            <text regex="true" value="{integer}|{string}|{vname}"/>
            <text value=");"/>
        </sequence>
        <text regex="true" name="wspace">\s+</text>
    </choice>
    <choice alias="bool-stmt" hidden="true">
        <text name="true" value="true"/>
        <text name="false" value="false"/>
        <sequence>
            <text regex="true" value="{vname}|{integer}" name="l-value"/><text value=" % "/><text regex="true" value="{vname}|{integer}" name="r-value"/>
        </sequence>
    </choice>
    <text alias="tab" value="    " hidden="true"/>
</sequence>
"""

PYTHON_CODE_SAMPLE_1 = """
print("hello world")
pass
"""

PYTHON_CODE_SAMPLE_2 = """
pass
for i in range(10):
    pass
    print(10)
"""

PYTHON_CODE_SAMPLE_3 = """
if i % 2 == 0:
    print(123)
"""

PYTHON_CODE_SAMPLE_4 = """
if i % 2 == 0:
    for value in range(111):
        if i % 10 == 2:
            print("nested")
"""

JS_CODE_SAMPLE_1 = """
console.log(1);
console.log(1);
"""

JS_CODE_SAMPLE_2 = """
for(var i=0;i<10;i++) {
    console.log(1);
}
"""

JS_CODE_SAMPLE_3 = """
if (value % 10 == 2){
    console.log("lorem ipsum");
} else if (true) {
    console.log(32332);
} else {
    console.log(10)
}
"""

PYTHON_CODE_SAMPLE_FIZZBUZZ = """
for i in range(1, 101):
    if i % 15 == 0:
        print("FizzBuzz")
    elif i % 3 == 0:
        print("Fizz")
    elif i % 5 == 0:
        print("Buzz")
    else:
        print(i)
"""

JAVASCRIPT_CODE_SAMPLE_FIZZBUZZ = """
for i in range(1, 101):
    if i % 15 == 0:
        print("FizzBuzz")
    elif i % 3 == 0:
        print("Fizz")
    elif i % 5 == 0:
        print("Buzz")
    else:
        print(i)
"""

REWRITE_SCRIPT = """
modify python.component.1 javascript.component.1 
argument.lala -> argument.other, foo -> bar;

"""
