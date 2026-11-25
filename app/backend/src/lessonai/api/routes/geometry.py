"""Legacy unsourced geometry endpoints retired in favor of confirmed scene specs."""
from fastapi import APIRouter, HTTPException
router = APIRouter(prefix='/api/v1/geometry', tags=['Legacy geometry'])

def retired():
    raise HTTPException(410, detail={"code":"geometry_contract_retired", "message":"Cần xác nhận dữ kiện tại /api/v1/visuals/confirm rồi dựng hình tại /api/v1/visuals/scene."})

for path in ('apex-coordinates', 'edge-topology', 'unfolded-net', 'vertex-labels', 'raycast-occlusion'):
    router.add_api_route('/'+path, retired, methods=['GET'])
router.add_api_route('/parametric-coordinates', retired, methods=['POST'])
