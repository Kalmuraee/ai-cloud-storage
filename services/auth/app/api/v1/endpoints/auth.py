from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.api import deps
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    verify_email_token,
)
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()

@router.post("/register", response_model=UserResponse)
from app.core.logging import get_logger

logger = get_logger()

@router.post("/register", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Register a new user.
    """
    try:
        # Registration logic
        logger.info(f"User {user_in.email} registered")
        return user
    except Exception as e:
        logger.error(f"Error registering user {user_in.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user"
        )

@router.post("/login", response_model=Token, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    try:
        # Login logic
        logger.info(f"User {form_data.username} logged in")
        return tokens
    except Exception as e:
        logger.error(f"Error logging in user {form_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error logging in user"
        )
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@router.post("/login", response_model=Token, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    # Login logic
    ...

@router.post("/register", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Register a new user.
    """
    # Registration logic
    ...

@app.on_event("startup")
async def startup():
    await FastAPILimiter.init(settings.REDIS_HOST, settings.REDIS_PORT)
@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Register a new user.
    """
    # Check if user exists
    user = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    # Create new user
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Send email verification
    verification_token = create_email_verification_token(user.id)
    send_email_verification_email(user.email, verification_token)

    return user

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    # Try to authenticate
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive",
        )

    if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified",
        )

    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Register a new user.
    """
    # Check if user exists
    user = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    # Create new user
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
@router.post("/roles", response_model=Role)
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Create a new role.
    """
    role = db.query(Role).filter(Role.name == role_in.name).first()
    if role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists",
        )

    role = Role(
        name=role_in.name,
        description=role_in.description,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@router.post("/permissions", response_model=Permission)
def create_permission(
    permission_in: PermissionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Create a new permission.
    """
    permission = db.query(Permission).filter(Permission.name == permission_in.name).first()
    if permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission with this name already exists",
        )

    permission = Permission(
        name=permission_in.name,
        description=permission_in.description,
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission

@router.post("/roles/{role_id}/permissions/{permission_id}")
def add_permission_to_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Add a permission to a role.
    """
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    permission = db.query(Permission).get(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )

    role.permissions.append(permission)
    db.commit()
    return {"message": "Permission added to role"}

@router.post("/users/{user_id}/roles/{role_id}")
def assign_role_to_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Assign a role to a user.
    """
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    user.roles.append(role)
    db.commit()
    return {"message": "Role assigned to user"}
@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    email: EmailStr,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Request a password reset.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if the email is registered or not
        return {"message": "If the email is registered, a password reset link has been sent."}

    reset_token = create_password_reset_token(user.id)
    send_password_reset_email(email, reset_token)

    return {"message": "If the email is registered, a password reset link has been sent."}

@router.post("/password-reset/{token}", response_model=Token)
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password using a valid token.
    """
    user = verify_password_reset_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    if len(new_password) < settings.PASSWORD_MIN_LENGTH or len(new_password) > settings.PASSWORD_MAX_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be between {settings.PASSWORD_MIN_LENGTH} and {settings.PASSWORD_MAX_LENGTH} characters",
        )

    user.hashed_password = get_password_hash(new_password)
    db.commit()

    # Generate new access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

    # Send email verification
    verification_token = create_email_verification_token(user.id)
@router.post("/login", response_model=Token, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    # Try to authenticate
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive",
        )

    if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified",
        )

    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
    send_email_verification_email(user.email, verification_token)

    return user

@router.post("/verify-email/{token}")
def verify_email(
    token: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Verify user email.
    """
    user = verify_email_verification_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    user.is_verified = True
    db.commit()

    return {"message": "Email verified successfully"}
@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Register a new user.
    """
    # Check if user exists
    user = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    # Create new user
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Send email verification
    verification_token = create_email_verification_token(user.id)
    send_email_verification_email(user.email, verification_token)

    return user

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    # Try to authenticate
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive",
        )

    if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified",
        )

    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Register a new user.
    """
    # Check if user exists
    user = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    # Create new user
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAILS_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_TLS=settings.SMTP_TLS,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER='./templates'
)

async def send_password_reset_email(email: str, reset_token: str):
    message = MessageSchema(
        subject="Password Reset",
        recipients=[email],
        template_body={
            "reset_token": reset_token
        },
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="password_reset.html")

