from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import User, Dashboard
from ..routes.auth import get_current_user

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])

class DashboardCreate(BaseModel):
    name: str = "My Dashboard"
    description: Optional[str] = None
    layout: Optional[dict] = {}
    widgets: Optional[list] = []

class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    layout: Optional[dict] = None
    widgets: Optional[list] = None

class DashboardResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    layout: Optional[dict]
    widgets: Optional[list]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/", response_model=DashboardResponse)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new dashboard"""
    dashboard = Dashboard(**dashboard_data.dict(), user_id=current_user.id)
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return dashboard

@router.get("/", response_model=List[DashboardResponse])
async def list_dashboards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all dashboards for the user"""
    return db.query(Dashboard).filter(Dashboard.user_id == current_user.id).all()

@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific dashboard"""
    dashboard = db.query(Dashboard).filter(
        Dashboard.id == dashboard_id, 
        Dashboard.user_id == current_user.id
    ).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard

@router.patch("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: int,
    dashboard_data: DashboardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a dashboard layout or widgets"""
    dashboard = db.query(Dashboard).filter(
        Dashboard.id == dashboard_id, 
        Dashboard.user_id == current_user.id
    ).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    data = dashboard_data.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(dashboard, key, value)
    
    db.commit()
    db.refresh(dashboard)
    return dashboard

@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a dashboard"""
    dashboard = db.query(Dashboard).filter(
        Dashboard.id == dashboard_id, 
        Dashboard.user_id == current_user.id
    ).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    db.delete(dashboard)
    db.commit()
    return None

class WidgetCreate(BaseModel):
    title: str
    type: str # 'chart' or 'query'
    data_source: str
    viz_config: Optional[dict] = None
    python_chart: Optional[str] = None
    sql: Optional[str] = None

@router.post("/{dashboard_id}/widgets", response_model=DashboardResponse)
async def add_widget(
    dashboard_id: int,
    widget: WidgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a widget to a dashboard"""
    dashboard = db.query(Dashboard).filter(
        Dashboard.id == dashboard_id, 
        Dashboard.user_id == current_user.id
    ).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    
    # Initialize widgets list if None
    current_widgets = dashboard.widgets or []
    
    # Create new widget dict
    new_widget = widget.dict()
    new_widget["id"] = datetime.now().timestamp() # Simple unique ID
    new_widget["layout"] = "half" # Default layout
    
    # Append
    current_widgets.append(new_widget)
    
    # Update dashboard
    dashboard.widgets = current_widgets
    
    # Force update (SQLAlchemy sometimes needs help with JSON mutation)
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(dashboard, "widgets")
    
    db.commit()
    db.refresh(dashboard)
    return dashboard
