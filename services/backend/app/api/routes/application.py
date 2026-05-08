from fastapi import APIRouter, HTTPException
from sqlmodel import select, func
from datetime import datetime
from app.api.deps import CurrentUser, SessionDep

# Import validation schemas
from app.api.validation.schemas import (
    SaveApplicationRequest,
    SaveApplicationResponse,
    UpdateApplicationStatusRequest,
    UpdateApplicationRequest,
    CreateApplicationRequest,
)

# Import database models
from database_pkg.models import (
    Application, 
    JobDescription as DBJobDescription, 
    GeneratedLetter as DBGeneratedLetter,
    ApplicationStatus,
    ApplicationStatusHistory
)

router = APIRouter(tags=["application"])

@router.post("/save-application", response_model=SaveApplicationResponse)
async def save_application(
    request: SaveApplicationRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    """
    Save complete application workflow to database.
    Requires JWT authentication.
    
    Creates or updates:
    - JobDescription (deduplicates by URL)
    - GeneratedLetter (all versions from race mode)
    - Application (final selected version with header)
    """
    try:
        # Step 1: Create or get existing JobDescription
        # Check if job description already exists for this URL
        statement = select(DBJobDescription).where(DBJobDescription.url == request.job_url)
        existing_job = session.exec(statement).first()
        
        if existing_job:
            job_description = existing_job
        else:
            job_description = DBJobDescription(
                url=request.job_url,
                full_description=request.job_description,
                requirements=request.job_requirements,
                job_title=request.job_title,
                company=request.job_company,
                source=request.job_source,
            )
            session.add(job_description)
            session.commit()
            session.refresh(job_description)
        
        # Step 2: Create GeneratedLetter with all versions
        generated_letters_data = [
            {
                "model": letter.model,
                "letter": letter.letter,
                "timestamp": letter.timestamp,
            }
            for letter in request.generated_letters
        ]
        
        generated_letter = DBGeneratedLetter(
            user_id=current_user.id,
            generated_letters=generated_letters_data,
        )
        session.add(generated_letter)
        session.commit()
        session.refresh(generated_letter)
        
        # Step 3: Create Application with final selected letter
        # Prepare cover_letter_final structure
        selected_letter = request.generated_letters[request.selected_letter_index]
        cover_letter_final = {
            "model": selected_letter.model,
            "timestamp": selected_letter.timestamp,
            "body": request.cover_letter_body,  # The final edited version
        }
        
        application = Application(
            user_id=current_user.id,
            job_description_id=job_description.id,
            generated_letter_id=generated_letter.id,
            header=request.header,
            cover_letter_final=cover_letter_final,
            status=ApplicationStatus.APPLIED,
        )
        session.add(application)
        session.commit()
        session.refresh(application)
        
        # Record initial status history
        history = ApplicationStatusHistory(
            application_id=application.id,
            old_status=None,
            new_status=ApplicationStatus.APPLIED,
            notes="Initial application creation"
        )
        session.add(history)
        session.commit()
        
        return SaveApplicationResponse(
            success=True,
            application_id=application.id,
            job_description_id=job_description.id,
            generated_letter_id=generated_letter.id,
        )
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save application: {str(e)}"
        )


