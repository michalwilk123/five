PYTHON_CODE_TEMPLATE = r"""
<choice name="code" multi="true" optional="true" alias="code">
    <sequence name="for-in-loop">
        <text value="for "/><regex value="{vname}" name="index"/><text value=" in range(" />
        <sequence optional="true">
            <regex value="{integer}" name="start"/><text value=", "/>
        </sequence>
        <regex value="{integer}" name="end"/><text value="):\n"/>
        <sequence name="for-loop-body" multi="true">
            <use ref="@tab"/>
            <use ref="@code"/>
        </sequence>
    </sequence>
    <sequence name="if-stmt">
        <text value="if "/><use ref="@bool-stmt"/><text value=":\n"/>
        <choice>
            <sequence>
                <use ref="@tab"/>
                <use ref="@code"/>
            </sequence>
            <sequence>
                <text value="elif "/><use ref="@bool-stmt"/><text value=":\n"/>
                <sequence>
                    <use ref="@tab"/>
                    <use ref="@code"/>
                </sequence>
            </sequence>
        </choice>
        <sequence optional="true">
            <text value="else:\n"/>
            <sequence>
                <use ref="@tab"/>
                <use ref="@code"/>
            </sequence>
        </sequence>
    </sequence>
    <sequence>
        <text value="print("/>
        <regex value="{integer|string|vname}"/>
        <text value=")\n"/>
    </sequence>
</choice>
<choice visible="false" alias="bool-stmt">
    <text name="true" value="True"/>
    <text name="false" value="False"/>
    <sequence>
        <regex value="{vname|integer}" name="l-value"/><text value=" % "/><regex value="{vname|integer}" name="r-value"/>
    </sequence>
</choice>
<text visible="false" alias="tab" value="    "/>
"""


JAVASCRIPT_CODE_TEMPLATE = r"""
<choice name="code" multi="true" optional="true" alias="code">
    <sequence name="for-in-loop">
        <text value="for(int "/><regex value="{vname}" name="index"/><text value="=" />
        <regex value="{integer}" name="start"/><text value="; "/><regex value="{vname}" name="start"/>
        <text value=" < "/><regex value="{integer}" name="end"/><text value="; "/><regex value="{vname}" name="start"/>
        <text value="++) {\n"/>
        <sequence name="for-loop-body" multi="true">
            <use ref="@tab"/>
            <use ref="@code"/>
        </sequence>
    </sequence>
    <sequence name="if-stmt">
        <text value="if ("/><use ref="@bool-stmt"/><text value=") {\n"/>
        <choice>
            <sequence>
                <use ref="@tab"/>
                <use ref="@code"/>
                <text value="}"/>
            </sequence>
            <sequence>
                <text value="else if ("/><use ref="@bool-stmt"/><text value=") {\n"/>
                <sequence>
                    <use ref="@tab"/>
                    <use ref="@code"/>
                <text value="}"/>
                </sequence>
            </sequence>
        </choice>
        <sequence optional="true">
            <text value="else {\n"/>
            <sequence>
                <use ref="@tab"/>
                <use ref="@code"/>
                <text value="}"/>
            </sequence>
        </sequence>
    </sequence>
    <sequence>
        <text value="console.log("/>
        <regex value="{integer|string|vname}"/>
        <text value=");\n"/>
    </sequence>
</choice>
<choice visible="false" alias="bool-stmt">
    <text name="true" value="true"/>
    <text name="false" value="false"/>
    <sequence>
        <regex value="{vname|integer}" name="l-value"/><text value=" % "/><regex value="{vname|integer}" name="r-value"/>
    </sequence>
</choice>
<text visible="false" alias="tab" value="    "/>
"""

a = """
<define name="block">
    <text value="{"/>
        <sequence multi="true">
            <regex value="{wspace}" optional="true"/><argument/>
        </sequence>
    <text value="}"/>
<define/>
<define name="condtition-construct">
    <argument/><regex value="{wspace}" default="\n"/>
    <call ref=".block">
        <argument/>
    <call/>
</define>
<define name="forloop">
    <call ref=".condtition-construct">
        <sequence>
            <text value="for(number i="/><regex name="start" value="{integer}" default="0"/>
            <text value="; i < "/><regex name="end" value="{integer}" default="10"/>
            <text value="; i++)"/>
        </sequence>
        <argument/>
    <call>
</define>
<call ref=".forloop">
    <text value="STATEMENT"/>
</call>
"""

REWRITE_SCRIPT = """
modify python.component.1 javascript.component.1 
argument.lala -> argument.other, foo -> bar;

"""