@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    email: EmailStr,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Request a password reset.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if the email is registered or not
        return {"message": "If the email is registered, a password reset link has been sent."}

    reset_token = create_password_reset_token(user.id)
    asyncio.create_task(send_password_reset_email(email, reset_token))

    return {"message": "If the email is registered, a password reset link has been sent."}
@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    email: EmailStr,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Request a password reset.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if the email is registered or not
        return {"message": "If the email is registered, a password reset link has been sent."}

    reset_token = create_password_reset_token(user.id)
    send_password_reset_email(email, reset_token)

    return {"message": "If the email is registered, a password reset link has been sent."}

@router.post("/password-reset/{token}", response_model=Token)
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password using a valid token.
    """
    user = verify_password_reset_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    if len(new_password) < settings.PASSWORD_MIN_LENGTH or len(new_password) > settings.PASSWORD_MAX_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be between {settings.PASSWORD_MIN_LENGTH} and {settings.PASSWORD_MAX_LENGTH} characters",
        )

    user.hashed_password = get_password_hash(new_password)
    db.commit()

    # Generate new access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

    # Send email verification
    verification_token = create_email_verification_token(user.id)
@router.post("/login", response_model=Token, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    # Try to authenticate
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive",
        )

    if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified",
        )

    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
    send_email_verification_email(user.email, verification_token)

    return user

@router.post("/verify-email/{token}")
def verify_email(
    token: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Verify user email.
    """
    user = verify_email_verification_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    user.is_verified = True
    db.commit()

    return {"message": "Email verified successfully"}
