import unittest

from flang.structures import Event, EventStorage

TEST_1_EVENT_SOURCE_CODE = """
var = 123

if var > 10:
    var = 22
else:
    pass

context["result"] = "success"

def f():
    nonlocal var
    var += 1

f()

return context
"""

TEST_2_EVENT_SOURCE_CODE = """
        context["indent"] = True
        return context
"""

TEST_3_EVENT_SOURCE_CODE = """
            print("badly indented")
        return context
"""

TEST_4_EVENT_SOURCE_CODE = """
context["no return"] = True
"""

TEST_5_EVENT_SOURCE_CODE = """
"wrong return value"
return False
"""

TEST_6_EVENT_SOURCE_CODE = """
if "value" not in context:
    context["created"] = True
    context["value"] = 1
else:
    context["value"] += 1
"""

sample_events_path = "tests/flang/test_files/test_module/sample_events.py"


class EventTestCase(unittest.TestCase):
    def test_create_event_from_text(self):
        event = Event.from_source_code(
            "foo", TEST_1_EVENT_SOURCE_CODE, {"trigger": "deletetion"}
        )
        context = {}
        new_context = event.run(context)
        self.assertEqual(new_context["result"], "success")

    def test_should_deindent_code(self):
        event = Event.from_source_code("foo", TEST_2_EVENT_SOURCE_CODE)
        context = {}
        context = event.run(context)
        self.assertEqual(context["indent"], True)

    def test_create_event_from_filepath(self):
        event = Event.from_path("foo", sample_events_path, "test1")

        context = {}
        event.run(context)
        self.assertEqual(context["result"], "success")


class EventStorageTestCase(unittest.TestCase):
    def test_event_context_persistancy(self):
        event_storage = EventStorage()
        event = Event.from_source_code("foo", TEST_6_EVENT_SOURCE_CODE)

        event_storage.add_event("on-run", 5, event)
        event_storage.add_event("on-run", 5, event)
        event_storage.add_event("on-run", 5, event)

        runner = event_storage.execute_iter("on-run")

        ctx = next(runner)
        self.assertEqual(ctx["value"], 1)
        self.assertEqual(ctx["created"], True)

        ctx = next(runner)
        self.assertEqual(ctx["value"], 2)
        self.assertEqual(ctx["created"], True)

        ctx = next(runner)
        self.assertEqual(ctx["value"], 3)
        self.assertEqual(ctx["created"], True)

    def test_event_execute_all(self):
        event_storage = EventStorage()
        event = Event.from_source_code("foo", TEST_6_EVENT_SOURCE_CODE)

        event_storage.add_event("on_run", 5, event)
        event_storage.add_event("on_run", 5, event)
        event_storage.add_event("on_run", 5, event)

        ctx = event_storage.execute_all("on_run")
        self.assertEqual(ctx["value"], 3)
        self.assertEqual(ctx["created"], True)
