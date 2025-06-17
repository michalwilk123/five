import unittest
import os
import shutil
from core.project_config import FiveProjectConfig
from utils.project_search import FiveProjectSearchEngine
from tests.utils import FiveChatbotControllerMock, FiveProjectTreeControllerMock
import tempfile

class TestFiveProjectSearchEngine(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the project and index
        self.test_dir = tempfile.mkdtemp()
        self.mock_project_location = os.path.join(self.test_dir, "mock_project")
        os.makedirs(self.mock_project_location, exist_ok=True)

        # Create a dummy config file
        self.dummy_config_path = os.path.join(self.test_dir, "dummy_config.toml")
        with open(self.dummy_config_path, "w") as f:
            f.write("""
[settings]
rules = ""

[[settings.objects]]
id = "test_object"
structure = "src/{name}.py"
globs = ["*.py"]
description = "A test object for searching."
examples = ["find all functions related to user authentication"]

            """)


        self.config = FiveProjectConfig(config_path=self.dummy_config_path)
        
        # Correctly initialize mock objects
        self.mock_tree_controller = FiveProjectTreeControllerMock(project_location=self.mock_project_location)
        self.mock_chatbot_controller = FiveChatbotControllerMock()

        self.search_engine = FiveProjectSearchEngine(
            config=self.config,
            project_tree_controller=self.mock_tree_controller,
            chatbot_controller=self.mock_chatbot_controller,
            overrides=True,
        )
        
        # Ensure .five directory is within the temp mock project location for cleanup
        self.five_dir_path = os.path.join(self.mock_project_location, ".five")


    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_index_code_object_and_search(self):
        object_name = "test_object"
        test_object_config = self.config.get_object_by_name(object_name)
        self.assertIsNotNone(test_object_config, "Test object config should not be None")

        # 1. Setup mock responses and data
        self.mock_tree_controller.passages_data = [
            ("dummy_file1.py", "1: def hello_world():\n2:    print(\"Hello, World!\")\n3:    # This is a test comment"),
            ("dummy_file2.py", "1: class Greeter:\n2:    def greet(self, name):\n3:        return f\"Hello, {name}!\"")
        ]

        # Simulate chatbot response for CREATE_INDEX_PROMPT
        # Each item in the list is (text_content, filepath, start_line, end_line)
        self.mock_chatbot_controller.create_index_json_response = [
            ("hello_world function", "dummy_file1.py", 1, 2),
            ("test comment about world", "dummy_file1.py", 3, 3),
            ("Greeter class", "dummy_file2.py", 1, 3),
        ]
        
        # 2. Index the code object
        passages_bm25_data = self.search_engine.index_code_object(
            description=test_object_config.description,
            object_name=object_name,
            passages_input=self.mock_tree_controller.get_passages([]), # globs are ignored by mock
        )
        
        self.assertTrue(len(passages_bm25_data) > 0, "BM25 data should be generated")
        
        # Check metadata in one of the passages
        self.assertIn("metadata", passages_bm25_data[0])
        self.assertIn("filepath", passages_bm25_data[0]["metadata"])
        self.assertIn("commit_hash", passages_bm25_data[0]["metadata"]) # Checks if get_last_commit_hash was called

        # 3. Generate the BM25 index on disk
        self.search_engine.generate_bm25_index(object_name, passages_bm25_data)
        
        index_path = os.path.join(self.five_dir_path, object_name)
        self.assertTrue(os.path.exists(index_path), f"Index directory should be created at {index_path}")
        self.assertTrue(os.path.exists(os.path.join(index_path, "corpus.jsonl")), "corpus.jsonl should exist")
        self.assertTrue(os.path.exists(os.path.join(index_path, "model.npz")), "model.npz should exist")

        # 4. Test the search functionality
        # Simulate chatbot response for SEARCH_INDEX_PROMPT
        self.mock_chatbot_controller.search_index_string_response = "hello world"
        
        user_instruction = "find code about hello world"
        search_results = self.search_engine.get_project_context(object_name, user_instruction)
        
        self.assertIsNotNone(search_results, "Search results should not be None")
        self.assertTrue(len(search_results) > 0, "Search should return some results")
        
        # Check the content of the search results
        found_relevant_passage = False
        for result in search_results:
            self.assertIn("text", result)
            self.assertIn("metadata", result)
            if "hello_world" in result["text"] or "world" in result["text"]:
                 found_relevant_passage = True
                 self.assertEqual(result["metadata"]["filepath"], "dummy_file1.py")

        self.assertTrue(found_relevant_passage, "Search results should contain relevant passages about 'hello world'")

if __name__ == '__main__':
    unittest.main() 