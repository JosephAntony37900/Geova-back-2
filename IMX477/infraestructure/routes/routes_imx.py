from fastapi import APIRouter, Request

router = APIRouter(prefix="/camera", tags=["IMX477"])

@router.get("/analyze")
async def analyze(req: Request, event: bool = False):
    data = await req.app.state.imx_controller.get_imx_data(event=event)
    return data.dict() if data else {"error": "No se pudo procesar el frame"}
