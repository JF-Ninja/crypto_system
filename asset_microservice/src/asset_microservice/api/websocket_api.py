from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from asset_microservice.websockets_manager import manager

router = APIRouter(prefix="/ws/assets", tags=["Assets API Management"])

@router.websocket('/get_assets')
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast("Connection closed")

