import os
import duckdb
import uuid
from datetime import datetime

class InteractionLogger:
    def __init__(self, db_path=None):
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = os.getenv("DUCKDB_PATH", "interactions.duckdb")
        self._init_db()

    def _init_db(self):
        """Initialize the database table if it doesn't exist."""
        with duckdb.connect(self.db_path) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS interactions (
                    id VARCHAR,
                    session_id VARCHAR,
                    role VARCHAR,
                    content VARCHAR,
                    timestamp TIMESTAMP
                )
            """)

    def log(self, session_id: str, role: str, content: str):
        """
        Log an interaction to the database.
        
        Args:
            session_id: Unique identifier for the chat session.
            role: The role of the speaker ('user' or 'assistant').
            content: The text content of the message.
        """
        if not content:
            return
            
        with duckdb.connect(self.db_path) as con:
            con.execute("""
                INSERT INTO interactions (id, session_id, role, content, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), session_id, role, content, datetime.now()))
