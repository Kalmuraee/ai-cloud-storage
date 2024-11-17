from typing import Dict, List
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User, Role, Permission


def init_roles(db: Session) -> Dict[str, Role]:
    """Initialize default roles."""
    default_roles = {
        "admin": "Full system administrator access",
        "user": "Standard user access",
    }
    
    roles = {}
    for role_name, description in default_roles.items():
        role = db.query(Role).filter(Role.name == role_name).first()
        if not role:
            role = Role(name=role_name, description=description)
            db.add(role)
            db.commit()
            db.refresh(role)
        roles[role_name] = role
    
    return roles


def init_permissions(db: Session) -> Dict[str, Permission]:
    """Initialize default permissions."""
    default_permissions = {
        # User management permissions
        "user:create": "Create new users",
        "user:read": "Read user information",
        "user:update": "Update user information",
        "user:delete": "Delete users",
        
        # Role management permissions
        "role:create": "Create new roles",
        "role:read": "Read role information",
        "role:update": "Update role information",
        "role:delete": "Delete roles",
        
        # File management permissions
        "file:upload": "Upload files",
        "file:download": "Download files",
        "file:delete": "Delete files",
        "file:share": "Share files with others",
        
        # System management permissions
        "system:manage": "Manage system settings",
        "system:monitor": "Monitor system status",
    }
    
    permissions = {}
    for perm_name, description in default_permissions.items():
        permission = db.query(Permission).filter(Permission.name == perm_name).first()
        if not permission:
            permission = Permission(name=perm_name, description=description)
            db.add(permission)
            db.commit()
            db.refresh(permission)
        permissions[perm_name] = permission
    
    return permissions


def assign_role_permissions(
    db: Session,
    roles: Dict[str, Role],
    permissions: Dict[str, Permission]
) -> None:
    """Assign permissions to roles."""
    # Admin role gets all permissions
    admin_role = roles["admin"]
    admin_role.permissions = list(permissions.values())
    
    # User role gets basic permissions
    user_role = roles["user"]
    user_permissions = [
        permissions["user:read"],
        permissions["file:upload"],
        permissions["file:download"],
        permissions["file:delete"],
        permissions["file:share"],
    ]
    user_role.permissions = user_permissions
    
    db.commit()


def create_initial_superuser(db: Session) -> None:
    """Create initial superuser if it doesn't exist."""
    email = "admin@example.com"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            username="admin",
            hashed_password=get_password_hash("admin123"),  # Change in production
            full_name="System Administrator",
            is_superuser=True,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Assign admin role
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role:
            user.roles = [admin_role]
            db.commit()


def init_db(db: Session) -> None:
    """Initialize database with default data."""
    # Create roles
    roles = init_roles(db)
    
    # Create permissions
    permissions = init_permissions(db)
    
    # Assign permissions to roles
    assign_role_permissions(db, roles, permissions)
    
    # Create superuser
    create_initial_superuser(db)