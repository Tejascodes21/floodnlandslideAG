import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.session import get_db
from app.db.schemas import User, Volunteer
from app.core.security import verify_password, get_password_hash, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "Citizen"  # Citizen, Volunteer, Researcher, NGO, Government, Admin
    language: str = "en"
    emergency_contact: str = None

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    # Check if user exists
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed = get_password_hash(req.password)
    new_user = User(
        username=req.username,
        hashed_password=hashed,
        role=req.role,
        language=req.language,
        emergency_contact=req.emergency_contact
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # If registering as a volunteer, seed a default Volunteer profile
    if req.role == "Volunteer":
        new_vol = Volunteer(
            user_id=new_user.id,
            full_name=req.username.capitalize(),
            skills="Rescue, First Aid",
            phone=req.emergency_contact or "9876543210",
            vehicle_type="4x4 SUV",
            lat=round(19.076 + random.uniform(-0.02, 0.02), 4),
            lon=round(72.877 + random.uniform(-0.02, 0.02), 4),
            active=True
        )
        db.add(new_vol)
        db.commit()
        
    return {"status": "success", "username": new_user.username, "role": new_user.role}

@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
        
    access_token = create_access_token(subject=user.username, role=user.role)
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": user.role, 
        "username": user.username,
        "language": user.language
    }

def seed_default_users(db: Session):
    """Utility to seed standard credentials so the platform is ready on start."""
    defaults = [
        {"username": "citizen", "password": "password123", "role": "Citizen", "contact": "9999999901"},
        {"username": "volunteer", "password": "password123", "role": "Volunteer", "contact": "9999999902"},
        {"username": "ngo", "password": "password123", "role": "NGO", "contact": "9999999903"},
        {"username": "govt", "password": "password123", "role": "Government Authority", "contact": "9999999904"},
        {"username": "admin", "password": "password123", "role": "Admin", "contact": "9999999905"}
    ]
    
    for u in defaults:
        exists = db.query(User).filter(User.username == u["username"]).first()
        if not exists:
            hashed = get_password_hash(u["password"])
            new_user = User(
                username=u["username"],
                hashed_password=hashed,
                role=u["role"],
                language="en",
                emergency_contact=u["contact"]
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Seed volunteer profiles
            if u["role"] == "Volunteer":
                # Check if volunteer profile exists
                v_exists = db.query(Volunteer).filter(Volunteer.full_name == "Volunteer Captain").first()
                if not v_exists:
                    new_vol = Volunteer(
                        user_id=new_user.id,
                        full_name="Volunteer Captain",
                        skills="Medical Aid, Fast Boat, Water Rescue",
                        phone="9876543210",
                        vehicle_type="Inflatable Powerboat",
                        lat=19.060,  # near Mumbai delta
                        lon=72.845,
                        active=True
                    )
                    db.add(new_vol)
                    db.commit()
                    
                    # Seed secondary volunteer
                    new_vol2 = Volunteer(
                        user_id=new_user.id,
                        full_name="Rescue Specialist Sunil",
                        skills="High Slope Climber, Landslide Clearance",
                        phone="9876543211",
                        vehicle_type="4x4 Rescue Truck",
                        lat=19.110,
                        lon=72.880,
                        active=True
                    )
                    db.add(new_vol2)
                    db.commit()
    print("Default GeoShield users seeded.")
