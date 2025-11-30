from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
import os
import logging
import httpx

logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

security = HTTPBearer(auto_error=False)

class User:
    def __init__(self, id: str, email: str, name: str, picture: str = None, role: str = "user"):
        self.id = id
        self.email = email
        self.name = name
        self.picture = picture
        self.role = role

async def get_user_from_session_token(session_token: str) -> Optional[User]:
    """Get user from session token stored in database."""
    try:
        # Find session
        session = await db.user_sessions.find_one({
            "session_token": session_token
        })
        
        if not session:
            logger.debug(f"Session not found for token: {session_token[:10]}...")
            return None
        
        # Check expiry
        expires_at = session.get('expires_at')
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at and expires_at < datetime.now(timezone.utc):
            logger.debug("Session expired")
            return None
        
        # Get user
        user_id = session.get('user_id')
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
        
        if not user_doc:
            logger.debug(f"User not found: {user_id}")
            return None
        
        return User(
            id=user_doc['id'],
            email=user_doc['email'],
            name=user_doc['name'],
            picture=user_doc.get('picture'),
            role=user_doc.get('role', 'user')
        )
    except Exception as e:
        logger.error(f"Error getting user from session: {str(e)}")
        return None

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """Get current authenticated user from cookie or Authorization header."""
    session_token = None
    
    # First check cookie
    session_token = request.cookies.get('session_token')
    
    # Fallback to Authorization header
    if not session_token and credentials:
        session_token = credentials.credentials
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = await get_user_from_session_token(session_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session"
        )
    
    return user

async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role."""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def process_session_id(session_id: str) -> Dict:
    """Exchange session_id for session_token and user data."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data',
                headers={'X-Session-ID': session_id}
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid session ID"
                )
            
            data = response.json()
            return data
    except httpx.RequestError as e:
        logger.error(f"Error fetching session data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate session"
        )

async def create_or_update_user(user_data: Dict) -> User:
    """Create new user or return existing user."""
    email = user_data['email']
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    if existing_user:
        return User(
            id=existing_user['id'],
            email=existing_user['email'],
            name=existing_user['name'],
            picture=existing_user.get('picture'),
            role=existing_user.get('role', 'user')
        )
    
    # Create new user
    user_doc = {
        "id": user_data['id'],
        "email": user_data['email'],
        "name": user_data['name'],
        "picture": user_data.get('picture'),
        "role": "user",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    
    return User(
        id=user_doc['id'],
        email=user_doc['email'],
        name=user_doc['name'],
        picture=user_doc.get('picture'),
        role=user_doc.get('role', 'user')
    )

async def save_session(user_id: str, session_token: str) -> None:
    """Save session to database with 7 day expiry."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_sessions.insert_one(session_doc)

async def delete_session(session_token: str) -> None:
    """Delete session from database."""
    await db.user_sessions.delete_one({"session_token": session_token})