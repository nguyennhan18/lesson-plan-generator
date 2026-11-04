#!/usr/bin/env python3
"""Current runtime acceptance. Never overwrite historical evidence."""
import argparse,json,time
from pathlib import Path
from fastapi.testclient import TestClient
from lessonai.main import create_app
from lessonai.services.math_worker import verify_equality
from lessonai.services.geometry_scene import build_scene
from lessonai.services.visual_requirements import confirm_requirement
from lessonai.schemas.slide_schema import SlideDeckSchema
from lessonai.exporters.graph_generator import generate_math_plot


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['baseline','acceptance'],required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();path=Path(args.output)
    if path.exists():parser.error('Evidence already exists; choose a new output path')
    checks={};start=time.monotonic()
    with TestClient(create_app()) as api:
        api.post('/api/v1/session')
        checks['no_sample_endpoint']=api.get('/api/v1/test-cases').status_code==404
        unsafe=api.post('/api/v1/chart/render',json={'kind':'function_plot','expression':"__import__('os').getcwd()"})
        checks['unsafe_expression_rejected']=unsafe.status_code==422
        spec={'kind':'function_plot','expression':'1/x','x_min':-2,'x_max':2,'deck_id':'audit-deck','slide_id':'audit-slide'}
        confirmation=confirm_requirement(spec);spec.update(confirmation['requirement']['spec']);spec['requirement_token']=confirmation['requirement_token']
        checks['confirmed_graph_png']=generate_math_plot(spec).startswith(b'\x89PNG')
        checks['wrong_numeric_solution_failed']=verify_equality('1+1','3')['status']=='failed'
        checks['domain_change_unverified']=verify_equality('(x^2-1)/(x-1)','x+1')['status']=='unverified'
        scene=build_scene({'polyhedron_type':'square_pyramid_at_a','height':3,'base_edge':4})
        checks['geometry_satisfies_input']=scene['vertices']['S']==[0,0,3] and scene['measurements']['volume']==16
        deck=SlideDeckSchema.model_validate({'presentation_title':'Probe','subject':'Toán học','grade':12,'slides':[{'title':'Probe','worked_solution_steps':['$1+1=3$']}]}).model_dump(mode='json')
        checks['quality_gate_blocks_wrong_step']=api.post('/api/v1/quality/check',json=deck).json()['status']=='blocked'
        checks['approval_cannot_override_error']=api.post('/api/v1/quality/approve',json={'deck':deck,'acknowledged':True}).status_code==409
        checks['error_has_request_id']=bool(unsafe.json()['detail'].get('request_id'))
    result={'stage':'runtime-upgrade','mode':args.mode,'checks':checks,'pass':all(checks.values()),'elapsed_seconds':round(time.monotonic()-start,3),'limits':['Không chứng nhận đúng toán ngoài phạm vi kiểm định','Chưa thay giáo viên duyệt chuyên môn']}
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps({'output':str(path),'pass':result['pass'],'checks':len(checks)}))
    if args.mode=='acceptance' and not result['pass']:raise SystemExit(1)

if __name__=='__main__':main()
