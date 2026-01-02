from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models import User, DataConnection
from ..routes.auth import get_current_user
from ..services.connection_service import connection_service

router = APIRouter(prefix="/connections", tags=["Connections"])

class ConnectionCreate(BaseModel):
    name: str
    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    additional_params: Optional[dict] = {}

class ConnectionResponse(BaseModel):
    id: int
    name: str
    type: str
    host: Optional[str]
    port: Optional[int]
    database: Optional[str]
    username: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/", response_model=ConnectionResponse)
async def create_connection(
    conn_data: ConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new database connection"""
    conn = DataConnection(**conn_data.dict(), user_id=current_user.id)
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn

@router.get("/", response_model=List[ConnectionResponse])
async def list_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all database connections for the user"""
    return db.query(DataConnection).filter(DataConnection.user_id == current_user.id).all()

@router.post("/{connection_id}/test")
async def test_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Test a database connection"""
    conn = db.query(DataConnection).filter(
        DataConnection.id == connection_id, 
        DataConnection.user_id == current_user.id
    ).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    return connection_service.test_connection(conn)

@router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a database connection"""
    conn = db.query(DataConnection).filter(
        DataConnection.id == connection_id, 
        DataConnection.user_id == current_user.id
    ).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    db.delete(conn)
    db.commit()
    return None

@router.get("/{connection_id}/tables", response_model=List[str])
async def list_connection_tables(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List tables in a database connection"""
    conn = db.query(DataConnection).filter(
        DataConnection.id == connection_id, 
        DataConnection.user_id == current_user.id
    ).first()
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return connection_service.get_tables(conn)
