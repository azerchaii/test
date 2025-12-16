"""
API Gateway - REST API entry point for the web application.
Translates REST requests to gRPC calls to backend services.
"""
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from jose import JWTError, jwt

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ==================== Configuration ====================

class Config:
    INVENTORY_GRPC_HOST = os.getenv("INVENTORY_GRPC_HOST", "localhost:50051")
    PROCUREMENT_GRPC_HOST = os.getenv("PROCUREMENT_GRPC_HOST", "localhost:50052")
    REQUEST_GRPC_HOST = os.getenv("REQUEST_GRPC_HOST", "localhost:50053")
    NOTIFICATION_GRPC_HOST = os.getenv("NOTIFICATION_GRPC_HOST", "localhost:50054")
    JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


# ==================== Pydantic Models ====================

class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    id: str
    username: str
    email: str
    role: str


class MaterialCreate(BaseModel):
    name: str
    unit: str = Field(..., description="Units: pieces, meters, kg, liters, m3, m2")
    category: str
    initial_quantity: int = 0
    min_threshold: int = 10


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None
    min_threshold: Optional[int] = None


class Material(BaseModel):
    id: str
    name: str
    unit: str
    category: str
    quantity: int
    reserved: int
    available: int
    min_threshold: int
    is_low_stock: bool
    created_at: str
    updated_at: str


class MaterialList(BaseModel):
    items: List[Material]
    total: int
    page: int
    page_size: int


class AvailabilityCheck(BaseModel):
    material_id: str
    is_available: bool
    available_quantity: int
    requested_quantity: int
    shortage: int


class RequestItemInput(BaseModel):
    material_id: str
    material_name: str = ""
    quantity: int


class MaterialRequestCreate(BaseModel):
    brigade_id: str
    project_id: Optional[str] = None
    items: List[RequestItemInput]
    priority: str = "MEDIUM"
    notes: Optional[str] = None


class MaterialRequest(BaseModel):
    id: str
    brigade_id: str
    project_id: Optional[str]
    items: List[dict]
    status: str
    priority: str
    created_by: str
    created_at: str
    notes: Optional[str]


class PurchaseOrder(BaseModel):
    id: str
    material_id: str
    material_name: str
    supplier_id: str
    supplier_name: str
    quantity: int
    unit_price: float
    total_price: float
    status: str
    expected_delivery: Optional[str]
    created_at: str


class Supplier(BaseModel):
    id: str
    name: str
    email: str
    phone: str
    rating: float
    is_active: bool


# ==================== Authentication ====================

security = HTTPBearer()

# Mock users for demo (in production, use database)
MOCK_USERS = {
    "admin": {
        "id": "user-001",
        "username": "admin",
        "email": "admin@construction.com",
        "password": "admin123",
        "role": "admin",
    },
    "brigadier": {
        "id": "user-002",
        "username": "brigadier",
        "email": "brigadier@construction.com",
        "password": "brigade123",
        "role": "brigadier",
    },
}


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=Config.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    payload = verify_token(credentials.credentials)
    username = payload.get("sub")
    if username not in MOCK_USERS:
        raise HTTPException(status_code=401, detail="User not found")
    return MOCK_USERS[username]


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ==================== Mock Data (for demo without gRPC) ====================

MOCK_MATERIALS = [
    {
        "id": "mat-001",
        "name": "Балка стальная 200x100",
        "unit": "pieces",
        "category": "Металлоконструкции",
        "quantity": 50,
        "reserved": 5,
        "available": 45,
        "min_threshold": 10,
        "is_low_stock": False,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-15T00:00:00",
    },
    {
        "id": "mat-002",
        "name": "Цемент М500",
        "unit": "kg",
        "category": "Сыпучие материалы",
        "quantity": 5000,
        "reserved": 500,
        "available": 4500,
        "min_threshold": 1000,
        "is_low_stock": False,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-15T00:00:00",
    },
    {
        "id": "mat-003",
        "name": "Кирпич красный",
        "unit": "pieces",
        "category": "Кирпич",
        "quantity": 8000,
        "reserved": 2000,
        "available": 6000,
        "min_threshold": 2000,
        "is_low_stock": False,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-15T00:00:00",
    },
]

MOCK_SUPPLIERS = [
    {
        "id": "sup-001",
        "name": "СтройМеталл",
        "email": "sales@stroymetal.ru",
        "phone": "+7-495-123-4567",
        "rating": 4.8,
        "is_active": True,
    },
    {
        "id": "sup-002",
        "name": "БетонПлюс",
        "email": "order@betonplus.ru",
        "phone": "+7-495-987-6543",
        "rating": 4.5,
        "is_active": True,
    },
]

MOCK_REQUESTS = []
MOCK_ORDERS = []


# ==================== FastAPI App ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API Gateway...")
    logger.info(f"Inventory Service: {Config.INVENTORY_GRPC_HOST}")
    logger.info(f"Procurement Service: {Config.PROCUREMENT_GRPC_HOST}")
    yield
    logger.info("Shutting down API Gateway...")


