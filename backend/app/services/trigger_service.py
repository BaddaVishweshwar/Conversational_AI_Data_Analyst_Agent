from sqlalchemy.orm import Session
from ..models import Trigger, Dataset, DataConnection
from .data_service import data_service
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TriggerService:
    def evaluate_trigger(self, db: Session, trigger_id: int):
        """Evaluate a specific trigger against its dataset"""
        trigger = db.query(Trigger).filter(Trigger.id == trigger_id).first()
        if not trigger or not trigger.is_active:
            return None
            
        dataset = db.query(Dataset).filter(Dataset.id == trigger.dataset_id).first()
        if not dataset:
            return None
            
        try:
            # Prepare execution context
            df = None
            connection = None
            if dataset.connection_id:
                connection = db.query(DataConnection).filter(DataConnection.id == dataset.connection_id).first()
            else:
                df = data_service.parse_file(dataset.file_path, dataset.file_type)
            
            # Execute the condition SQL (should return a single scalar value)
            result = data_service.execute_sql_query(
                sql_query=trigger.condition_sql,
                df=df,
                connection=connection
            )
            
            if not result["success"] or not result["data"]:
                return None
                
            # Assume first column of first row is the value
            actual_value = list(result["data"][0].values())[0]
            
            # Comparison logic
            is_triggered = False
            threshold = float(trigger.threshold)
            val = float(actual_value)
            
            if trigger.operator == ">": is_triggered = val > threshold
            elif trigger.operator == "<": is_triggered = val < threshold
            elif trigger.operator == "=": is_triggered = val == threshold
            elif trigger.operator == ">=": is_triggered = val >= threshold
            elif trigger.operator == "<=": is_triggered = val <= threshold
            
            if is_triggered:
                trigger.last_triggered = datetime.utcnow()
                db.commit()
                logger.info(f"🔔 Trigger '{trigger.name}' fired! Value: {val} {trigger.operator} {threshold}")
                return {
                    "triggered": True,
                    "name": trigger.name,
                    "value": val,
                    "threshold": threshold,
                    "operator": trigger.operator
                }
            
            return {"triggered": False}
        except Exception as e:
            logger.error(f"Error evaluating trigger {trigger_id}: {e}")
            return None

trigger_service = TriggerService()
