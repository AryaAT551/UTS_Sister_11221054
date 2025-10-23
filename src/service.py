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
        if not self._processing:
            self._processing = True
            self._consumer_task = asyncio.create_task(self._process_queue())
            logger.info("✅ EventService started.")

    async def stop(self):
        if self._processing:
            self._processing = False
            await self._queue.join()
            if self._consumer_task:
                self._consumer_task.cancel()
                try:
                    await self._consumer_task
                except asyncio.CancelledError:
                    logger.info("🛑 Consumer task cancelled.")
            logger.info("🚦 EventService stopped.")

    async def process_events(self, events: List[Event]):
        """Add events to queue and process"""
        if not self._processing:
            await self.start()

        results = {"processed": 0, "duplicates": 0}

        for event in events:
            await self._queue.put(event)

        # Process immediately
        while not self._queue.empty():
            event = await self._queue.get()
            is_duplicate = await self.store.is_duplicate(event)
            if not is_duplicate:
                await self.store.store_event(event)
                results["processed"] += 1
            else:
                await self.store.store_event(event)  # update stats for duplicate
                results["duplicates"] += 1
            self._queue.task_done()

        return results

    async def _process_queue(self):
        while self._processing:
            try:
                event = await self._queue.get()
                await self.store.store_event(event)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Queue processing error: {str(e)}")

    async def get_events(self, topic: str = None):
        return await self.store.get_events(topic)

    async def get_stats(self):
        return await self.store.get_stats()