@router.get("/me", response_model=UserResponse)
def get_current_user(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get the current user.
    """
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update the current user's profile.
    """
    user = current_user
    user.full_name = user_update.full_name
    user.email = user_update.email
    user.username = user_update.username
    db.commit()
    db.refresh(user)
    return user

@router.post("/change-password")
def change_password(
    password_change: PasswordChange,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Change the current user's password.
    """
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    if len(password_change.new_password) < settings.PASSWORD_MIN_LENGTH or len(password_change.new_password) > settings.PASSWORD_MAX_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be between {settings.PASSWORD_MIN_LENGTH} and {settings.PASSWORD_MAX_LENGTH} characters",
        )

    current_user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()
    return {"message": "Password changed successfully"}
from app.core.logging import get_logger

logger = get_logger()

@router.post("/register", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Register a new user.
    """
    try:
        # Registration logic
        logger.info(f"User {user_in.email} registered")
        return user
    except Exception as e:
        logger.error(f"Error registering user {user_in.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user"
        )

@router.post("/login", response_model=Token, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    try:
        # Login logic
        logger.info(f"User {form_data.username} logged in")
        return tokens
    except Exception as e:
        logger.error(f"Error logging in user {form_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error logging in user"
        )
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@router.post("/login", response_model=Token, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    # Login logic
    ...

@router.post("/register", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAILS_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_TLS=settings.SMTP_TLS,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER='./templates'
)

async def send_password_reset_email(email: str, reset_token: str):
    message = MessageSchema(
        subject="Password Reset",
        recipients=[email],
        template_body={
            "reset_token": reset_token
        },
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="password_reset.html")

@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    email: EmailStr,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Request a password reset.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if the email is registered or not
        return {"message": "If the email is registered, a password reset link has been sent."}

    reset_token = create_password_reset_token(user.id)
    asyncio.create_task(send_password_reset_email(email, reset_token))

    return {"message": "If the email is registered, a password reset link has been sent."}
@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    email: EmailStr,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Request a password reset.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if the email is registered or not
        return {"message": "If the email is registered, a password reset link has been sent."}

    reset_token = create_password_reset_token(user.id)
    send_password_reset_email(email, reset_token)

    return {"message": "If the email is registered, a password reset link has been sent."}

@router.post("/password-reset/{token}", response_model=Token)
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password using a valid token.
    """
    user = verify_password_reset_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    if len(new_password) < settings.PASSWORD_MIN_LENGTH or len(new_password) > settings.PASSWORD_MAX_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be between {settings.PASSWORD_MIN_LENGTH} and {settings.PASSWORD_MAX_LENGTH} characters",
        )

    user.hashed_password = get_password_hash(new_password)
    db.commit()

    # Generate new access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
    Register a new user.
    """
    # Registration logic
    ...

@app.on_event("startup")
async def startup():
    await FastAPILimiter.init(settings.REDIS_HOST, settings.REDIS_PORT)
@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Register a new user.
    """
    # Check if user exists
    user = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    # Create new user
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Send email verification
    verification_token = create_email_verification_token(user.id)
    send_email_verification_email(user.email, verification_token)

    return user

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    # Try to authenticate
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive",
        )

    if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified",
        )

    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
@router.post("/register", response_model=UserResponse)
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Register a new user.
    """
    # Check if user exists
    user = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )

    # Create new user
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Send email verification
    verification_token = create_email_verification_token(user.id)
@router.post("/login", response_model=Token, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    # Try to authenticate
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive",
        )

    if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified",
        )

    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
    send_email_verification_email(user.email, verification_token)

    return user

@router.post("/verify-email/{token}")
@router.post("/roles", response_model=Role)
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Create a new role.
    """
    role = db.query(Role).filter(Role.name == role_in.name).first()
    if role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists",
        )

    role = Role(
        name=role_in.name,
        description=role_in.description,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@router.post("/permissions", response_model=Permission)
def create_permission(
    permission_in: PermissionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Create a new permission.
    """
    permission = db.query(Permission).filter(Permission.name == permission_in.name).first()
    if permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission with this name already exists",
        )

    permission = Permission(
        name=permission_in.name,
        description=permission_in.description,
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission

@router.post("/roles/{role_id}/permissions/{permission_id}")
def add_permission_to_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Add a permission to a role.
    """
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    permission = db.query(Permission).get(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )

    role.permissions.append(permission)
    db.commit()
    return {"message": "Permission added to role"}

@router.post("/users/{user_id}/roles/{role_id}")
def assign_role_to_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Assign a role to a user.
    """
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    user.roles.append(role)
    db.commit()
    return {"message": "Role assigned to user"}
@router.post("/verify-email/{token}")
def verify_email(
    token: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Verify user email.
    """
    user = verify_email_verification_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    user.is_verified = True
    db.commit()

    return {"message": "Email verified successfully"}

@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    email: EmailStr,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Request a password reset.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if the email is registered or not
        return {"message": "If the email is registered, a password reset link has been sent."}

    reset_token = create_password_reset_token(user.id)
    send_password_reset_email(email, reset_token)

    return {"message": "If the email is registered, a password reset link has been sent."}

@router.post("/password-reset/{token}", response_model=Token)
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password using a valid token.
    """
    user = verify_password_reset_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    if len(new_password) < settings.PASSWORD_MIN_LENGTH or len(new_password) > settings.PASSWORD_MAX_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be between {settings.PASSWORD_MIN_LENGTH} and {settings.PASSWORD_MAX_LENGTH} characters",
        )

    user.hashed_password = get_password_hash(new_password)
    db.commit()

    # Generate new access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
def verify_email(
    token: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Verify user email.
    """
    user = verify_email_verification_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    user.is_verified = True
    db.commit()

    return {"message": "Email verified successfully"}
@router.get("/me", response_model=UserResponse)
def get_current_user(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get the current user.
    """
    return current_user

@router.put("/me", response_model=UserResponse)
def update_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Update the current user's profile.
    """
    user = current_user
    user.full_name = user_update.full_name
    user.email = user_update.email
    user.username = user_update.username
    db.commit()
    db.refresh(user)
    return user

@router.post("/change-password")
def change_password(
    password_change: PasswordChange,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Change the current user's password.
    """
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )

    if len(password_change.new_password) < settings.PASSWORD_MIN_LENGTH or len(password_change.new_password) > settings.PASSWORD_MAX_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be between {settings.PASSWORD_MIN_LENGTH} and {settings.PASSWORD_MAX_LENGTH} characters",
        )

    current_user.hashed_password = get_password_hash(password_change.new_password)
    db.commit()
    return {"message": "Password changed successfully"}
from app.core.logging import get_logger

logger = get_logger()

@router.post("/register", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Register a new user.
    """
    try:
        # Registration logic
        logger.info(f"User {user_in.email} registered")
        return user
    except Exception as e:
        logger.error(f"Error registering user {user_in.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error registering user"
        )

@router.post("/login", response_model=Token, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    try:
        # Login logic
        logger.info(f"User {form_data.username} logged in")
        return tokens
    except Exception as e:
        logger.error(f"Error logging in user {form_data.username}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error logging in user"
        )
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@router.post("/login", response_model=Token, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    # Login logic
    ...

@router.post("/register", response_model=UserResponse, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_PER_MINUTE, seconds=60))])
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAILS_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_TLS=settings.SMTP_TLS,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER='./templates'
)

async def send_password_reset_email(email: str, reset_token: str):
    message = MessageSchema(
        subject="Password Reset",
        recipients=[email],
        template_body={
            "reset_token": reset_token
        },
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name="password_reset.html")

@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    email: EmailStr,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Request a password reset.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if the email is registered or not
        return {"message": "If the email is registered, a password reset link has been sent."}

    reset_token = create_password_reset_token(user.id)
    asyncio.create_task(send_password_reset_email(email, reset_token))

    return {"message": "If the email is registered, a password reset link has been sent."}
@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    email: EmailStr,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Request a password reset.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if the email is registered or not
        return {"message": "If the email is registered, a password reset link has been sent."}

    reset_token = create_password_reset_token(user.id)
    send_password_reset_email(email, reset_token)

    return {"message": "If the email is registered, a password reset link has been sent."}

@router.post("/password-reset/{token}", response_model=Token)
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password using a valid token.
    """
    user = verify_password_reset_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    if len(new_password) < settings.PASSWORD_MIN_LENGTH or len(new_password) > settings.PASSWORD_MAX_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be between {settings.PASSWORD_MIN_LENGTH} and {settings.PASSWORD_MAX_LENGTH} characters",
        )

    user.hashed_password = get_password_hash(new_password)
    db.commit()

    # Generate new access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
    Register a new user.
    """
    # Registration logic
    ...

@app.on_event("startup")
async def startup():
    await FastAPILimiter.init(settings.REDIS_HOST, settings.REDIS_PORT)
def register(
    user_in: UserCreate,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Register a new user.
    """
    # Check if user exists
    user = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered",
        )
    
    # Create new user
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@router.post("/login", response_model=Token)
def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login.
    """
    # Try to authenticate
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive",
        )
    
    if settings.EMAIL_VERIFICATION_REQUIRED and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email not verified",
        )
    
    # Create access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/refresh", response_model=Token)
@router.post("/password-reset", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    email: EmailStr,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Request a password reset.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if the email is registered or not
        return {"message": "If the email is registered, a password reset link has been sent."}

    reset_token = create_password_reset_token(user.id)
    send_password_reset_email(email, reset_token)

    return {"message": "If the email is registered, a password reset link has been sent."}
def refresh_token(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """
    Refresh access token.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
