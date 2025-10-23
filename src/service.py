from .models import Event
from .store import SQLiteEventStore
from typing import List
import asyncio
import logging

logger = logging.getLogger(__name__)

class EventService:
    def __init__(self, store: SQLiteEventStore):
        self.store = store
        self._queue = asyncio.Queue()
        self._consumer_task = None
        self._processing = False

    async def start(self):
        """Start the event processing"""
        if not self._processing:
            self._processing = True
            logger.info("✅ EventService started.")
            self._consumer_task = asyncio.create_task(self._process_queue())

    async def stop(self):
        """Stop the event processing"""
        if self._processing:
            self._processing = False
            logger.info("🕓 Waiting for remaining events to be processed...")
            await self._queue.join()  # Tunggu semua event di queue selesai diproses
            
            if self._consumer_task:
                self._consumer_task.cancel()
                try:
                    await self._consumer_task
                except asyncio.CancelledError:
                    logger.info("🛑 Consumer task cancelled gracefully.")

            logger.info("🚦 EventService stopped.")

    async def process_events(self, events: List[Event]):
        """Add events to the processing queue"""
        if not self._processing:
            await self.start()

        for event in events:
            await self._queue.put(event)
            logger.debug(f"📩 Event queued: {event.topic}:{event.event_id}")
        
        logger.info(f"📦 {len(events)} events added to processing queue.")
        return {"processed": len(events)}

    async def _process_queue(self):
        """Process events from the queue"""
        while self._processing:
            try:
                event = await self._queue.get()
                logger.debug(f"⚙️ Processing event: {event.topic}:{event.event_id}")

                for attempt in range(3):  # maksimal 3 kali retry
                    try:
                        is_duplicate = await self.store.is_duplicate(event)
                        if not is_duplicate:
                            await self.store.store_event(event)
                            logger.info(f"✅ Event stored: {event.topic}:{event.event_id}")
                        else:
                            logger.info(f"⚠️ Duplicate event skipped: {event.topic}:{event.event_id}")
                        break  # keluar dari retry loop jika berhasil
                    except Exception as e:
                        logger.error(f"❌ Error storing event (attempt {attempt+1}): {str(e)}")
                        await asyncio.sleep(0.5)

                self._queue.task_done()

            except asyncio.CancelledError:
                logger.info("🛑 Queue processing cancelled.")
                break
            except Exception as e:
                logger.error(f"🔥 Queue processing error: {str(e)}")

    async def get_events(self, topic: str = None) -> List[Event]:
        """Retrieve processed events"""
        logger.debug(f"📤 Retrieving events for topic: {topic or 'all'}")
        return await self.store.get_events(topic)

    async def get_stats(self) -> dict:
        """Get current statistics"""
        stats = await self.store.get_stats()
        logger.debug(f"📊 Current stats: {stats}")
        return stats
