
SOLID_JS_PROJECT_TEMPLATE = r"""
<sequence>
    <choice>
        <file pattern="store.ts">
        </file>
        <file pattern="components">
            <choice>
                <file multi="true" pattern="{vname}.tsx" regex="true">
                    <text command="Import statement for node.js" value="((.+)\n{1,2})*"/>
                    <text value="\n\n"\n>
                    <sequence multi="true" description="Place for component independent utility functions">
                        <sequence command="Utility function">
<text>function(</text><text command="Function arguments" value="[^\)]" regex="true"/>
<text value=") {\n"/>
<text command="Function body" value="" />
                        </sequence>
                        <text value="\n"/>
                    </sequence>
                </file>
            <choice>
        </file>
    </choice>
</sequence>


<file pattern="easy" name="html-project">
    <file multi="true" pattern="{filename}.html" regex="true">
        <sequence name="html">
            <text name="content" value="some text "/>
            <text regex="true" name="number" value="{number}"/>
        </sequence>
</file>
"""
