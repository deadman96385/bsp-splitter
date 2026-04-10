import unittest
import subprocess
from unittest.mock import patch, mock_open

# Because we are testing in the same dir
import splitter

class TestSplitter(unittest.TestCase):

    @patch('splitter.time.sleep')
    def test_execute_with_retry_success(self, mock_sleep):
        """Test that a succeeding function does not trigger sleep retries."""
        def dummy_func(a, b):
            return a + b
            
        result = splitter.execute_with_retry(dummy_func, 2, 3)
        self.assertEqual(result, 5)
        mock_sleep.assert_not_called()

    @patch('splitter.time.sleep')
    def test_execute_with_retry_recovers(self, mock_sleep):
        """Test that a function failing initially but succeeding later triggers sleep appropriately."""
        calls = [0]
        def dummy_func():
            calls[0] += 1
            if calls[0] < 3:
                raise subprocess.CalledProcessError(1, 'cmd')
            return "success"
            
        # It should fail twice, sleep twice, and succeed on the third attempt
        result = splitter.execute_with_retry(dummy_func, retries=5, delay=10)
        self.assertEqual(result, "success")
        self.assertEqual(calls[0], 3)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_called_with(10)

    @patch('splitter.time.sleep')
    def test_execute_with_retry_fails(self, mock_sleep):
        """Test that an unrecoverable failure raises the exception and stops retrying."""
        def dummy_func():
            raise subprocess.CalledProcessError(1, 'cmd')
            
        with self.assertRaises(subprocess.CalledProcessError):
            splitter.execute_with_retry(dummy_func, retries=4, delay=1)
            
        # If it retries 4 times, it attempts attempt 0, 1, 2, 3. It sleeps after 0, 1, 2. (3 times)
        self.assertEqual(mock_sleep.call_count, 3)

    @patch('builtins.open', new_callable=mock_open, read_data='{"modified": ["projectA", "projectB"], "no_changes": ["projectC"], "failed": ["projectD"]}')
    def test_get_skipped_projects(self, mock_file):
        """Test that getting skipped projects perfectly joins the 'modified' and 'no_changes' arrays."""
        skipped = splitter.get_skipped_projects("dummy.json")
        self.assertIn("projectA", skipped)
        self.assertIn("projectB", skipped)
        self.assertIn("projectC", skipped)
        self.assertNotIn("projectD", skipped)
        self.assertEqual(len(skipped), 3)

    @patch('builtins.open', side_effect=Exception("Simulated IO Error"))
    def test_get_skipped_projects_failure(self, mock_file):
        """Test that skipping project crashes/exits when file doesn't exist to prevent data loss."""
        with self.assertRaises(SystemExit):
            splitter.get_skipped_projects("dummy.json")

if __name__ == '__main__':
    unittest.main()
