import shutil
from pathlib import Path
from datetime import datetime
import logfire

class BackupService:
    def __init__(self, backup_dir: str = "/app/backups/letters_file_backup"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_cover_letter_pdf(
        self,
        source_path: str,
        user_id: str,
        company: str,
        date_str: str = None
    ) -> str:
        """
        Backs up proper formatted filename: user_id_date_company.pdf
        """
        try:
            if not date_str:
                date_str = datetime.now().strftime("%Y-%m-%d")
            
            # Sanitize company name
            safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
            
            filename = f"{user_id}_{date_str}_{safe_company}.pdf"
            destination = self.backup_dir / filename
            
            shutil.copy2(source_path, destination)
            logfire.info(f"Backed up cover letter to {destination}")
            return str(destination)
        except Exception as e:
            logfire.error(f"Backup failed: {str(e)}")
            # We don't want to break the main flow if backup fails, but we should log it
            return None
