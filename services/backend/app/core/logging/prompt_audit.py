import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from app.core.config import settings

class PromptAuditLogger:
    """
    Logs raw LLM outputs to local files when validation fails.
    Useful for debugging hallucinations and refining prompts.
    """
    
    def __init__(self):
        self.enabled = settings.PROMPT_AUDIT_LOG_ENABLED
        self.base_dir = settings.LOGS_DIR / "prompt_audit"
        
    def _ensure_dir(self):
        if not self.base_dir.exists():
            self.base_dir.mkdir(parents=True, exist_ok=True)

    def log_failure(
        self, 
        context: str, 
        raw_output: str, 
        error: str, 
        model_name: str = "unknown"
    ) -> Optional[Path]:
        """
        Log a validation failure to a temporary file.
        """
        if not self.enabled:
            return None
            
        try:
            self._ensure_dir()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_id = str(uuid.uuid4())[:8]
            filename = f"audit_{timestamp}_{log_id}.txt"
            file_path = self.base_dir / filename
            
            content = [
                "=== PROMPT AUDIT LOG ===",
                f"Timestamp: {datetime.now().isoformat()}",
                f"Model: {model_name}",
                f"Context/Source: {context}",
                "\n=== VALIDATION ERROR ===",
                error,
                "\n=== RAW LLM OUTPUT ===",
                raw_output,
                "\n=== END OF LOG ==="
            ]
            
            with open(file_path, "w") as f:
                f.write("\n".join(content))
                
            return file_path
        except Exception as e:
            # Fallback to print if file logging fails to avoid crashing the main process
            print(f"Failed to write prompt audit log: {e}")
            return None

# Singleton instance
prompt_audit_logger = PromptAuditLogger()
