
import sys
sys.path.append('backend')

from models import FrameRequest, FrameNode, FrameMember, FrameUniformLoad, FramePointLoad
from frame_solver import FrameSolver
import json

def verify():
    # User Problem 3 (Sway Frame, 18kN):
    # A(0,0) Fix, D(6,0) Fix. (Span 6m)
    # B(0,4), C(6,4). (Height 4m)
    # AB: 4m, 3I.
    # BC: 6m, 1.5I.
    # CD: 4m, 3I.
    
    nodes = [
        FrameNode(id="A", x=0, y=0, fix_x=True, fix_y=True, fix_r=True),
        FrameNode(id="B", x=0, y=4, fix_x=False, fix_y=False, fix_r=False),
        FrameNode(id="C", x=6, y=4, fix_x=False, fix_y=False, fix_r=False),
        FrameNode(id="D", x=6, y=0, fix_x=True, fix_y=True, fix_r=True),
    ]
    
    members = [
        FrameMember(id="AB", start_node_id="A", end_node_id="B", elastic_modulus=1000, moment_of_inertia=3, cross_section_area=100000),
        FrameMember(id="BC", start_node_id="B", end_node_id="C", elastic_modulus=1000, moment_of_inertia=1.5, cross_section_area=100000),
        FrameMember(id="CD", start_node_id="C", end_node_id="D", elastic_modulus=1000, moment_of_inertia=3, cross_section_area=100000),
    ]
    
    # Load: 18kN on BC, 2m from B.
    # Type: MEMBER_POINT_LOAD. Target BC. Magnitude Y = -18 (Down). Position = 2.
    
    point_loads = [
        FramePointLoad(id="PL1", type="MEMBER_POINT_LOAD", target_id="BC", magnitude_y=-18, position=2.0)
    ]
    
    req = FrameRequest(nodes=nodes, members=members, point_loads=point_loads, uniform_loads=[])
    solver = FrameSolver()
    res = solver.solve(req)
    
    print("\nResults Problem 3 (Sway 18kN):")
    m_ba = next(r for r in res['member_results'] if r['member_id'] == "AB")
    m_bc = next(r for r in res['member_results'] if r['member_id'] == "BC")
    m_cb = next(r for r in res['member_results'] if r['member_id'] == "BC") # End
    m_cd = next(r for r in res['member_results'] if r['member_id'] == "CD") # Start
    
    print(f"M_AB (Start of AB): {m_ba['moment_start']:.3f} (Image: 3.81)")
    print(f"M_BA (End of AB): {m_ba['moment_end']:.3f} (Image: 11.62)")
    print(f"M_BC (Start of BC): {m_bc['moment_start']:.3f} (Image: 11.62)")
    print(f"M_CB (End of BC): {m_bc['moment_end']:.3f} (Image: 8.95)")
    print(f"M_CD (Start of CD): {m_cd['moment_start']:.3f} (Image: 8.95)")
    print(f"M_DC (End of CD): {m_cd['moment_end']:.3f} (Image: 6.47)")
    
if __name__ == "__main__":
    verify()
