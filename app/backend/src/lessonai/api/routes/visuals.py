from fastapi import APIRouter, HTTPException, Depends
from lessonai.services.visual_requirements import confirm_requirement, checked_requirement, VisualError
from lessonai.services.geometry_scene import build_scene
from lessonai.services.workbench_visuals import build_verified_bbt, sample_workbench_graph
from lessonai.services.math_expression import ExpressionError
from lessonai.core.jobs import JobError

from lessonai.core.ownership import require_owner

router = APIRouter(prefix="/api/v1/visuals", tags=["Visual requirements"])


@router.post("/confirm")
def confirm(data: dict, owner=Depends(require_owner)):
    try:
        return confirm_requirement(data)
    except (ValueError, KeyError, TypeError) as error:
        raise HTTPException(422, detail={"code": "visual_invalid", "message": str(error)}) from error


@router.post("/scene")
def scene(spec: dict):
    try:
        checked_requirement(spec)
        nested = spec.get("data") if isinstance(spec.get("data"), dict) else {}
        return build_scene({**nested, **{k: v for k, v in spec.items() if k != "data"}})
    except VisualError as error:
        raise HTTPException(409, detail={"code": error.code, "message": str(error)}) from error


@router.post("/graph/sample")
def graph_sample(spec: dict):
    try:
        return sample_workbench_graph(spec)
    except VisualError as error:
        raise HTTPException(409, detail={"code": error.code, "message": str(error)}) from error
    except ExpressionError as error:
        raise HTTPException(422, detail=error.detail()) from error
    except JobError as error:
        status = 503 if error.code == "job_busy" else 504 if error.code == "job_timeout" else 422
        raise HTTPException(status, detail={"code": error.code, "message": str(error)}) from error
    except (ValueError, KeyError, TypeError) as error:
        raise HTTPException(422, detail={"code": "graph_invalid", "message": str(error)}) from error


@router.post("/bbt")
def bbt_table(spec: dict):
    try:
        return build_verified_bbt(spec)
    except VisualError as error:
        raise HTTPException(409, detail={"code": error.code, "message": str(error)}) from error
    except ExpressionError as error:
        raise HTTPException(422, detail=error.detail()) from error
    except (ValueError, KeyError, TypeError) as error:
        raise HTTPException(422, detail={"code": "bbt_invalid", "message": str(error)}) from error
