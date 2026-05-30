import re
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

from database_pkg.models import (
    Application,
    ApplicationStatus,
    ApplicationStatusHistory,
)
from database_pkg.models import (
    GeneratedLetter as DBGeneratedLetter,
)
from database_pkg.models import (
    JobDescription as DBJobDescription,
)
from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep

from app.api.validation.schemas import (
    CreateApplicationRequest,
    SaveApplicationRequest,
    SaveApplicationResponse,
    UpdateApplicationRequest,
    UpdateApplicationStatusRequest,
)

router = APIRouter(tags=["application"])


@router.post("/save-application", response_model=SaveApplicationResponse)
async def save_application(request: SaveApplicationRequest, session: SessionDep, current_user: CurrentUser):
    try:
        statement = select(DBJobDescription).where(DBJobDescription.url == request.job_url)
        existing_job = session.exec(statement).first()
        if existing_job:
            job_description = existing_job
        else:
            job_description = DBJobDescription(url=request.job_url, full_description=request.job_description, requirements=request.job_requirements, job_title=request.job_title, company=request.job_company, source=request.job_source)
            session.add(job_description)
            session.commit()
            session.refresh(job_description)
        generated_letters_data = [{"model": letter.model, "letter": letter.letter, "timestamp": letter.timestamp} for letter in request.generated_letters]
        generated_letter = DBGeneratedLetter(user_id=current_user.id, generated_letters=generated_letters_data)
        session.add(generated_letter)
        session.commit()
        session.refresh(generated_letter)
        selected_letter = request.generated_letters[request.selected_letter_index]
        cover_letter_final = {"model": selected_letter.model, "timestamp": selected_letter.timestamp, "body": request.cover_letter_body}
        application = Application(user_id=current_user.id, job_description_id=job_description.id, generated_letter_id=generated_letter.id, header=request.header, cover_letter_final=cover_letter_final, status=ApplicationStatus.APPLIED)
        session.add(application)
        session.commit()
        session.refresh(application)
        history = ApplicationStatusHistory(application_id=application.id, old_status=None, new_status=ApplicationStatus.APPLIED, notes="Initial application creation")
        session.add(history)
        session.commit()
        return SaveApplicationResponse(success=True, application_id=application.id, job_description_id=job_description.id, generated_letter_id=generated_letter.id)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save application: {str(e)}")


@router.post("/application")
async def create_manual_application(request: CreateApplicationRequest, session: SessionDep, current_user: CurrentUser):
    try:
        job_description = None
        if request.job_url:
            statement = select(DBJobDescription).where(DBJobDescription.url == request.job_url)
            job_description = session.exec(statement).first()
        if not job_description:
            job_description = DBJobDescription(url=request.job_url or f"manual-{datetime.utcnow().timestamp()}", job_title=request.job_title, company=request.company, full_description=f"Manually created application for {request.job_title} at {request.company}", requirements=[], source="Manual Entry")
            session.add(job_description)
            session.commit()
            session.refresh(job_description)
        application = Application(user_id=current_user.id, job_description_id=job_description.id, status=ApplicationStatus(request.status), notes=request.notes, cover_letter_final={"model": "Manual", "timestamp": datetime.utcnow().isoformat(), "body": request.cover_letter_body}, header={})
        session.add(application)
        session.commit()
        session.refresh(application)
        history = ApplicationStatusHistory(application_id=application.id, old_status=None, new_status=application.status, notes="Manual application creation")
        session.add(history)
        session.commit()
        return {"success": True, "application_id": application.id}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create manual application: {str(e)}")


