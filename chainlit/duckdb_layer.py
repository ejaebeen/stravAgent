import duckdb
import json
from typing import Optional, List, Dict, Any
import chainlit.data as cl_data
from chainlit.types import ThreadDict, Pagination, PaginatedResponse, PageInfo

class DuckDBDataLayer(cl_data.BaseDataLayer):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with duckdb.connect(self.db_path) as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS cl_threads (
                    id TEXT PRIMARY KEY,
                    createdAt TEXT,
                    name TEXT,
                    userId TEXT,
                    userIdentifier TEXT,
                    tags TEXT[],
                    metadata TEXT
                );
                CREATE TABLE IF NOT EXISTS cl_steps (
                    id TEXT PRIMARY KEY,
                    threadId TEXT,
                    parentId TEXT,
                    type TEXT,
                    name TEXT,
                    createdAt TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    input TEXT,
                    output TEXT,
                    metadata TEXT,
                    isError BOOLEAN,
                    showInput TEXT,
                    language TEXT,
                    indent INT
                );
                CREATE TABLE IF NOT EXISTS cl_users (
                    id TEXT PRIMARY KEY,
                    identifier TEXT,
                    metadata TEXT,
                    createdAt TEXT
                );
                CREATE TABLE IF NOT EXISTS cl_elements (
                    id TEXT PRIMARY KEY,
                    threadId TEXT,
                    type TEXT,
                    url TEXT,
                    chainlitKey TEXT,
                    name TEXT,
                    display TEXT,
                    size TEXT,
                    language TEXT,
                    forId TEXT,
                    mime TEXT
                );
                CREATE TABLE IF NOT EXISTS cl_feedback (
                    id TEXT PRIMARY KEY,
                    forId TEXT,
                    value INT,
                    comment TEXT
                );
            """)

    async def list_threads(self, pagination: Pagination, filter: Any) -> PaginatedResponse[ThreadDict]:
        limit = pagination.first or 20
        
        with duckdb.connect(self.db_path) as con:
            # Fetch threads ordered by creation date
            rows = con.execute(f"""
                SELECT id, createdAt, name, userId, userIdentifier, tags, metadata 
                FROM cl_threads 
                ORDER BY createdAt DESC 
                LIMIT {limit}
            """).fetchall()
            
        threads = []
        for row in rows:
            threads.append({
                "id": row[0],
                "createdAt": row[1],
                "name": row[2],
                "userId": row[3],
                "userIdentifier": row[4],
                "tags": row[5],
                "metadata": json.loads(row[6]) if row[6] else None
            })
            
        return PaginatedResponse(data=threads, pageInfo=PageInfo(hasNextPage=False, endCursor=None))

    async def get_thread(self, thread_id: str) -> Optional[ThreadDict]:
        with duckdb.connect(self.db_path) as con:
            thread_row = con.execute("SELECT * FROM cl_threads WHERE id = ?", [thread_id]).fetchone()
            if not thread_row:
                return None
            
            steps_rows = con.execute("SELECT * FROM cl_steps WHERE threadId = ? ORDER BY createdAt ASC", [thread_id]).fetchall()
        
        steps = []
        for row in steps_rows:
            steps.append({
                "id": row[0],
                "threadId": row[1],
                "parentId": row[2],
                "type": row[3],
                "name": row[4],
                "createdAt": row[5],
                "start": row[6],
                "end": row[7],
                "input": row[8],
                "output": row[9],
                "metadata": json.loads(row[10]) if row[10] else {},
                "isError": row[11],
                "showInput": row[12],
                "language": row[13],
                "indent": row[14]
            })
            
        return {
            "id": thread_row[0],
            "createdAt": thread_row[1],
            "name": thread_row[2],
            "userId": thread_row[3],
            "userIdentifier": thread_row[4],
            "tags": thread_row[5],
            "metadata": json.loads(thread_row[6]) if thread_row[6] else None,
            "steps": steps
        }

    async def create_thread(self, thread_dict: ThreadDict):
        with duckdb.connect(self.db_path) as con:
            con.execute("INSERT INTO cl_threads VALUES (?, ?, ?, ?, ?, ?, ?)", (
                thread_dict.get("id"), thread_dict.get("createdAt"), thread_dict.get("name"),
                thread_dict.get("userId"), thread_dict.get("userIdentifier"), thread_dict.get("tags"),
                json.dumps(thread_dict.get("metadata"))
            ))

    async def update_thread(self, thread_id: str, name: Optional[str] = None, user_id: Optional[str] = None, metadata: Optional[Dict] = None, tags: Optional[List[str]] = None):
        if name:
            with duckdb.connect(self.db_path) as con:
                con.execute("UPDATE cl_threads SET name = ? WHERE id = ?", (name, thread_id))

    async def delete_thread(self, thread_id: str):
        with duckdb.connect(self.db_path) as con:
            con.execute("DELETE FROM cl_threads WHERE id = ?", [thread_id])
            con.execute("DELETE FROM cl_steps WHERE threadId = ?", [thread_id])

    async def create_step(self, step_dict: Dict[str, Any]):
        with duckdb.connect(self.db_path) as con:
            con.execute("INSERT INTO cl_steps VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                step_dict.get("id"), step_dict.get("threadId"), step_dict.get("parentId"), step_dict.get("type"),
                step_dict.get("name"), step_dict.get("createdAt"), step_dict.get("start"), step_dict.get("end"),
                step_dict.get("input"), step_dict.get("output"), json.dumps(step_dict.get("metadata")),
                step_dict.get("isError"), str(step_dict.get("showInput")), step_dict.get("language"), step_dict.get("indent")
            ))

    async def update_step(self, step_dict: Dict[str, Any]):
        with duckdb.connect(self.db_path) as con:
            con.execute("""
                UPDATE cl_steps SET output = ?, end_time = ?, metadata = ?, isError = ?, input = ? WHERE id = ?
            """, (
                step_dict.get("output"), step_dict.get("end"), json.dumps(step_dict.get("metadata")),
                step_dict.get("isError"), step_dict.get("input"), step_dict.get("id")
            ))

    async def delete_step(self, step_id: str):
        with duckdb.connect(self.db_path) as con:
            con.execute("DELETE FROM cl_steps WHERE id = ?", [step_id])

    async def get_user(self, identifier: str) -> Optional[Dict[str, Any]]:
        with duckdb.connect(self.db_path) as con:
            row = con.execute("SELECT * FROM cl_users WHERE identifier = ?", [identifier]).fetchone()
            if row:
                return {"id": row[0], "identifier": row[1], "metadata": json.loads(row[2]) if row[2] else {}, "createdAt": row[3]}
        return None

    async def create_user(self, user: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with duckdb.connect(self.db_path) as con:
            con.execute("INSERT INTO cl_users VALUES (?, ?, ?, ?)", 
                        (user.get("id"), user.get("identifier"), json.dumps(user.get("metadata")), user.get("createdAt")))
        return user

    async def create_element(self, element: Dict[str, Any]):
        with duckdb.connect(self.db_path) as con:
            con.execute("INSERT INTO cl_elements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (element.get("id"), element.get("threadId"), element.get("type"), element.get("url"),
                         element.get("chainlitKey"), element.get("name"), element.get("display"), element.get("size"),
                         element.get("language"), element.get("forId"), element.get("mime")))

    async def get_element(self, thread_id: str, element_id: str) -> Optional[Dict[str, Any]]:
        with duckdb.connect(self.db_path) as con:
            row = con.execute("SELECT * FROM cl_elements WHERE id = ?", [element_id]).fetchone()
            if row:
                return {
                    "id": row[0], "threadId": row[1], "type": row[2], "url": row[3], "chainlitKey": row[4],
                    "name": row[5], "display": row[6], "size": row[7], "language": row[8], "forId": row[9], "mime": row[10]
                }
        return None

    async def delete_element(self, element_id: str):
        with duckdb.connect(self.db_path) as con:
            con.execute("DELETE FROM cl_elements WHERE id = ?", [element_id])

    async def upsert_feedback(self, feedback: Dict[str, Any]) -> str:
        with duckdb.connect(self.db_path) as con:
            exists = con.execute("SELECT 1 FROM cl_feedback WHERE id = ?", [feedback.get("id")]).fetchone()
            if exists:
                con.execute("UPDATE cl_feedback SET value = ?, comment = ? WHERE id = ?",
                            (feedback.get("value"), feedback.get("comment"), feedback.get("id")))
            else:
                con.execute("INSERT INTO cl_feedback VALUES (?, ?, ?, ?)",
                            (feedback.get("id"), feedback.get("forId"), feedback.get("value"), feedback.get("comment")))
        return feedback.get("id")

    async def delete_feedback(self, feedback_id: str):
         with duckdb.connect(self.db_path) as con:
            con.execute("DELETE FROM cl_feedback WHERE id = ?", [feedback_id])
            
    async def get_thread_author(self, thread_id: str) -> str:
        with duckdb.connect(self.db_path) as con:
            res = con.execute("SELECT userIdentifier FROM cl_threads WHERE id = ?", [thread_id]).fetchone()
            return res[0] if res else ""
    
    async def get_favorite_steps(self, user_identifier: str) -> List[Dict[str, Any]]:
        # Return empty list for now as we haven't implemented favorites logic
        return []

    async def build_debug_url(self) -> str:
        return ""

    async def close(self):
        pass