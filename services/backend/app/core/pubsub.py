import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Set
import psycopg
from psycopg import sql
from app.core.config import settings

logger = logging.getLogger(__name__)

class PubSubManager:
    """
    Manages a single PostgreSQL connection for LISTEN/NOTIFY.
    Distributes events to all active SSE subscribers.
    """
    
    def __init__(self):
        self.channel = "job_wizard_notifications"
        self._listeners: Set[asyncio.Queue] = set()
        self._conn: Optional[psycopg.AsyncConnection] = None
        self._task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start the background listener task."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._listen_loop())
        logger.info(f"PubSubManager started listening on channel: {self.channel}")

    async def stop(self):
        """Stop the background listener task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        if self._conn:
            await self._conn.close()
        
        logger.info("PubSubManager stopped")

    async def _get_conn(self) -> psycopg.AsyncConnection:
        """Create a new async connection."""
        # Convert DATABASE_URL if it has the +psycopg or +psycopg2 prefix
        # psycopg.connect prefers standard postgresql://
        url = settings.DATABASE_URL
        if "+psycopg2" in url:
            url = url.replace("+psycopg2", "")
        elif "+psycopg" in url:
            url = url.replace("+psycopg", "")
            
        return await psycopg.AsyncConnection.connect(
            url, 
            autocommit=True,
            prepare_threshold=None # Recommended for persistent connections
        )

    async def _listen_loop(self):
        """Infinite loop to handle incoming NOTIFY events."""
        while self._running:
            try:
                self._conn = await self._get_conn()
                async with self._conn.cursor() as cur:
                    await cur.execute(sql.SQL("LISTEN {channel}").format(
                        channel=sql.Identifier(self.channel)
                    ))
                    
                    logger.info(f"Postgres LISTEN established on {self.channel}")
                    
                    async for notify in self._conn.notifies():
                        try:
                            payload = json.loads(notify.payload)
                            # Fan out to all queues
                            for queue in list(self._listeners): # Use list to avoid mutation during iteration
                                await queue.put(payload)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode NOTIFY payload: {notify.payload}")
                        except Exception as e:
                            logger.error(f"Error distributing notification: {e}")
                            
            except (psycopg.OperationalError, Exception) as e:
                logger.error(f"PubSub connection error: {e}. Retrying in 5s...")
                if self._conn:
                    try:
                        await self._conn.close()
                    except:
                        pass
                await asyncio.sleep(5)

    async def subscribe(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Subscribe to the event stream."""
        queue = asyncio.Queue()
        self._listeners.add(queue)
        try:
            while True:
                # Yield messages as they arrive
                yield await queue.get()
        finally:
            self._listeners.remove(queue)

    async def notify(self, payload: Dict[str, Any]):
        """Helper to send a NOTIFY event."""
        try:
            async with await self._get_conn() as conn:
                await conn.execute(
                    sql.SQL("NOTIFY {channel}, {payload}").format(
                        channel=sql.Identifier(self.channel),
                        payload=sql.Literal(json.dumps(payload))
                    )
                )
        except Exception as e:
            logger.error(f"Failed to send NOTIFY: {e}")

# Singleton instance
pubsub_manager = PubSubManager()
