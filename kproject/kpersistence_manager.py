import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Any, Set
import hashlib

from kproject.kevent import KEvent, KEventTypes
from kproject.kmanager import KManager
from kira import KData, KLiteral
from kira.kdata.kliteral import KLiteralType

class DataCorruptionError(Exception):
    """Raised when data loaded from the database is corrupted or in an invalid format."""
    pass

class KPersistenceManager(KManager):
    """
    Handles event sourcing logs and heavy KData isolation.
    Functions entirely in memory for unsaved projects and flushes 
    to a SQLite-backed store upon request.
    """
    def __init__(self, filepath: Optional[str] = None):
        self.__filepath = filepath
        self.__events: List[KEvent] = []
        
        self.__conn: Optional[sqlite3.Connection] = None
        
        # In-Memory Trackers
        self.__unsaved_events: List[KEvent] = []
        self.__unsaved_data: Set[str] = set()
        self.__kdata_cache: Dict[str, KData] = {}

        if self.__filepath:
            self.__conn = sqlite3.connect(self.__filepath)
            self._init_db()
            self._load_all_events_from_db()
            
    def _load_all_events_from_db(self):
        cursor = self.__conn.cursor()
        cursor.execute("SELECT timestamp, author, event_type, target, body FROM events ORDER BY id ASC")
        for row in cursor.fetchall():
            ts, author, evt_type_str, name, body = row
            evt = KEvent(
                author=author,
                timestamp=datetime.fromisoformat(ts),
                type=KEventTypes(evt_type_str),
                target=name,
                body=body
            )
            # evt.event_id is automatically computed in @property
            self.__events.append(evt)

    def get_all_events(self) -> List[KEvent]:
        """Returns all events currently loaded in memory."""
        return self.__events

    def process_event(self, event: KEvent):
        """Standard KManager interface. Appends to event logs."""
        self.__events.append(event)
        self.__unsaved_events.append(event)
        if self.__conn:
            self.save_events()

    def truncate_history(self, event_id: str):
        """
        Removes all events starting from the given event_id (hash) from memory and disk.
        Used for the divergence model in Undo/Redo.
        """
        # 1. Truncate memory
        truncate_idx = None
        for i, evt in enumerate(self.__events):
            if evt.event_id == event_id:
                truncate_idx = i
                break
        
        if truncate_idx is None:
            return

        # 2. Truncate disk
        if self.__conn:
            cursor = self.__conn.cursor()
            # Since we don't have event_id in DB, we find the primary key 'id' 
            # by matching the content of the event at truncate_idx.
            # However, simpler: Get all IDs and pick the one at truncate_idx.
            cursor.execute("SELECT id FROM events ORDER BY id ASC")
            all_db_ids = [row[0] for row in cursor.fetchall()]
            if truncate_idx < len(all_db_ids):
                sql_id = all_db_ids[truncate_idx]
                cursor.execute("DELETE FROM events WHERE id >= ?", (sql_id,))
                self.__conn.commit()

        # 3. Truncate memory list
        self.__events = self.__events[:truncate_idx]
        self.__unsaved_events = [] 
        
    def cache_data(self, data: KData):
        """Caches data in memory so it doesn't need to be deserialized repeatedly."""
        name = data.name
        self.__kdata_cache[name] = data
        self.__unsaved_data.add(name)
        if self.__conn:
            self.save_data()
        
    def get_data(self, name: str) -> Optional[KData]:
        """
        Retrieves KData. Checks memory cache first, then disk if available.
        """
        if name in self.__kdata_cache:
            return self.__kdata_cache[name]
            
        assert self.__conn is not None, f"Cannot load KData '{name}' from disk without active connection."
        
        data = self._load_data_from_disk(name)
        assert data is not None, f"get_data: Expected KData, got None for name {name}"
        assert isinstance(data, KData), f"get_data: Expected KData, got {type(data)} for name {name}"
        return data

    def _init_db(self):
        """Initializes the SQLite schema."""
        cursor = self.__conn.cursor()
        
        # Events table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            author TEXT,
            event_type TEXT,
            target TEXT,
            body TEXT
        )
        ''')
        
        # Data Metadata / Simple Data Log
        # content is equal to blob_id for complex data
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS kdata_storage (
            name TEXT PRIMARY KEY,
            data_type TEXT,
            string_value TEXT,
            content TEXT 
        )
        ''')
        
        # Table Blob Storage
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ktable_storage (
            blob_id TEXT PRIMARY KEY,
            table_type_enum TEXT,
            content BLOB
        )
        ''')
        
        self.__conn.commit()

    def save_project(self, filepath: Optional[str] = None):
        """
        Flushes all unsaved events and data to the SQLite database.
        """
        if filepath:
            if self.__filepath and self.__filepath != filepath:
                raise ValueError("Project is already associated with a filepath. Saving to multiple places is not supported.")
            if not self.__conn:
                self.__filepath = filepath
                self.__conn = sqlite3.connect(self.__filepath)
                self._init_db()
            
        assert self.__conn is not None, "Cannot save project: No active database connection."
            
        self.save_events()
        self.save_data()

    def save_events(self):
        """Flushes all unsaved events to the SQLite database."""
        if not self.__conn or not self.__unsaved_events:
            return
            
        cursor = self.__conn.cursor()
                event.timestamp.isoformat(),
                event.author,
                event.type.value,
                event.target,
                event.body
            ))
        self.__conn.commit()
        self.__unsaved_events.clear()

    def save_data(self):
        """Flushes all unsaved data to the SQLite database."""
        if not self.__conn or not self.__unsaved_data:
            return

        cursor = self.__conn.cursor()
        for name in self.__unsaved_data:
            kdata = self.__kdata_cache[name]
            
            if isinstance(kdata.value, KLiteral):
                lit_type = kdata.value.lit_type
                
                if lit_type in (KLiteralType.DATE, KLiteralType.DATETIME):
                    string_val = kdata.value.value.isoformat()
                else:
                    string_val = str(kdata.value.value)
                    
                data_type_str = "KLiteral"
                json_string = json.dumps({"lit_type": lit_type.name, "value": string_val})
                
                # Store scalar/literals cleanly
                cursor.execute('''
                INSERT OR REPLACE INTO kdata_storage (name, data_type, string_value, content)
                VALUES (?, ?, ?, NULL)
                ''', (name, data_type_str, json_string))
            else:
                # TODO: implement serialization for all data types that are not KLiteral
                raise NotImplementedError(f"Serialization for non-KLiteral data types is not implemented yet. Found: {type(kdata.value)}")
            
        self.__conn.commit()
        self.__unsaved_data.clear()

    def _load_data_from_disk(self, name: str) -> KData:
        """Loads data from the SQLite database."""
        # TODO Refactor: if data is not available return KData(None, KErrorMissingData))

        cursor = self.__conn.cursor()
        cursor.execute('SELECT name, data_type, string_value, blob_id FROM kdata_storage WHERE name=?', (name,))
        row = cursor.fetchone()

        assert row, f"_load_data_from_disk: No data available for name: {name}"

        value = None
        _, data_type, string_val, content = row
        if data_type == "KLiteral":
            try:
                parsed = json.loads(string_val)
                if isinstance(parsed, dict) and "value" in parsed and "lit_type" in parsed:
                    val_str = parsed["value"]
                    lit_type_name = parsed["lit_type"]
                    lit_type = KLiteralType[lit_type_name]
                else:
                    raise DataCorruptionError(f"Missing 'value' or 'lit_type' field in KLiteral JSON data for name '{name}'.")
            except json.JSONDecodeError as e:
                raise DataCorruptionError(f"Failed to parse KLiteral JSON data for name '{name}': {e}")

            if lit_type == KLiteralType.INTEGER:
                val = int(val_str)
            elif lit_type == KLiteralType.NUMBER:
                val = float(val_str)
            elif lit_type == KLiteralType.BOOLEAN:
                val = val_str.lower() == 'true'
            elif lit_type == KLiteralType.DATE:
                val = datetime.fromisoformat(val_str).date()
            elif lit_type == KLiteralType.DATETIME:
                val = datetime.fromisoformat(val_str)
            else:
                val = val_str

            value = KLiteral(val, lit_type)
        elif data_type == "KTable":
            cursor.execute('SELECT blob_id, table_type_enum, content FROM ktable_storage WHERE blob_id=?', (content,))
            # blob_row = cursor.fetchone()
            # TODO: implement deserialization for KTables
            raise NotImplementedError(f"Deserialization for data type {data_type} is not implemented yet.")
        else:
            # TODO: implement deserialization for all data types that are not KLiteral or KTable
            raise NotImplementedError(f"Deserialization for data type {data_type} is not implemented yet.")

        assert value is not None, f"_load_data_from_disk: Deserialized value is None for name: {name}"
        data = KData(name, value)

        self.__kdata_cache[name] = data
        return data
        
    def close(self):
        """Closes the underlying SQLite connection if it exists."""
        if self.__conn:
            self.__conn.close()
            self.__conn = None
