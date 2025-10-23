import aiosqlite
import json
import logging
from datetime import datetime
from .models import Event

logger = logging.getLogger(__name__)

class SQLiteEventStore:
    """Asynchronous SQLite store for event-driven systems."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.stats = {
            "received": 0,
            "unique_processed": 0,
            "duplicate_dropped": 0,
            "topics": set()
        }

    async def initialize(self):
        """Initialize database schema if not exists."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    topic TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    UNIQUE(topic, event_id)
                )
            """)
            await db.commit()
        logger.info(f"🗄️ Database initialized at: {self.db_path}")

    async def is_duplicate(self, event: Event) -> bool:
        """Check if event already exists in the database."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT 1 FROM events WHERE topic = ? AND event_id = ?",
                (event.topic, event.event_id)
            )
            result = await cursor.fetchone()
            await cursor.close()
            return result is not None

    async def store_event(self, event: Event) -> bool:
        """Store event into the database, skip duplicates."""
        self.stats["received"] += 1

        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO events (topic, event_id, timestamp, source, payload)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        event.topic,
                        event.event_id,
                        event.timestamp.isoformat(),
                        event.source,
                        json.dumps(event.payload)
                    )
                )
                await db.commit()

                self.stats["unique_processed"] += 1
                self.stats["topics"].add(event.topic)
                logger.info(f"✅ Event stored: {event.topic}:{event.event_id}")
                return True

        except aiosqlite.IntegrityError:
            # Duplicate event detected
            self.stats["duplicate_dropped"] += 1
            logger.warning(f"⚠️ Duplicate event ignored: {event.topic}:{event.event_id}")
            return False

        except Exception as e:
            logger.error(f"❌ Error storing event: {str(e)}")
            return False

    async def get_events(self, topic: str = None):
        """Retrieve all events, optionally filtered by topic."""
        async with aiosqlite.connect(self.db_path) as db:
            if topic:
                query = "SELECT * FROM events WHERE topic = ?"
                params = (topic,)
            else:
                query = "SELECT * FROM events"
                params = ()

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            await cursor.close()

            events = [
                {
                    "topic": row[0],
                    "event_id": row[1],
                    "timestamp": row[2],
                    "source": row[3],
                    "payload": json.loads(row[4])
                }
                for row in rows
            ]
            logger.debug(f"📤 Retrieved {len(events)} events from DB.")
            return events

    async def get_stats(self):
        """Return runtime statistics."""
        stats_copy = {
            "received": self.stats["received"],
            "unique_processed": self.stats["unique_processed"],
            "duplicate_dropped": self.stats["duplicate_dropped"],
            "topics": sorted(self.stats["topics"])
        }
        logger.debug(f"📊 Stats: {stats_copy}")
        return stats_copy
