from datetime import datetime
import json
import logging
import signal
import subprocess
import sys

from mitmproxy import http

from five_cli.ai.anthropic import (
    clean_completion_request_body,
    convert_to_conversation_format,
    extract_user_prompt,
    get_accessed_file_paths,
    has_write_tool_usage,
    is_completion_request,
    is_end_turn_response,
    is_interaction_start_message,
    parse_streaming_response,
)
from five_cli.core.events import on_ai_agent_start, on_ai_agent_stop
from five_cli.core.models import CompletedTask, Conversation

CLAUDE_HOSTS = [
    'api.anthropic.com',
    'claude.ai',
    'console.anthropic.com',
]


def notify_send(title: str, message: str = '') -> None:
    """Default notification implementation using notify-send."""
    subprocess.run(['notify-send', title, message], check=False)


class ClaudeInterceptor:
    def __init__(self, log_file, five_config_path, project_path):
        self.logger = logging.getLogger('five_cli.proxy.addon')
        self.log_file = log_file
        self.five_config_path = five_config_path
        self.project_path = project_path
        self.message_request_dictionary = {}
        self.conversation_data = {}  # Store request/response pairs for conversation building
        self.conversation_active = False
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""

        def signal_handler(signum, frame):
            self.log_to_file(f'Received signal {signum}, ending conversation gracefully')
            if self.conversation_active:
                self.end_conversation_gracefully()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def log_to_file(self, message):
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(message + '\n')

    def log_claude_request(self, flow: http.HTTPFlow, timestamp: str) -> None:
        self.log_to_file(f'\n{"=" * 80}')
        self.log_to_file(f'[Claude request] {timestamp}')
        self.log_to_file(f'method: {flow.request.method}')
        self.log_to_file(f'URL: {flow.request.pretty_url}')

    def log_request_body(self, byte_len: int, json_content: dict) -> None:
        self.log_to_file(f'\nRequest Body ({byte_len} bytes):')
        self.log_to_file(json.dumps(json_content, indent=2))

    def log_merged_response(self, merged: dict, timestamp: str) -> None:
        self.log_to_file(f'\n[{timestamp}] MERGED RESPONSE:')
        self.log_to_file(json.dumps(merged, indent=2))

    def log_conversation_analysis(self, has_code_changes: bool, accessed_files: list[str]) -> None:
        self.log_to_file(f'\n{"=" * 40}')
        self.log_to_file('CONVERSATION ANALYSIS')
        self.log_to_file(f'Has code changes: {has_code_changes}')
        self.log_to_file(f'Files accessed: {len(accessed_files)}')
        if accessed_files:
            self.log_to_file('Accessed file paths:')
            for file_path in accessed_files:
                self.log_to_file(f'  - {file_path}')
        self.log_to_file(f'{"=" * 40}')

    def end_conversation_gracefully(self):
        """End conversation gracefully when interrupted"""
        self.log_to_file('Ending conversation due to interruption')

        if self.conversation_data:
            # Process all conversation data to check for code changes
            has_code_changes = has_write_tool_usage(self.conversation_data)
            accessed_files = get_accessed_file_paths(self.conversation_data)

            self.log_conversation_analysis(has_code_changes, accessed_files)

            if has_code_changes:
                # Use the most recent conversation data for the task
                latest_flow_id = max(self.conversation_data.keys())
                latest_data = self.conversation_data[latest_flow_id]

                request_content = latest_data.get('request', {})
                response_content = latest_data.get('response', {})

                user_prompt = extract_user_prompt(request_content)
                conversations = convert_to_conversation_format(request_content, response_content)

                task = CompletedTask(
                    references=[],
                    conversation=Conversation(
                        user_prompt=user_prompt or 'Interrupted conversation',
                        messages=conversations,
                        temperature=request_content.get('temperature', 1.0),
                        model_name=response_content.get('model', 'unknown'),
                    ),
                )

                on_ai_agent_stop(
                    self.five_config_path,
                    self.project_path,
                    task,
                    self.log_to_file,
                    self.log_to_file,
                )
                notify_send('🟠 Conversation Interrupted', 'Changes committed')
            else:
                notify_send('🟠 Conversation Interrupted', 'No changes detected')

        self.conversation_active = False
        self.conversation_data.clear()

    def request(self, flow: http.HTTPFlow) -> None:
        if (
            flow.request.pretty_host in CLAUDE_HOSTS
            and flow.request.path == '/custom-proxy-health-check'
        ):
            health_response = {
                'status': 'running',
                'proxy': 'claude-mitm-proxy',
                'timestamp': datetime.now().isoformat(),
                'features': ['system-key-removal', 'request-logging'],
            }
            flow.response = http.Response.make(
                200,
                json.dumps(health_response, indent=2),
                {'Content-Type': 'application/json'},
            )
            return

        if (
            flow.request.pretty_host == 'api.anthropic.com'
            and '/v1/messages' in flow.request.path
            and flow.request.method == 'POST'
        ):
            # Parse JSON safely; if invalid, log and skip tracking this flow
            try:
                json_request_content = flow.request.json()
            except Exception as e:
                self.log_to_file(f'INVALID OR MALFORMED JSON REQUEST: {str(e)}')
                return

            if not isinstance(json_request_content, dict):
                self.log_to_file('UNEXPECTED JSON TYPE (expected object)')
                return

            self.message_request_dictionary[flow.id] = json_request_content

            timestamp = datetime.now().isoformat()

            self.log_claude_request(flow, timestamp)

            json_content = clean_completion_request_body(json_request_content)
            self.log_request_body(len(flow.request.content), json_content)

            if is_interaction_start_message(json_request_content):
                self.conversation_active = True
                on_ai_agent_start(
                    self.five_config_path, self.project_path, self.log_to_file, self.log_to_file
                )
                notify_send('🟢 Conversation Started', '')

    def response(self, flow: http.HTTPFlow) -> None:
        if not (request_json_message := self.message_request_dictionary.pop(flow.id, None)):
            return

        try:
            merged = parse_streaming_response(flow.response.text)
            timestamp = datetime.now().isoformat()
            self.log_merged_response(merged, timestamp)
        except Exception as e:
            self.log_to_file(f'\n[MERGE ERROR] {str(e)}')
            return

        # Store conversation data for building CodeGenerationTask
        self.conversation_data[flow.id] = {
            'request': request_json_message,
            'response': merged,
            'timestamp': timestamp,
        }

        # Check if this is the end of an interaction - be more permissive
        # End of interaction if we have an end_turn response OR if the conversation was active
        is_end_of_interaction = (self.conversation_active and is_end_turn_response(merged)) or (
            # Fallback: check if it looks like a completion request with end turn
            is_completion_request(request_json_message) and is_end_turn_response(merged)
        )

        if is_end_of_interaction:
            # Check if conversation contains actual code changes - use all conversation data
            has_code_changes = has_write_tool_usage(self.conversation_data)
            notify_send('🔴 Conversation Ended:', 'Has code changes: {}'.format(has_code_changes))
            accessed_files = get_accessed_file_paths(self.conversation_data)
            notify_send('🔴 Conversation Ended:', 'Accessed files: {}'.format(accessed_files))

            self.log_conversation_analysis(has_code_changes, accessed_files)

            # Only commit if there are actual code changes
            if has_code_changes:
                latest_data = self.conversation_data.get(flow.id, {})
                request_content = latest_data.get('request', {})
                response_content = latest_data.get('response', {})

                user_prompt = latest_data.get('initial_user_prompt') or extract_user_prompt(
                    request_content
                )
                conversations = convert_to_conversation_format(request_content, response_content)
                task = CompletedTask(
                    references=[],
                    conversation=Conversation(
                        user_prompt=user_prompt,
                        messages=conversations,
                        temperature=request_content.get('temperature', 1.0),
                        model_name=response_content.get('model', 'unknown'),
                    ),
                )

                on_ai_agent_stop(
                    self.five_config_path,
                    self.project_path,
                    task,
                    self.log_to_file,
                    self.log_to_file,
                )
            else:
                self.log_to_file('Skipping commit - no code changes detected')

            # Display generation task info in notification
            try:
                latest_data = self.conversation_data.get(flow.id)
                if latest_data:
                    user_prompt = extract_user_prompt(latest_data.get('request', {}))

                    # Truncate prompt for notification
                    prompt_preview = (
                        user_prompt[:50] + '...' if len(user_prompt) > 50 else user_prompt
                    )

                    if has_code_changes:
                        notify_send('🔴 Conversation Ended', f'Task: {prompt_preview}')
                    else:
                        notify_send('🔴 Conversation Ended (No Changes)', f'Task: {prompt_preview}')
                else:
                    notify_send('🔴 Conversation Ended', '')
            except Exception as e:
                notify_send('🔴 Conversation Ended', f'Error: {str(e)}')
            finally:
                self.conversation_active = False
                self.conversation_data.clear()  # Clear all conversation data, not just current flow
