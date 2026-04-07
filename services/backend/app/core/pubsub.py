import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Set, Optional
import psycopg
from psycopg import sql
from app.core.config import settings
import logfire

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
        """Helper to send a NOTIFY event. Also persists the status to the database."""
        job_id = payload.get("job_id")
        status = payload.get("status")
        
        with logfire.span("PubSub Notify: {status}", status=status, job_id=job_id):
            # 1. Persist to Database for SSE Replay/Fallback
            if job_id and status:
                try:
                    from sqlmodel import Session
                    from app.core.db import engine
                    from database_pkg.models.job_status import JobStatus
                    from datetime import datetime
                    
                    with Session(engine) as session:
                        # Try to get existing job status or create new one
                        job_status = session.get(JobStatus, job_id)
                        if not job_status:
                            job_status = JobStatus(job_id=job_id, status=status, payload=payload)
                        else:
                            job_status.status = status
                            job_status.payload = payload
                            job_status.updated_at = datetime.utcnow()
                        
                        session.add(job_status)
                        session.commit()
                except Exception as db_err:
                    logger.error(f"Failed to persist job status for {job_id}: {db_err}")

            # 2. Send Real-time Notification
            try:
                async with await self._get_conn() as conn:
                    await conn.execute(
                        sql.SQL("NOTIFY {channel}, {payload}").format(
                            channel=sql.Identifier(self.channel),
                            payload=sql.Literal(json.dumps(payload))
                        )
                    )
                
                # 3. Also notify ephemeral listeners
                for queue in self._listeners:
                    await queue.put(payload)
            except Exception as e:
                logger.error(f"Notification error for {job_id}: {e}")

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the latest status for a job from the database."""
        try:
            from sqlmodel import Session, select
            from app.core.db import engine
            from database_pkg.models.job_status import JobStatus
            
            with Session(engine) as session:
                statement = select(JobStatus).where(JobStatus.job_id == job_id)
                result = session.exec(statement).first()
                if result:
                    return {
                        "job_id": result.job_id,
                        "status": result.status,
                        "payload": result.payload or {}
                    }
        except Exception as e:
            logger.error(f"Error fetching job status for {job_id}: {e}")
        return None

# Singleton instance
pubsub_manager = PubSubManager()
