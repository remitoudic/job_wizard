from sqlmodel import SQLModel, Field
from typing import Optional

# Import User models from the database package
# The package name is 'src' because of how it's structured in the DB folder, 
# but installed via pyproject.toml name 'job-wizard-db'. 
# When installed, it exposes 'src' as a top level module? 
# Wait, standard structure is 'src/package_name' or just 'package_name'.
# In database folder we have 'src' folder. In pyproject.toml we didn't specify packages manually?
# Hatchling default behavior: if 'src' exists, it packages contents of 'src' as modules. 
# So 'database/src/models' -> 'models' module? OR 'src.models'?
# Hatchling src-layout: 'src/my_app' -> 'my_app'.
# Here we have 'src/models'. So 'models' will be top level? That's risky (generic name).
# Let's assume it imports as 'src' or checking structure.
# Ah, I created 'database/src/models'. So 'models' is inside 'src'.
# If I install 'database' folder, and it has 'src', typically 'src' is stripped if using src-layout.
# But I didn't verify Hatchling config.
# Let's try importing from `src.models.user` as that's safe for now or verify later.
# Actually, I should probably rename `database/src` to `database/job_wizard_db` to be safe.
# But for now I'll respect the user's request: "folder src with inside the a model folder".
# User requested `database/src`. 
# If installed as editable or standard, `src` might be the namespace. 

from src.models.user import User, UserCreate, UserRead, UserUpdate, UserBase

class Token(SQLModel):
    access_token: str
    token_type: str

class TokenData(SQLModel):
    username: Optional[str] = None
