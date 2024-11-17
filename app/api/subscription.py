from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.models.subscription import SubscriptionCreate, SubscriptionResponse, SubscriptionUpdate
from app.services.subscription_service import SubscriptionService
from app.utils.security import get_current_user
from app.models.user import UserResponse

router = APIRouter()

@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Create a new subscription for the current user.
    
    Parameters:
    - plan_type: Type of subscription plan
    - payment_method_id: ID of the payment method to use
    
    Returns:
    - Created subscription details
    """
    try:
        return await SubscriptionService.create_subscription(current_user.id, subscription_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/subscriptions/current", response_model=SubscriptionResponse)
async def get_current_subscription(current_user: UserResponse = Depends(get_current_user)):
    """
    Get the current user's active subscription.
    
    Returns:
    - Current subscription details
    """
    subscription = await SubscriptionService.get_active_subscription(current_user.id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    return subscription

@router.get("/subscriptions/history", response_model=List[SubscriptionResponse])
async def get_subscription_history(current_user: UserResponse = Depends(get_current_user)):
    """
    Get the user's subscription history.
    
    Returns:
    - List of all subscriptions, including past ones
    """
    return await SubscriptionService.get_subscription_history(current_user.id)

@router.put("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: int,
    update_data: SubscriptionUpdate,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Update an existing subscription.
    
    Parameters:
    - subscription_id: ID of the subscription to update
    - plan_type: New plan type (optional)
    - status: New status (optional)
    
    Returns:
    - Updated subscription details
    """
    try:
        return await SubscriptionService.update_subscription(
            subscription_id,
            current_user.id,
            update_data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_subscription(
    subscription_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Cancel an active subscription.
    
    Parameters:
    - subscription_id: ID of the subscription to cancel
    """
    try:
        await SubscriptionService.cancel_subscription(subscription_id, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/subscription-plans")
async def get_available_plans():
    """
    Get list of available subscription plans.
    
    Returns:
    - List of subscription plans with details
    """
    return await SubscriptionService.get_available_plans()

@router.post("/subscriptions/{subscription_id}/change-plan")
async def change_subscription_plan(
    subscription_id: int,
    new_plan_id: int,
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Change the plan of an existing subscription.
    
    Parameters:
    - subscription_id: ID of the subscription to modify
    - new_plan_id: ID of the new plan
    
    Returns:
    - Updated subscription details
    """
    try:
        return await SubscriptionService.change_subscription_plan(
            subscription_id,
            current_user.id,
            new_plan_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