@router.post("/application")
async def create_manual_application(
    request: CreateApplicationRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    """
    Manually create a new application record.
    """
    try:
        # Step 1: Create or get JobDescription
        # We use the URL as a unique identifier if provided, otherwise create new
        job_description = None
        if request.job_url:
            statement = select(DBJobDescription).where(DBJobDescription.url == request.job_url)
            job_description = session.exec(statement).first()
        
        if not job_description:
            job_description = DBJobDescription(
                url=request.job_url or f"manual-{datetime.utcnow().timestamp()}",
                job_title=request.job_title,
                company=request.company,
                full_description=f"Manually created application for {request.job_title} at {request.company}",
                requirements=[],
                source="Manual Entry"
            )
            session.add(job_description)
            session.commit()
            session.refresh(job_description)
        
        # Step 2: Create Application
        application = Application(
            user_id=current_user.id,
            job_description_id=job_description.id,
            status=ApplicationStatus(request.status),
            notes=request.notes,
            cover_letter_final={
                "model": "Manual",
                "timestamp": datetime.utcnow().isoformat(),
                "body": request.cover_letter_body
            },
            header={} # Empty header for manual entry
        )
        session.add(application)
        session.commit()
        session.refresh(application)
        
        # Step 3: Record initial history
        history = ApplicationStatusHistory(
            application_id=application.id,
            old_status=None,
            new_status=application.status,
            notes="Manual application creation"
        )
        session.add(history)
        session.commit()
        
        return {"success": True, "application_id": application.id}
        
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create manual application: {str(e)}"
        )


