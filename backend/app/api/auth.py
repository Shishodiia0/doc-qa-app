import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.schemas import UserCreate, UserResponse, Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user: UserCreate, db=Depends(get_db)):
    existing = await db.users.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")
    user_id = str(uuid.uuid4())
    await db.users.insert_one({
        "_id": user_id,
        "username": user.username,
        "password": hash_password(user.password),
    })
    return UserResponse(id=user_id, username=user.username)


@router.post("/login", response_model=Token)
async def login(user: UserCreate, db=Depends(get_db)):
    db_user = await db.users.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": db_user["_id"]})
    return Token(access_token=token)
