import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the scripts directory to the path so we can import the module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.verify_memgraph_connection import verify_memgraph_connection

class TestVerifyMemgraphConnection(unittest.TestCase):
    
    @patch('mgclient.connect')
    def test_successful_connection(self, mock_connect):
        # Set up mocks
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["Connection successful!"]
        
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Call the function
        success, error = verify_memgraph_connection(max_retries=1)
        
        # Assertions
        self.assertTrue(success)
        self.assertIsNone(error)
        mock_connect.assert_called_once()
        self.assertEqual(mock_cursor.execute.call_count, 3)
        
    @patch('mgclient.connect')
    def test_failed_connection(self, mock_connect):
        # Set up mocks
        mock_connect.side_effect = Exception("Connection error")
        
        # Call the function
        success, error = verify_memgraph_connection(max_retries=1, retry_delay=0)
        
        # Assertions
        self.assertFalse(success)
        self.assertIn("Connection error", error)
        mock_connect.assert_called_once()

if __name__ == '__main__':
    unittest.main()
