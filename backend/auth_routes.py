from fastapi import APIRouter, HTTPException, Request, Response, Depends
from pydantic import BaseModel
from auth import (
    process_session_id,
    create_or_update_user,
    save_session,
    delete_session,
    get_current_user,
    User
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

class SessionRequest(BaseModel):
    session_id: str

@router.post("/session")
async def create_session(request: SessionRequest, response: Response):
    """Exchange session_id for session_token and user data."""
    try:
        # Get user data from Emergent auth
        user_data = await process_session_id(request.session_id)
        
        # Create or get user
        user = await create_or_update_user(user_data)
        
        # Save session
        session_token = user_data['session_token']
        await save_session(user.id, session_token)
        
        # Set httpOnly cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7 * 24 * 60 * 60  # 7 days
        )
        
        return {
            "success": True,
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "picture": user.picture,
                "role": user.role
            }
        }
    except Exception as e:
        logger.error(f"Session creation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture,
        "role": current_user.role
    }

@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout and clear session."""
    session_token = request.cookies.get('session_token')
    
    if session_token:
        await delete_session(session_token)
    
    response.delete_cookie(
        key="session_token",
        path="/",
        samesite="none",
        secure=True
    )
    
    return {"success": True, "message": "Logged out successfully"}