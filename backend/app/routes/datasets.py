from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import shutil
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from ..database import get_db
from ..models import User, Dataset
from ..routes.auth import get_current_user
from ..services.data_service import data_service
from ..config import settings

from ..services.ollama_service import ollama_service
from ..services.visualization_service import visualization_service

router = APIRouter(prefix="/datasets", tags=["Datasets"])

# Pydantic schemas
class EDAResponse(BaseModel):
    report: str
    visualization: Optional[str]
    success: bool
    error: Optional[str]
class DatasetResponse(BaseModel):
    id: int
    name: str
    filename: str
    file_type: str
    row_count: Optional[int]
    column_count: Optional[int]
    schema: Optional[dict]
    sample_data: Optional[list]
    status: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class DatasetListResponse(BaseModel):
    id: int
    name: str
    filename: str
    file_type: str
    row_count: Optional[int]
    column_count: Optional[int]
    status: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a new dataset (CSV or Excel)"""
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = Path(settings.UPLOAD_DIR) / str(current_user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = upload_dir / safe_filename
    
    # Save file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Create dataset record with processing status
    dataset = Dataset(
        name=name or file.filename,
        filename=file.filename,
        file_path=str(file_path),
        file_type=file_ext[1:],
        user_id=current_user.id,
        status="processing"
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    # Add background task
    background_tasks.add_task(process_dataset_task, dataset.id, str(file_path), file_ext[1:], db)
    
    return dataset

class DatasetFromConnection(BaseModel):
    name: str
    connection_id: int
    table_name: Optional[str] = None # Optional: Limit to specific table or use full DB context?

@router.post("/from-connection", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset_from_connection(
    data: DatasetFromConnection,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a dataset from an existing database connection"""
    from ..models import DataConnection
    
    conn = db.query(DataConnection).filter(
        DataConnection.id == data.connection_id,
        DataConnection.user_id == current_user.id
    ).first()
    
    if not conn:
        raise HTTPException(status_code=404, detail="Connection not found")
        
    # Create dataset record
    dataset = Dataset(
        name=data.name,
        filename=f"DB: {conn.name}",
        file_path=f"connection://{conn.id}", # Placeholder
        file_type=conn.type,
        user_id=current_user.id,
        connection_id=conn.id,
        status="processing"
    )
    
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    
    # Fetch schema and sample data if table name is provided
    try:
        from ..services.connection_service import connection_service
        
        if data.table_name:
            # Introspect schema
            dataset.schema = connection_service.get_table_schema(conn, data.table_name)
            
            # Fetch sample data
            dataset.sample_data = connection_service.get_sample_data(conn, data.table_name)
            
            # Estimate row count (optional optimization: fetch exact count if small table)
            # For now, we leave row_count as None or handle later.
            
        dataset.status = "completed"
        
    except Exception as e:
        print(f"Error introspecting connection: {e}")
        dataset.status = "error"
        dataset.error_message = f"Introspection failed: {str(e)}"

    db.commit()

    return dataset

def process_dataset_task(dataset_id: int, file_path: str, file_type: str, db: Session):
    """Background task to process dataset with V4 schema extraction"""
    import asyncio
    
    try:
        from ..database import SessionLocal
        from ..services.schema_extraction_service import schema_extraction_service
        
        with SessionLocal() as session:
            dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()
            if not dataset:
                return

            try:
                # Use V4 schema extraction service (includes profiling, semantic tagging, embeddings)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                extraction_result = loop.run_until_complete(
                    schema_extraction_service.extract_and_store_schema(
                        dataset_id=dataset_id,
                        file_path=file_path,
                        db=session
                    )
                )
                
                loop.close()
                
                if extraction_result['success']:
                    # Schema extraction already updated the dataset record
                    # Just mark as completed
                    dataset.status = "completed"
                    session.commit()
                    print(f"✅ Dataset {dataset_id} processed with V4 schema extraction")
                else:
                    dataset.status = "error"
                    dataset.error_message = "Schema extraction failed"
                    session.commit()
                
            except Exception as e:
                dataset.status = "error"
                dataset.error_message = str(e)
                session.commit()
                print(f"Error processing dataset {dataset_id}: {e}")
                
    except Exception as e:
        print(f"Critical error in background task: {e}")


@router.get("/", response_model=List[DatasetListResponse])
async def list_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all datasets for current user"""
    datasets = db.query(Dataset).filter(
        Dataset.user_id == current_user.id
    ).order_by(Dataset.created_at.desc()).all()
    
    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dataset details"""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return dataset


@router.get("/{dataset_id}/data")
async def get_dataset_data(
    dataset_id: int,
    limit: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full dataset data"""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    try:
        # Load full data from file
        df = data_service.parse_file(dataset.file_path, dataset.file_type)
        
        # Apply limit if specified
        if limit:
            df = df.head(limit)
        
        # Convert to list of dicts
        data = df.to_dict('records')
        columns = df.columns.tolist()
        
        return {
            "data": data,
            "columns": columns,
            "total_rows": len(df),
            "dataset_info": {
                "id": dataset.id,
                "name": dataset.name,
                "row_count": dataset.row_count,
                "column_count": dataset.column_count
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a dataset"""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Delete file
    file_path = Path(dataset.file_path)
    if file_path.exists():
        file_path.unlink()
    
    # Delete database record
    db.delete(dataset)
    db.commit()
    
    return None
@router.get("/{dataset_id}/eda", response_model=EDAResponse)
async def get_dataset_eda(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate Auto-EDA for a dataset"""
    dataset = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.user_id == current_user.id
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    try:
        # Return cached report if available (and for local files)
        # In a real app, we might want to check if the file changed
        if dataset.last_eda_report:
            # We still might want a fresh visualization, but let's stick to cached for now
            pass

        # Generate report plan
        eda_plan = ollama_service.generate_eda_report(
            schema=dataset.schema,
            sample_data=dataset.sample_data
        )
        
        if not eda_plan["success"]:
            return EDAResponse(report="", visualization=None, success=False, error=eda_plan["error"])
            
        # Execute the visualization part
        df = None
        connection = None
        if dataset.connection_id:
            from ..models import DataConnection
            connection = db.query(DataConnection).filter(DataConnection.id == dataset.connection_id).first()
        else:
            df = data_service.parse_file(dataset.file_path, dataset.file_type)

        execution_result = data_service.execute_sql_query(
            sql_query="SELECT * FROM data LIMIT 500", # Sample for EDA
            df=df,
            connection=connection
        )
        
        viz_result = visualization_service.generate_custom_chart(
            data=execution_result["data"],
            python_code=eda_plan["python"],
            title="Exploratory Analysis"
        )
        
        # Persist report
        dataset.last_eda_report = eda_plan["report"]
        db.commit()
        
        return EDAResponse(
            report=eda_plan["report"],
            visualization=viz_result["image"] if viz_result["success"] else None,
            success=True,
            error=None
        )
        
    except Exception as e:
        return EDAResponse(report="", visualization=None, success=False, error=str(e))