@router.post("/roles", response_model=Role)
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Create a new role.
    """
    role = db.query(Role).filter(Role.name == role_in.name).first()
    if role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role with this name already exists",
        )

    role = Role(
        name=role_in.name,
        description=role_in.description,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@router.post("/permissions", response_model=Permission)
def create_permission(
    permission_in: PermissionCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Create a new permission.
    """
    permission = db.query(Permission).filter(Permission.name == permission_in.name).first()
    if permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission with this name already exists",
        )

    permission = Permission(
        name=permission_in.name,
        description=permission_in.description,
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission

@router.post("/roles/{role_id}/permissions/{permission_id}")
def add_permission_to_role(
    role_id: int,
    permission_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Add a permission to a role.
    """
    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    permission = db.query(Permission).get(permission_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )

    role.permissions.append(permission)
    db.commit()
    return {"message": "Permission added to role"}

@router.post("/users/{user_id}/roles/{role_id}")
def assign_role_to_user(
    user_id: int,
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_superuser),
) -> Any:
    """
    Assign a role to a user.
    """
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    role = db.query(Role).get(role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found",
        )

    user.roles.append(role)
    db.commit()
    return {"message": "Role assigned to user"}
@router.post("/password-reset/{token}", response_model=Token)
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Reset password using a valid token.
    """
    user = verify_password_reset_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    if len(new_password) < settings.PASSWORD_MIN_LENGTH or len(new_password) > settings.PASSWORD_MAX_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password must be between {settings.PASSWORD_MIN_LENGTH} and {settings.PASSWORD_MAX_LENGTH} characters",
        )

    user.hashed_password = get_password_hash(new_password)
    db.commit()

    # Generate new access and refresh tokens
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = create_access_token(
        user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        user.id, expires_delta=refresh_token_expires
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = create_access_token(
        current_user.id, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        current_user.id, expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@router.post("/verify-email/{token}")
def verify_email(
    token: str,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Verify user email.
    """
    user = verify_email_token(token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )
    
    user.is_verified = True
    db.commit()
    
    return {"message": "Email verified successfully"}