@router.get("/applications")
async def get_user_applications(
    session: SessionDep,
    current_user: CurrentUser,
    limit: int = 50,
    skip: int = 0,
    include_details: bool = False,
):
    """
    Get current user's applications.
    Requires JWT authentication.
    
    Returns list of applications (lightweight by default) with pagination.
    """
    try:
        # Count total
        count_stmt = select(func.count(Application.id)).where(Application.user_id == current_user.id)
        total = session.exec(count_stmt).one()
        
        # Query applications for current user with job description join
        statement = (
            select(Application, DBJobDescription)
            .join(DBJobDescription, Application.job_description_id == DBJobDescription.id)
            .where(Application.user_id == current_user.id)
            .order_by(Application.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        results = session.exec(statement).all()
        
        # Transform to response format
        applications = []
        for app, job_desc in results:
            app_dict = {
                "id": app.id,
                "job_title": job_desc.job_title,
                "company": job_desc.company,
                "job_url": job_desc.url,
                "status": app.status.value,
                "notes": app.notes,
                "created_at": app.created_at.isoformat(),
            }
            if include_details:
                app_dict["header"] = app.header
                app_dict["cover_letter_final"] = app.cover_letter_final
                app_dict["job_description"] = job_desc.full_description
                app_dict["requirements"] = job_desc.requirements
                
            applications.append(app_dict)
        
        return {"applications": applications, "total": total}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch applications: {str(e)}"
        )


@router.get("/application/{application_id}/details")
async def get_application_details(
    application_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    """
    Get heavy details for a specific application.
    Requires JWT authentication.
    """
    try:
        statement = (
            select(Application, DBJobDescription)
            .join(DBJobDescription, Application.job_description_id == DBJobDescription.id)
            .where(
                Application.id == application_id,
                Application.user_id == current_user.id
            )
        )
        result = session.exec(statement).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Application not found")
            
        app, job_desc = result
        
        return {
            "id": app.id,
            "job_title": job_desc.job_title,
            "company": job_desc.company,
            "status": app.status.value,
            "job_url": job_desc.url,
            "header": app.header,
            "cover_letter_final": app.cover_letter_final,
            "notes": app.notes,
            "job_description": job_desc.full_description,
            "requirements": job_desc.requirements,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch application details: {str(e)}"
        )


@router.patch("/application/{application_id}/status")
async def update_application_status(
    application_id: int,
    request: UpdateApplicationStatusRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    """
    Update application status.
    Requires JWT authentication.
    """
    try:
        # Verify application exists and belongs to user
        statement = select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id
        )
        application = session.exec(statement).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
            
        # Validate status enum
        try:
            new_status = ApplicationStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
            
        # Update status
        application.status = new_status
        session.add(application)
        session.commit()
        session.refresh(application)
        
        return {"success": True, "status": application.status.value}
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update status: {str(e)}"
        )


@router.delete("/application/{application_id}")
async def delete_application(
    application_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    """
    Delete an application.
    Requires JWT authentication.
    """
    try:
        # Verify application exists and belongs to user
        statement = select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id
        )
        application = session.exec(statement).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        # Keep the generated letter reference before nullifying it.
        # This avoids FK violations when the application still points to the letter row.
        letter_id = application.generated_letter_id
        application.generated_letter_id = None
        session.add(application)
        session.flush()

        # 1. Delete status history records
        history_statement = select(ApplicationStatusHistory).where(
            ApplicationStatusHistory.application_id == application_id
        )
        history_records = session.exec(history_statement).all()
        for record in history_records:
            session.delete(record)

        # 2. Delete related generated letters
        # Some applications have a direct link, some have letters pointing back to them.
        # Delete letters pointing back to this application
        related_letters_stmt = select(DBGeneratedLetter).where(
            DBGeneratedLetter.application_id == application_id
        )
        related_letters = session.exec(related_letters_stmt).all()
        deleted_letter_ids = set()
        for letter in related_letters:
            deleted_letter_ids.add(letter.id)
            session.delete(letter)

        # Delete the specific linked letter if it wasn't already deleted above.
        if letter_id and letter_id not in deleted_letter_ids:
            specific_letter = session.get(DBGeneratedLetter, letter_id)
            if specific_letter and specific_letter.user_id == current_user.id:
                session.delete(specific_letter)

        # 3. Finally delete the application
        session.delete(application)
        session.commit()
        
        return {"success": True, "message": "Application deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete application: {str(e)}"
        )
@router.patch("/application/{application_id}")
async def update_application(
    application_id: int,
    request: UpdateApplicationRequest,
    session: SessionDep,
    current_user: CurrentUser,
):
    """
    Update application details, notes, or job info.
    Requires JWT authentication.
    """
    try:
        # Verify application exists and belongs to user
        statement = (
            select(Application, DBJobDescription)
            .join(DBJobDescription, Application.job_description_id == DBJobDescription.id)
            .where(
                Application.id == application_id,
                Application.user_id == current_user.id
            )
        )
        result = session.exec(statement).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="Application not found")
            
        application, job_description = result
        
        # Update Application fields
        if request.status is not None:
            try:
                new_status = ApplicationStatus(request.status)
                if new_status != application.status:
                    # Record history before changing status
                    history = ApplicationStatusHistory(
                        application_id=application.id,
                        old_status=application.status,
                        new_status=new_status,
                        notes=request.notes if request.notes else "Status manual update"
                    )
                    session.add(history)
                    application.status = new_status
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {request.status}")
        
        if request.notes is not None:
            application.notes = request.notes
            
        if request.header is not None:
            application.header = request.header
            
        if request.cover_letter_body is not None:
            # Update the body in the cover_letter_final JSON
            new_final = dict(application.cover_letter_final)
            new_final["body"] = request.cover_letter_body
            application.cover_letter_final = new_final
            
        application.updated_at = datetime.utcnow()
        
        # Update JobDescription fields
        job_updated = False
        if request.job_title is not None:
            job_description.job_title = request.job_title
            job_updated = True
            
        if request.company is not None:
            job_description.company = request.company
            job_updated = True
            
        if job_updated:
            job_description.updated_at = datetime.utcnow()
            session.add(job_description)
            
        session.add(application)
        session.commit()
        session.refresh(application)
        
        return {"success": True, "application_id": application.id}
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update application: {str(e)}"
        )

@router.get("/application/{application_id}/history")
async def get_application_history(
    application_id: int,
    session: SessionDep,
    current_user: CurrentUser,
):
    """
    Get the status history of a specific application.
    Requires JWT authentication.
    """
    try:
        # Verify ownership
        statement = select(Application).where(
            Application.id == application_id,
            Application.user_id == current_user.id
        )
        application = session.exec(statement).first()
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")
            
        # Get history
        history_statement = (
            select(ApplicationStatusHistory)
            .where(ApplicationStatusHistory.application_id == application_id)
            .order_by(ApplicationStatusHistory.created_at.desc())
        )
        history = session.exec(history_statement).all()
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch history: {str(e)}"
        )
