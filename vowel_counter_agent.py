import asyncio

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)


def count_vowels(text: str) -> int:
    vowels = 'aeiouAEIOU'
    return sum(1 for char in text if char in vowels)


@tool('count_vowels', 'Count the number of vowels in a given text', {'text': str})
async def count_vowels_tool(args):
    text = args.get('text', '')
    vowel_count = count_vowels(text)
    return {
        'content': [
            {
                'type': 'text',
                'text': f'The text contains {vowel_count} vowel(s).',
            }
        ]
    }


async def run_vowel_counter_agent(user_prompt: str):
    print(f'User prompt: {user_prompt}')
    print('Initializing vowel counter agent...\n')

    server = create_sdk_mcp_server(
        name='vowel-tools',
        version='1.0.0',
        tools=[count_vowels_tool],
    )

    options = ClaudeAgentOptions(
        model='claude-sonnet-4-5',
        mcp_servers={'vowel_tools': server},
        allowed_tools=['mcp__vowel_tools__count_vowels'],
    )

    print('Starting conversation with Claude...\n')

    async with ClaudeSDKClient(options=options) as client:
        await client.query(user_prompt)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f'Claude: {block.text}')
                    elif isinstance(block, ToolUseBlock):
                        print(f'Tool used: {block.name}')
                        print(f'Tool input: {block.input}')


async def main():
    user_prompt = 'Count the vowels in the text: "Hello World"'
    await run_vowel_counter_agent(user_prompt)


if __name__ == '__main__':
    asyncio.run(main())
