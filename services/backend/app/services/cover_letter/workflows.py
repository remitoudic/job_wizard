from datetime import timedelta
from temporalio import workflow
from typing import Dict, Any

@workflow.defn(name="CoverLetterWorkflow")
class CoverLetterWorkflow:
    @workflow.run
    async def run(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        # Fallback to workflow ID if job_id is missing in payload
        job_id = request_data.get("job_id") or workflow.info().workflow_id
        # Ensure it's in the dict for downstream activities
        request_data["job_id"] = job_id
        
        # 1. Extraction phase
        if request_data.get("context_text"):
            await workflow.execute_activity(
                "notify_status",
                {
                    "job_id": job_id,
                    "status": "extracting",
                    "message": "Analyzing your profile context..."
                },
                start_to_close_timeout=timedelta(seconds=10),
            )
            
            contact_info = await workflow.execute_activity(
                "extract_contact_info",
                request_data["context_text"],
                start_to_close_timeout=timedelta(minutes=2),
            )
            
            await workflow.execute_activity(
                "notify_status",
                {
                    "job_id": job_id,
                    "status": "extracted",
                    "message": "Profile analysis complete.",
                    "contact_info": contact_info
                },
                start_to_close_timeout=timedelta(seconds=10),
            )
            # Update request data for generation if needed
            request_data["contact_info"] = contact_info

        # 2. Generation phase
        generation_result = await workflow.execute_activity(
            "generate_text_race",
            request_data,
            start_to_close_timeout=timedelta(minutes=5),
        )

        return generation_result
