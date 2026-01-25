import sys
import os
import json
sys.path.append(os.path.abspath("backend"))

from frame_solver import FrameSolver
# Depending on how models are defined, we might need to instantite them
# Or maybe the solver accepts dicts if we are lucky? 
# Usually Pydantic models need instantiation or parse_obj
from models import FrameRequest, FrameNode, FrameMember, FramePointLoad, FrameUniformLoad

# Define Payload (Dict)
payload = {
    "nodes": [
        {"id": "1", "x": 0, "y": 0, "fixX": True, "fixY": True, "fixR": True},
        {"id": "2", "x": 0, "y": 4, "fixX": False, "fixY": False, "fixR": False},
        {"id": "3", "x": 5, "y": 4, "fixX": False, "fixY": False, "fixR": False},
        {"id": "4", "x": 5, "y": 0, "fixX": True, "fixY": True, "fixR": True}
    ],
    "members": [
        {"id": "1", "startNodeId": "1", "endNodeId": "2", "elasticModulus": 200, "momentOfInertia": 200, "crossSectionArea": 0.01},
        {"id": "2", "startNodeId": "2", "endNodeId": "3", "elasticModulus": 200, "momentOfInertia": 100, "crossSectionArea": 0.01},
        {"id": "3", "startNodeId": "3", "endNodeId": "4", "elasticModulus": 200, "momentOfInertia": 200, "crossSectionArea": 0.01}
    ],
    "pointLoads": [
        # Side Loads (Member Point Loads) need to be handled.
        # Check models.py or frame_solver logic for mixed loads.
        # Assuming API converts them or Solver handles 'MEMBER_POINT_LOAD' type.
        {"id": "p1", "type": "MEMBER_POINT_LOAD", "targetId": "1", "magnitudeX": 0, "magnitudeY": -20, "position": 2},
        {"id": "p2", "type": "MEMBER_POINT_LOAD", "targetId": "3", "magnitudeX": 0, "magnitudeY": -20, "position": 2}
    ],
    "uniformLoads": [
        {"id": "u1", "type": "UNIFORM_LOAD", "memberId": "2", "magnitudeX": 0, "magnitudeY": -15}
    ]
}

# Try to use Pydantic parsing if available
try:
    # Handle field aliasing (Frontend uses camelCase, Backend Pydantic might use snake_case or alias)
    # Looking at frame_solver.py: pl.magnitude_x, member.start_node_id. 
    # Frontend sends startNodeId.
    # We must ensure keys match what FrameRequest expects.
    # Usually FastAPI handles this conversion automatically.
    # For manual test, we might need to map them.
    
    # Let's try raw dict first, if fail, we map.
    
    # Map to snake_case for Pydantic if needed
    def to_snake(d):
        new_d = {}
        for k, v in d.items():
            if isinstance(v, list):
                new_d[k] = [to_snake(i) if isinstance(i, dict) else i for i in v]
            else:
                s = ''.join(['_'+c.lower() if c.isupper() else c for c in k]).lstrip('_')
                # Specific corrections
                if k == 'startNodeId': s = 'start_node_id'
                if k == 'endNodeId': s = 'end_node_id'
                if k == 'targetId': s = 'target_id'
                if k == 'memberId': s = 'member_id' 
                if k == 'elasticModulus': s = 'elastic_modulus'
                if k == 'momentOfInertia': s = 'moment_of_inertia'
                if k == 'crossSectionArea': s = 'cross_section_area'
                if k == 'fixX': s = 'fix_x'
                if k == 'fixY': s = 'fix_y'
                if k == 'fixR': s = 'fix_r'
                if k == 'magnitudeX': s = 'magnitude_x'
                if k == 'magnitudeY': s = 'magnitude_y'
                new_d[s] = v
        return new_d

    snake_payload = to_snake(payload)
    # Fix top level keys
    snake_payload['point_loads'] = snake_payload.pop('point_loads', [])
    snake_payload['uniform_loads'] = snake_payload.pop('uniform_loads', [])
    
    print("Constructing Request...")
    req = FrameRequest(**snake_payload)
    
    print("Solving...")
    solver = FrameSolver()
    result = solver.solve(req)
    
    print("Success:", result["success"])
    if not result["success"]:
        print("Error:", result.get("error"))
    else:
        print("Reactions:", result["reactions"])
        # Check member_results
        if "member_results" in result and result["member_results"]:
            print("Member Results Found:", len(result["member_results"]))
            print("M1 V-Diagram Length:", len(result["member_results"][0]["v_diagram"]))
        else:
            print("WARNING: member_results MISSING")

except Exception as e:
    print("CRASH during Pydantic/Solve:", str(e))
    import traceback
    traceback.print_exc()