@router.get("/applications")
async def get_user_applications(session: SessionDep, current_user: CurrentUser, limit: int = 50, skip: int = 0, include_details: bool = False, sort_by: str = "created_at", sort_order: str = "desc", company: str | None = None):
    try:
        count_stmt = select(func.count(Application.id)).join(DBJobDescription).where(Application.user_id == current_user.id)
        if company:
            count_stmt = count_stmt.where(DBJobDescription.company.ilike(f"%{company}%"))
        total = session.exec(count_stmt).one()
        sort_map = {"created_at": Application.created_at, "company": DBJobDescription.company, "status": Application.status, "job_title": DBJobDescription.job_title}
        sort_col = sort_map.get(sort_by, Application.created_at)
        from sqlmodel import asc, desc
        order_expr = desc(sort_col) if sort_order == "desc" else asc(sort_col)
        statement = select(Application, DBJobDescription).join(DBJobDescription).where(Application.user_id == current_user.id)
        if company:
            statement = statement.where(DBJobDescription.company.ilike(f"%{company}%"))
        statement = statement.order_by(order_expr).offset(skip).limit(limit)
        results = session.exec(statement).all()
        applications = []
        for app, job_desc in results:
            app_dict = {"id": app.id, "job_title": job_desc.job_title, "company": job_desc.company, "job_url": job_desc.url, "status": app.status.value, "notes": app.notes, "created_at": app.created_at.isoformat()}
            if include_details:
                app_dict["header"] = app.header
                app_dict["cover_letter_final"] = app.cover_letter_final
                app_dict["job_description"] = job_desc.full_description
                app_dict["requirements"] = job_desc.requirements
            applications.append(app_dict)
        return {"applications": applications, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch applications: {str(e)}")


@router.get("/applications/companies", response_model=list[str])
async def get_user_companies(session: SessionDep, current_user: CurrentUser):
    try:
        statement = select(DBJobDescription.company).join(Application).where(Application.user_id == current_user.id).distinct().order_by(DBJobDescription.company)
        companies = session.exec(statement).all()
        return [c for c in companies if c]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/application/{application_id}/details")
async def get_application_details(application_id: int, session: SessionDep, current_user: CurrentUser):
    try:
        statement = select(Application, DBJobDescription).join(DBJobDescription, Application.job_description_id == DBJobDescription.id).where(Application.id == application_id, Application.user_id == current_user.id)
        result = session.exec(statement).first()
        if not result:
            raise HTTPException(status_code=404, detail="Application not found")
        app, job_desc = result
        return {"id": app.id, "job_title": job_desc.job_title, "company": job_desc.company, "status": app.status.value, "job_url": job_desc.url, "header": app.header, "cover_letter_final": app.cover_letter_final, "notes": app.notes, "job_description": job_desc.full_description, "requirements": job_desc.requirements}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch application details: {str(e)}")


@router.get("/application/check-duplicate")
async def check_duplicate_application(job_url: str, session: SessionDep, current_user: CurrentUser):
    """
    Check if the current user already has an application for a given job URL.
    Handles: www/non-www, trailing slashes, LinkedIn job ID extraction.
    """
    try:
        parsed = urlparse(job_url)
        netloc = parsed.netloc.lower()
        path = parsed.path.rstrip("/") or "/"
        normalized_netloc = netloc.removeprefix("www.")
        normalized_url = urlunparse((parsed.scheme, normalized_netloc, path, parsed.params, parsed.query, parsed.fragment)).rstrip("/")
        www_url = urlunparse((parsed.scheme, f"www.{normalized_netloc}", path, parsed.params, parsed.query, parsed.fragment)).rstrip("/")
        url_variants = set([job_url, normalized_url, www_url])
        job_id = None
        m = re.search(r"linkedin\.com/jobs/view/(\d+)", job_url)
        if not m:
            m = re.search(r"currentJobId=(\d+)", job_url)
        if m:
            job_id = m.group(1)
            url_variants.add(f"https://www.linkedin.com/jobs/view/{job_id}/")
            url_variants.add(f"https://linkedin.com/jobs/view/{job_id}/")
        url_variants = list(url_variants)
        statement = select(Application, DBJobDescription).join(DBJobDescription, Application.job_description_id == DBJobDescription.id).where(Application.user_id == current_user.id, DBJobDescription.url.in_(url_variants))
        result = session.exec(statement).first()
        if not result:
            return {"is_duplicate": False, "existing_application": None}
        app, job_desc = result
        cover_letter_body = None
        if app.cover_letter_final and "body" in app.cover_letter_final:
            cover_letter_body = app.cover_letter_final["body"]
        return {"is_duplicate": True, "existing_application": {"id": app.id, "job_title": job_desc.job_title, "company": job_desc.company, "status": app.status.value, "notes": app.notes, "cover_letter_body": cover_letter_body, "created_at": app.created_at.isoformat()}}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check duplicate application: {str(e)}")


@router.patch("/application/{application_id}/status")
async def update_application_status(application_id: int, request: UpdateApplicationStatusRequest, session: SessionDep, current_user: CurrentUser):
    try:
        statement = select(Application).where(Application.id == application_id, Application.user_id == current_user.id)
        application = session.exec(statement).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        try:
            new_status = ApplicationStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
        application.status = new_status
        session.add(application)
        session.commit()
        session.refresh(application)
        return {"success": True, "status": application.status.value}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")


@router.delete("/application/{application_id}")
async def delete_application(application_id: int, session: SessionDep, current_user: CurrentUser):
    try:
        statement = select(Application).where(Application.id == application_id, Application.user_id == current_user.id)
        application = session.exec(statement).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        letter_id = application.generated_letter_id
        history_statement = select(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id == application_id)
        history_records = session.exec(history_statement).all()
        for record in history_records:
            session.delete(record)
        related_letters_stmt = select(DBGeneratedLetter).where(DBGeneratedLetter.application_id == application_id)
        related_letters = session.exec(related_letters_stmt).all()
        session.delete(application)
        session.flush()
        deleted_letter_ids = set()
        for letter in related_letters:
            deleted_letter_ids.add(letter.id)
            session.delete(letter)
        if letter_id and letter_id not in deleted_letter_ids:
            refs_stmt = select(func.count(Application.id)).where(Application.generated_letter_id == letter_id, Application.id != application_id)
            remaining_refs = session.exec(refs_stmt).one()
            if remaining_refs == 0:
                specific_letter = session.get(DBGeneratedLetter, letter_id)
                if specific_letter and specific_letter.user_id == current_user.id:
                    session.delete(specific_letter)
        session.commit()
        return {"success": True, "message": "Application deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete application: {str(e)}")


@router.patch("/application/{application_id}")
async def update_application(application_id: int, request: UpdateApplicationRequest, session: SessionDep, current_user: CurrentUser):
    try:
        statement = select(Application, DBJobDescription).join(DBJobDescription, Application.job_description_id == DBJobDescription.id).where(Application.id == application_id, Application.user_id == current_user.id)
        result = session.exec(statement).first()
        if not result:
            raise HTTPException(status_code=404, detail="Application not found")
        application, job_description = result
        if request.status is not None:
            try:
                new_status = ApplicationStatus(request.status)
                if new_status != application.status:
                    history = ApplicationStatusHistory(application_id=application.id, old_status=application.status, new_status=new_status, notes=request.notes if request.notes else "Status manual update")
                    session.add(history)
                    application.status = new_status
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
        if request.notes is not None:
            application.notes = request.notes
        if request.header is not None:
            application.header = request.header
        if request.cover_letter_body is not None:
            new_final = dict(application.cover_letter_final)
            new_final["body"] = request.cover_letter_body
            application.cover_letter_final = new_final
        application.updated_at = datetime.now(timezone.utc)
        job_updated = False
        if request.job_title is not None:
            job_description.job_title = request.job_title
            job_updated = True
        if request.company is not None:
            job_description.company = request.company
            job_updated = True
        if job_updated:
            job_description.updated_at = datetime.now(timezone.utc)
            session.add(job_description)
        session.add(application)
        session.commit()
        session.refresh(application)
        return {"success": True, "application_id": application.id}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update application: {str(e)}")


@router.get("/application/{application_id}/history")
async def get_application_history(application_id: int, session: SessionDep, current_user: CurrentUser):
    try:
        statement = select(Application).where(Application.id == application_id, Application.user_id == current_user.id)
        application = session.exec(statement).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
        history_statement = select(ApplicationStatusHistory).where(ApplicationStatusHistory.application_id == application_id).order_by(ApplicationStatusHistory.created_at.desc())
        history = session.exec(history_statement).all()
        return history
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")