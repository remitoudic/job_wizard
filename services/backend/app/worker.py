import asyncio
import logging
import os
from temporalio.worker import Worker, UnsandboxedWorkflowRunner
from app.core.temporal import get_temporal_client
from app.services.cover_letter.workflows import CoverLetterWorkflow
from app.services.cover_letter import activities

# Minimal logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    # Connect to Temporal
    logger.info("Connecting to Temporal...")
    client = await get_temporal_client()
    
    # Run the worker with explicit UnsandboxedWorkflowRunner
    worker = Worker(
        client,
        task_queue="cover-letter-tasks",
        workflows=[CoverLetterWorkflow],
        activities=[
            activities.extract_contact_info,
            activities.generate_text_race,
            activities.render_pdf,
            activities.backup_pdf,
            activities.notify_status
        ],
        workflow_runner=UnsandboxedWorkflowRunner(),
    )
    
    logger.info("Temporal Worker started (Explicitly Unsandboxed)")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())
