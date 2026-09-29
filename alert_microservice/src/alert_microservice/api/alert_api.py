from alert_microservice.dependencies import get_alert_service, get_current_user
from fastapi import APIRouter
from fastapi import Depends

from alert_microservice.schema.alert_schema import SAlertBase

router = APIRouter(prefix="/alerts", tags=["Alert Management"])

@router.post('/create_alert')
async def create_alert(alert: SAlertBase, service = Depends(get_alert_service), user_info: dict = Depends(get_current_user)):
    return await service.create_alert(alert, user_info)

@router.get('/alerts')
async def get_alerts(service = Depends(get_alert_service), user_info: dict = Depends(get_current_user)):
    return await service.get_all_alerts(user_info)