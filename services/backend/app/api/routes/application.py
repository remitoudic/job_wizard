import re
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

from database_pkg.models import Application, ApplicationStatus, ApplicationStatusHistory
from database_pkg.models import GeneratedLetter as DBGeneratedLetter
from database_pkg.models import JobDescription as DBJobDescription
from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.api.validation.schemas import CreateApplicationRequest, SaveApplicationRequest, SaveApplicationResponse, UpdateApplicationRequest, UpdateApplicationStatusRequest

router = APIRouter(tags=["application"])