app = FastAPI(
    title="Construction Materials API",
    description="REST API для системы управления строительными материалами",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Auth Endpoints ====================

@app.post("/api/v1/auth/login", response_model=Token, tags=["Authentication"])
async def login(credentials: UserLogin):
    """Authenticate user and return JWT token."""
    user = MOCK_USERS.get(credentials.username)
    if not user or user["password"] != credentials.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return Token(access_token=token)


@app.get("/api/v1/auth/me", response_model=UserInfo, tags=["Authentication"])
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user info."""
    return UserInfo(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        role=user["role"],
    )


# ==================== Inventory Endpoints ====================

@app.get("/api/v1/inventory/materials", response_model=MaterialList, tags=["Inventory"])
async def list_materials(
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(get_current_user),
):
    """Get list of materials."""
    # In production, this would call Inventory Service via gRPC
    materials = MOCK_MATERIALS
    if category:
        materials = [m for m in materials if m["category"] == category]
    
    return MaterialList(
        items=[Material(**m) for m in materials],
        total=len(materials),
        page=page,
        page_size=page_size,
    )


@app.get("/api/v1/inventory/materials/{material_id}", response_model=Material, tags=["Inventory"])
async def get_material(
    material_id: str,
    user: dict = Depends(get_current_user),
):
    """Get material by ID."""
    material = next((m for m in MOCK_MATERIALS if m["id"] == material_id), None)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    return Material(**material)


@app.post("/api/v1/inventory/materials", response_model=Material, tags=["Inventory"])
async def create_material(
    data: MaterialCreate,
    user: dict = Depends(require_admin),
):
    """Create a new material (admin only)."""
    import uuid
    new_material = {
        "id": str(uuid.uuid4()),
        "name": data.name,
        "unit": data.unit,
        "category": data.category,
        "quantity": data.initial_quantity,
        "reserved": 0,
        "available": data.initial_quantity,
        "min_threshold": data.min_threshold,
        "is_low_stock": data.initial_quantity < data.min_threshold,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    MOCK_MATERIALS.append(new_material)
    return Material(**new_material)


@app.get("/api/v1/inventory/materials/{material_id}/availability", tags=["Inventory"])
async def check_availability(
    material_id: str,
    quantity: int,
    user: dict = Depends(get_current_user),
):
    """Check material availability."""
    material = next((m for m in MOCK_MATERIALS if m["id"] == material_id), None)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    is_available = material["available"] >= quantity
    shortage = max(0, quantity - material["available"])
    
    return AvailabilityCheck(
        material_id=material_id,
        is_available=is_available,
        available_quantity=material["available"],
        requested_quantity=quantity,
        shortage=shortage,
    )


@app.get("/api/v1/inventory/low-stock", response_model=List[Material], tags=["Inventory"])
async def get_low_stock(user: dict = Depends(get_current_user)):
    """Get materials below threshold."""
    low_stock = [m for m in MOCK_MATERIALS if m["is_low_stock"]]
    return [Material(**m) for m in low_stock]


# ==================== Requests Endpoints ====================

@app.post("/api/v1/requests", response_model=MaterialRequest, tags=["Requests"])
async def create_request(
    data: MaterialRequestCreate,
    user: dict = Depends(get_current_user),
):
    """Create a material request."""
    import uuid
    new_request = {
        "id": str(uuid.uuid4()),
        "brigade_id": data.brigade_id,
        "project_id": data.project_id,
        "items": [item.dict() for item in data.items],
        "status": "PENDING",
        "priority": data.priority,
        "created_by": user["id"],
        "created_at": datetime.utcnow().isoformat(),
        "notes": data.notes,
    }
    MOCK_REQUESTS.append(new_request)
    
    # Check availability and trigger auto-procurement if needed
    for item in data.items:
        material = next((m for m in MOCK_MATERIALS if m["id"] == item.material_id), None)
        if material and material["available"] < item.quantity:
            logger.info(f"Shortage detected for {item.material_id}, triggering auto-procurement")
            # In production, this would publish to RabbitMQ
    
    return MaterialRequest(**new_request)


@app.get("/api/v1/requests", response_model=List[MaterialRequest], tags=["Requests"])
async def list_requests(
    status: Optional[str] = None,
    brigade_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Get list of requests."""
    requests = MOCK_REQUESTS
    if status:
        requests = [r for r in requests if r["status"] == status]
    if brigade_id:
        requests = [r for r in requests if r["brigade_id"] == brigade_id]
    return [MaterialRequest(**r) for r in requests]


# ==================== Procurement Endpoints ====================

@app.get("/api/v1/procurement/orders", response_model=List[PurchaseOrder], tags=["Procurement"])
async def list_orders(
    status: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Get list of purchase orders."""
    orders = MOCK_ORDERS
    if status:
        orders = [o for o in orders if o["status"] == status]
    return [PurchaseOrder(**o) for o in orders]


@app.get("/api/v1/procurement/suppliers", response_model=List[Supplier], tags=["Procurement"])
async def list_suppliers(user: dict = Depends(get_current_user)):
    """Get list of suppliers."""
    return [Supplier(**s) for s in MOCK_SUPPLIERS]


# ==================== Health Check ====================

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
