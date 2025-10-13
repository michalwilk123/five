import json

from five_cli.core.models import Message


def is_interaction_start_message(message: dict) -> bool:
    system = message.get('system')
    if not system:
        return False

    for item in system:
        if item.get('type') == 'text':
            text = item.get('text', '')
            if all(
                phrase in text
                for phrase in [
                    'Analyze if this message indicates a new conversation topic',
                    'extract a 2-3 word title that captures the new topic',
                    'new conversation topic',
                ]
            ):
                return True

    return False


def is_end_turn_response(content: dict) -> bool:
    return content.get('stop_reason') == 'end_turn'


def is_completion_request(content: dict) -> bool:
    system = content.get('system', [])
    if not system:
        return False

    for item in system:
        if item.get('type') == 'text':
            text = item.get('text', '')
            if (
                text == "You are Claude Code, Anthropic's official CLI for Claude."
                or 'You are an interactive CLI tool that helps users with software engineering tasks'
                in text
            ):
                return True

    return False


def parse_streaming_events(response_text):
    events = []
    lines = response_text.strip().split('\n')

    for i, line in enumerate(lines):
        line = line.strip()

        if line.startswith('event: '):
            event_type = line[7:].strip()
            is_next_line_text_data = i + 1 < len(lines) and lines[i + 1].strip().startswith(
                'data: '
            )

            if is_next_line_text_data:
                data_line = lines[i + 1][6:].strip()

                try:
                    data = json.loads(data_line)
                    events.append({'event': event_type, 'data': data})
                except json.JSONDecodeError:
                    continue

    return events


def merge_streaming_events(events):
    merged_response = {
        'message_id': None,
        'model': None,
        'role': 'assistant',
        'content_blocks': {},
        'usage': None,
        'stop_reason': None,
        'stop_sequence': None,
    }

    for event in events:
        event_type = event['event']
        data = event['data']

        if event_type == 'message_start':
            message = data.get('message', {})
            merged_response['message_id'] = message.get('id')
            merged_response['model'] = message.get('model')
            merged_response['usage'] = message.get('usage')

        elif event_type == 'content_block_start':
            index = data.get('index', 0)
            content_block = data.get('content_block', {})
            merged_response['content_blocks'][index] = {
                'type': content_block.get('type', 'text'),
                'text': content_block.get('text', ''),
            }

        elif event_type == 'content_block_delta':
            index = data.get('index', 0)
            delta = data.get('delta', {})
            if delta.get('type') == 'text_delta':
                text_to_add = delta.get('text', '')
                if index not in merged_response['content_blocks']:
                    merged_response['content_blocks'][index] = {'type': 'text', 'text': ''}
                merged_response['content_blocks'][index]['text'] += text_to_add

        elif event_type == 'message_delta':
            delta = data.get('delta', {})
            merged_response['stop_reason'] = delta.get('stop_reason')
            merged_response['stop_sequence'] = delta.get('stop_sequence')
            usage_data = data.get('usage', {})
            if usage_data:
                merged_response['usage'] = usage_data

    content_list = []
    for index in sorted(merged_response['content_blocks'].keys()):
        content_list.append(merged_response['content_blocks'][index])

    return {
        'message_id': merged_response['message_id'],
        'model': merged_response['model'],
        'role': merged_response['role'],
        'content': content_list,
        'stop_reason': merged_response['stop_reason'],
        'stop_sequence': merged_response['stop_sequence'],
        'usage': merged_response['usage'],
    }


def parse_streaming_response(response_text):
    events = parse_streaming_events(response_text)
    return merge_streaming_events(events)


def clean_completion_request_body(content: dict) -> dict:
    if all(instruction not in content for instruction in ['tools', 'system']):
        return content

    content = content.copy()
    content.pop('tools', None)

    # Only remove system messages that are not interaction start messages
    system = content.get('system', [])
    if system and not is_interaction_start_message(content):
        content.pop('system', None)

    return content


def extract_user_prompt(request_content: dict) -> str:
    messages = request_content.get('messages', [])

    for message in messages:
        if message.get('role') == 'user':
            content = message.get('content', '')
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Extract text from content blocks
                text_parts = []
                for block in content:
                    if block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                return ' '.join(text_parts)

    return ''


