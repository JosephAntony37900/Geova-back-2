# TFLuna/infraestructure/routes/routes_tf.py
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from TFLuna.domain.entities.sensor_tf import SensorTFLuna as SensorTF
from TFLuna.infraestructure.ws.ws_manager import WebSocketManager

router_ws_tf = APIRouter()
ws_manager = WebSocketManager()
router = APIRouter()

@router.get("/tfluna/sensor")
async def get_sensor(request: Request, event: bool = False):
    controller = request.app.state.tf_controller
    data = await controller.get_tf_data(event=event)
    return data.dict() if data else {"error": "No data"}

@router.post("/tfluna/sensor")
async def post_sensor(request: Request, payload: SensorTF):
    controller = request.app.state.tf_controller
    result = await controller.create_sensor(payload)
    return JSONResponse(content=result)

@router.put("/tfluna/sensor/{sensor_id}")
async def put_sensor(request: Request, sensor_id: int, payload: SensorTF):
    controller = request.app.state.tf_controller
    result = await controller.update_sensor(sensor_id, payload)

    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.put("/tfluna/sensor/{sensor_id}/dual")
async def put_dual_sensor(request: Request, sensor_id: int, payload: SensorTF):
    controller = request.app.state.tf_controller
    result = await controller.update_dual_sensor(sensor_id, payload)

    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=400)

@router.delete("/tfluna/sensor/project/{project_id}")
async def delete_sensor_by_project(request: Request, project_id: int):
    controller = request.app.state.tf_controller
    result = await controller.delete_sensor(project_id)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.delete("/tfluna/sensor/{record_id}")
async def delete_sensor_by_id(request: Request, record_id: int):
    controller = request.app.state.tf_controller
    result = await controller.delete_sensor_by_id(record_id)
    
    if result.get("success", True):
        return JSONResponse(content=result)
    else:
        return JSONResponse(content=result, status_code=404)

@router.get("/tfluna/sensor/{project_id}")
async def get_sensor_by_project_id(request: Request, project_id: int):
    controller = request.app.state.tf_controller
    data = await controller.get_by_project_id(project_id)
    if data:
        return data
    return JSONResponse(content={"error": "No se encontró medición para ese proyecto"}, status_code=404)

@router_ws_tf.websocket("/tfluna/sensor/ws")
async def tf_luna_ws(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

@router.get("/tfluna/debug/diagnosis")
async def get_tf_diagnosis(request: Request):
    """Endpoint para diagnóstico del sistema TF-Luna"""
    diagnosis = await diagnose_tf_system()
    return diagnosis

@router.get("/tfluna/debug/websocket-stats")
async def get_websocket_stats(request: Request):
    """Endpoint para obtener estadísticas del WebSocket"""
    return ws_manager.get_stats()

# Agregar esta ruta a routes_tf.py para debugging

@router.get("/tfluna/debug/data-structure")
async def get_data_structure_debug(request: Request):
    """Debug: Ver la estructura exacta de los datos que se envían"""
    try:
        controller = request.app.state.tf_controller
        
        # Obtener datos del sensor
        sensor_data = await controller.get_tf_data(event=False)
        
        if not sensor_data:
            return {
                "error": "No hay datos del sensor disponibles",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Convertir a dict como lo hace el WebSocket
        sensor_dict = sensor_data.dict()
        
        # Simular el enhanced_data que se envía por WebSocket
        enhanced_data = {
            **sensor_dict,
            "message_id": 999,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "sensor_data",
            "sensor_type": "TF-Luna",
            "total_connections": 1
        }
        
        return {
            "raw_sensor_object": str(sensor_data),
            "sensor_dict": sensor_dict,
            "enhanced_data_sent_via_websocket": enhanced_data,
            "field_types": {
                field: type(value).__name__ 
                for field, value in sensor_dict.items()
            },
            "available_fields": list(sensor_dict.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        import traceback
        return {
            "error": f"Error obteniendo estructura: {str(e)}",
            "traceback": traceback.format_exc(),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/tfluna/debug/compare-data")
async def compare_data_formats(request: Request):
    """Comparar datos del sensor vs datos enviados por WebSocket"""
    try:
        controller = request.app.state.tf_controller
        
        # Obtener datos como HTTP
        http_data = await controller.get_tf_data(event=False)
        
        if not http_data:
            return {"error": "No hay datos disponibles"}
        
        # Simular el procesamiento del WebSocket
        ws_data = {
            **http_data.dict(),
            "message_id": 999,
            "timestamp": datetime.utcnow().isoformat(),
            "type": "sensor_data",
            "sensor_type": "TF-Luna"
        }
        
        return {
            "http_endpoint_data": http_data.dict(),
            "websocket_data": ws_data,
            "differences": {
                "additional_fields_in_ws": [
                    key for key in ws_data.keys() 
                    if key not in http_data.dict().keys()
                ],
                "missing_fields_in_ws": [
                    key for key in http_data.dict().keys() 
                    if key not in ws_data.keys()
                ]
            },
            "sample_frontend_access": {
                "distancia_cm": f"data.distancia_cm = {ws_data.get('distancia_cm', 'undefined')}",
                "distancia_m": f"data.distancia_m = {ws_data.get('distancia_m', 'undefined')}",
                "temperatura": f"data.temperatura = {ws_data.get('temperatura', 'undefined')}",
                "fuerza_senal": f"data.fuerza_senal = {ws_data.get('fuerza_senal', 'undefined')}",
                "id_project": f"data.id_project = {ws_data.get('id_project', 'undefined')}"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }