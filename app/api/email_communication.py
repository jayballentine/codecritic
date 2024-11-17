from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from app.services.email_service import email_service
from app.services.subscription_service import subscription_service
from app.auth.access_control import get_current_user
from app.models.user import User

router = APIRouter(prefix="/email", tags=["email"])

class EmailRequest(BaseModel):
    recipient: str
    subject: str
    template_name: str
    context: Dict
    subscription_tier: Optional[str] = None

@router.post("/send")
async def send_email(
    email_request: EmailRequest, 
    current_user: User = Depends(get_current_user)
):
    """
    Send an email with optional subscription-aware templating
    
    Args:
        email_request (EmailRequest): Email sending details
        current_user (User): Authenticated user
    
    Returns:
        dict: Email sending status
    """
    try:
        # Fetch user's subscription if tier is not provided
        subscription = None
        if email_request.subscription_tier:
            subscription = subscription_service.get_subscription_by_tier(
                email_request.subscription_tier
            )
        
        success = email_service.send_email(
            recipient=email_request.recipient,
            subject=email_request.subject,
            template_name=email_request.template_name,
            context=email_request.context,
            subscription=subscription
        )
        
        return {
            "status": "success" if success else "failed",
            "message": "Email sent successfully" if success else "Email sending failed"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/queue")
async def queue_email(
    email_request: EmailRequest, 
    current_user: User = Depends(get_current_user)
):
    """
    Queue an email for later processing
    
    Args:
        email_request (EmailRequest): Email queuing details
        current_user (User): Authenticated user
    
    Returns:
        dict: Email queuing status
    """
    try:
        # Fetch user's subscription if tier is not provided
        subscription = None
        if email_request.subscription_tier:
            subscription = subscription_service.get_subscription_by_tier(
                email_request.subscription_tier
            )
        
        email_service.queue_email({
            'recipient': email_request.recipient,
            'subject': email_request.subject,
            'template_name': email_request.template_name,
            'context': email_request.context,
            'subscription': subscription
        })
        
        return {
            "status": "success",
            "message": "Email queued successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-queue")
async def process_email_queue(current_user: User = Depends(get_current_user)):
    """
    Manually trigger email queue processing
    
    Args:
        current_user (User): Authenticated user
    
    Returns:
        dict: Queue processing status
    """
    try:
        email_service.process_email_queue()
        return {
            "status": "success",
            "message": "Email queue processed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