def is_system_reminder_message(content: str) -> bool:
    """Check if content is a system reminder message"""
    stripped = content.strip()
    return stripped.startswith('<system-reminder>') and stripped.endswith('</system-reminder>')


def _iter_message_blocks(messages: list):
    for message in messages:
        content = message.get('content', [])
        if isinstance(content, list):
            for block in content:
                yield block


def _iter_tool_use_blocks(conversation_data: dict):
    for data in conversation_data.values():
        messages = data.get('request', {}).get('messages', [])
        for block in _iter_message_blocks(messages):
            if block.get('type') == 'tool_use':
                yield messages, block


def has_write_tool_usage(conversation_data: dict) -> bool:
    """Check if conversation contains successful Write/Edit/MultiEdit tool usage"""
    write_tools = {'Write', 'Edit', 'MultiEdit', 'NotebookEdit'}

    for messages, block in _iter_tool_use_blocks(conversation_data):
        if block.get('name', '') in write_tools:
            if _has_successful_tool_result(messages, block.get('id', '')):
                return True

    return False


def get_accessed_file_paths(conversation_data: dict) -> list[str]:
    """Extract file paths from successful Read, Grep, and Glob tool calls"""
    accessed_files = set()

    for messages, block in _iter_tool_use_blocks(conversation_data):
        if _has_successful_tool_result(messages, block.get('id', '')):
            tool_name = block.get('name', '')
            tool_input = block.get('input', {}) or {}

            if tool_name == 'Read':
                file_path = tool_input.get('file_path')
                if file_path:
                    accessed_files.add(file_path)
            elif tool_name in ('Grep', 'Glob'):
                accessed_files.add(tool_input.get('path', '.'))

    return sorted(list(accessed_files))


def _has_successful_tool_result(messages: list, tool_use_id: str) -> bool:
    """Check if there's a successful tool result for the given tool_use_id"""
    for block in _iter_message_blocks(messages):
        if block.get('type') == 'tool_result' and block.get('tool_use_id') == tool_use_id:
            result_content = block.get('content', '')
            if isinstance(result_content, str):
                result_lower = result_content.strip().lower()
                error_indicators = ['error', 'error:', 'failed', 'exception']
                has_error = any(indicator in result_lower for indicator in error_indicators)
                return not (result_lower.startswith('error') or has_error)
            return True
    return False


def convert_to_conversation_format(request_content: dict, response_content: dict) -> list[Message]:
    conversations = []

    # Process request messages
    messages = request_content.get('messages', [])
    for message in messages:
        role = message.get('role', '')
        content = message.get('content', '')

        if isinstance(content, list):
            # Handle content blocks (tool use, text, etc.)
            for block in content:
                if block.get('type') == 'text':
                    text_content = block.get('text', '')
                    # Skip system reminder messages
                    if not is_system_reminder_message(text_content):
                        conversations.append(
                            Message(
                                role=role,
                                content=text_content,
                                arguments=None,
                                results=None,
                                type='text',
                            )
                        )
                elif block.get('type') == 'tool_use':
                    conversations.append(
                        Message(
                            role=role,
                            content=block.get('name', ''),
                            arguments=block.get('input', {}),
                            results=None,
                            type='tool_use',
                        )
                    )
                elif block.get('type') == 'tool_result':
                    conversations.append(
                        Message(
                            role=role,
                            content=None,
                            arguments=None,
                            results={
                                'tool_use_id': block.get('tool_use_id'),
                                'content': block.get('content'),
                            },
                            type='tool_result',
                        )
                    )
        else:
            # Simple text content - skip system reminder messages
            if not is_system_reminder_message(content):
                conversations.append(
                    Message(role=role, content=content, arguments=None, results=None, type='text')
                )

    # Process response content
    response_content_blocks = response_content.get('content', [])
    for block in response_content_blocks:
        if block.get('type') == 'text':
            conversations.append(
                Message(
                    role='assistant',
                    content=block.get('text', ''),
                    arguments=None,
                    results=None,
                    type='text',
                )
            )

    return conversations
