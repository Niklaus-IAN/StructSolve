import sys
import os
import math # Added missing import

# Add current directory to path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from frame_solver import FrameSolver
from models import FrameRequest, FrameNode, FrameMember, FrameUniformLoad, FramePointLoad, FrameMemberResult

def print_separator(title):
    print("\n" + "="*50)
    print(f" {title}")
    print("="*50)

def verify_fixed_beam():
    print_separator("TEST CASE 1: FIXED-FIXED BEAM with UDL")
    
    # Parameters
    L = 6.0 # meters
    w = -10.0 # kN/m (Downwards)
    E = 200e6 # kN/m^2
    I = 0.0001 # m^4
    A = 0.01 # m^2
    
    print(f"Parameters: L={L}m, w={w}kN/m (Down), E={E}, I={I}")
    
    # Expected Results (Clockwise Negative? Solver uses CCW Positive based on analysis)
    # Fixed End Moments: wL^2/12
    fem_magnitude = abs(w * L**2 / 12) # 10 * 36 / 12 = 30 kNm
    
    # Solver Convention: Warning, need to check.
    # Usually: Left Moment CCW (+), Right Moment CW (-) for sagging?
    # Actually for Fixed-Fixed with load down:
    # Left support rotates relative to chord...
    # Left Moment acts CCW (+) to resist rotation.
    # Right Moment acts CW (-) to resist rotation.
    # So Expected: M_start = +30, M_end = -30.
    
    # Expected Reactions: wL/2 = 30 kN (Upwards)
    
    print(f"EXPECTED: Moment Start = +{fem_magnitude:.2f}, Moment End = -{fem_magnitude:.2f}")
    print(f"EXPECTED: Shear Start = +{abs(w*L/2):.2f}, Shear End = -{abs(w*L/2):.2f} (Reaction)")
    
    # Setup Model
    nodes = [
        FrameNode(id="n1", x=0, y=0, fix_x=True, fix_y=True, fix_r=True),
        FrameNode(id="n2", x=L, y=0, fix_x=True, fix_y=True, fix_r=True)
    ]
    
    members = [
        FrameMember(
            id="m1", 
            start_node_id="n1", 
            end_node_id="n2",
            elastic_modulus=E,
            moment_of_inertia=I,
            cross_section_area=A
        )
    ]
    
    # Load: UDL in Local Y. Local Y is perpendicular to beam.
    # For horizontal beam, Local Y is Global Y.
    # Load is -10.
    uniform_loads = [
        FrameUniformLoad(member_id="m1", magnitude_y=w)
    ]
    
    request = FrameRequest(
        nodes=nodes,
        members=members,
        uniform_loads=uniform_loads
    )
    
    solver = FrameSolver()
    result_dict = solver.solve(request)
    
    if not result_dict['success']:
        print("Solver Failed!")
        return
        
    # Validating against Pydantic Model
    from models import FrameResponse
    result = FrameResponse(**result_dict)
    
    m_res = result.member_results[0]
    
    print("\nSOLVER RESULTS:")
    print(f"Moment Start: {m_res.moment_start:.4f}")
    print(f"Moment End:   {m_res.moment_end:.4f}")
    print(f"Shear Start:  {m_res.shear_start:.4f}")
    print(f"Shear End:    {m_res.shear_end:.4f}")
    
    # Verification
    # Start Moment
    if math.isclose(m_res.moment_start, fem_magnitude, rel_tol=1e-3):
        print("✅ Start Moment Matches")
    else:
        print(f"❌ Start Moment Mismatch. Diff: {m_res.moment_start - fem_magnitude}")
        
    # End Moment
    if math.isclose(m_res.moment_end, -fem_magnitude, rel_tol=1e-3):
        print("✅ End Moment Matches")
    else:
        print(f"❌ End Moment Mismatch. Diff: {m_res.moment_end - (-fem_magnitude)}") 
        
    # Start Shear   
    if math.isclose(m_res.shear_start, abs(w*L/2), rel_tol=1e-3):
        print("✅ Start Shear Matches")
    else:
        print(f"❌ Start Shear Mismatch")


def verify_portal_frame():
    print_separator("TEST CASE 2: SIMPLE PORTAL FRAME")
    """
       10kN ->  B ______ C
                |      |
                |      | 4m
              A |______| D
    """
    H = 4.0
    L = 4.0
    E = 200e6
    I = 0.0001
    A = 0.01
    P = 10.0 # kN (Horizontal at B)
    
    print(f"Parameters: H={H}m, L={L}m, Load P={P}kN at Node B (Right)")
    
    # Setup Model
    nodes = [
        FrameNode(id="A", x=0, y=0, fix_x=True, fix_y=True, fix_r=True),
        FrameNode(id="B", x=0, y=H, fix_x=False, fix_y=False, fix_r=False),
        FrameNode(id="C", x=L, y=H, fix_x=False, fix_y=False, fix_r=False),
        FrameNode(id="D", x=L, y=0, fix_x=True, fix_y=True, fix_r=True)
    ]
    
    members = [
        FrameMember(id="col1", start_node_id="A", end_node_id="B", elastic_modulus=E, moment_of_inertia=I, cross_section_area=A),
        FrameMember(id="beam", start_node_id="B", end_node_id="C", elastic_modulus=E, moment_of_inertia=I, cross_section_area=A),
        FrameMember(id="col2", start_node_id="C", end_node_id="D", elastic_modulus=E, moment_of_inertia=I, cross_section_area=A)
    ]
    
    point_loads = [
        FramePointLoad(type="NODE_LOAD", target_id="B", magnitude_x=P)
    ]
    
    request = FrameRequest(
        nodes=nodes,
        members=members,
        point_loads=point_loads
    )
    
    solver = FrameSolver()
    result_dict = solver.solve(request)
    
    if not result_dict['success']:
        print("Solver Failed!")
        return

    from models import FrameResponse
    result = FrameResponse(**result_dict)
    
    # Simple check: Sum of horizontal reactions = -Applied Load
    # Rx_A + Rx_D = -10
    
    reactions = result.reactions 
    # Reaction Vector Indices: A(0,1,2), B(3,4,5), C(6,7,8), D(9,10,11). 
    # But wait, B and C are free, so no reaction in 'reactions' vector?
    # The solver returns reactions for ALL DOFs, but non-supports should be zero (equilibrium residual).
    
    Rx_A = reactions[0]
    Rx_D = reactions[9]
    
    sum_Rx = Rx_A + Rx_D
    print("\nSOLVER RESULTS:")
    print(f"Reaction Ax: {Rx_A:.4f}")
    print(f"Reaction Dx: {Rx_D:.4f}")
    print(f"Sum Rx: {sum_Rx:.4f}")
    
    if math.isclose(sum_Rx, -P, rel_tol=1e-3):
        print("✅ Global Equilibrium (Horizontal) Verified")
    else:
        print(f"❌ Global Equilibrium Failed. Sum={sum_Rx}, Expected={-P}")
        
    # Check Symmetry of moments? No, sway frame isn't symmetric due to load.
    # But M_ba should equilibrate M_bc.
    
    # Let's inspect Member Results
    res_col1 = next(r for r in result.member_results if r.member_id == "col1")
    res_beam = next(r for r in result.member_results if r.member_id == "beam")
    
    # Joint B Equilibrium: M_BA + M_BC = 0.
    # Col1 is A->B. End Moment is M_AB_end (at B).
    # Beam is B->C. Start Moment is M_BC_start (at B).
    
    m_ba = res_col1.moment_end
    m_bc = res_beam.moment_start
    
    print(f"Moment BA: {m_ba:.4f}")
    print(f"Moment BC: {m_bc:.4f}")
    print(f"Sum Moments at B: {m_ba + m_bc:.4f}")
    
    if math.isclose(m_ba + m_bc, 0, abs_tol=1e-3):
         print("✅ Joint B Equilibrium Verified")
    else:
         print("❌ Joint B Equilibrium Failed")


def verify_stan_academy_problem():
    print_separator("TEST CASE 3: STAN ACADEMY FRAME")
    """
    Fixed-Fixed Portal Frame.
    H = 4m, W = 5m.
    A(0,0), B(0,4), C(5,4), D(5,0). Supports A, D Fixed.
    Properties: I_beam = I, I_col = 2I.
    Loads:
      - Beam BC: UDL 15 kN/m (Down).
      - Col AB: Point 20 kN at mid (2m) acting Right (+X).
      - Col CD: Point 20 kN at mid (2m) acting Left (-X).
    Expected Moments (Magnitudes):
      - Joint B (End of AB / Start of BC): ~22.71 kNm.
      - Support A (Start of AB): ~1.14 kNm.
    """
    H = 4.0
    W = 5.0
    E = 200e6
    I_ref = 0.0001
    A_ref = 0.01
    
    # I_col = 2 * I_ref
    # I_beam = I_ref
    
    print(f"Parameters: H={H}m, W={W}m")
    print("Properties: Colon I = 2I, Beam I = I")
    print("Loads: Beam UDL=15, Cols Point=20 (Symm)")
    
    nodes = [
        FrameNode(id="A", x=0, y=0, fix_x=True, fix_y=True, fix_r=True),
        FrameNode(id="B", x=0, y=H, fix_x=False, fix_y=False, fix_r=False),
        FrameNode(id="C", x=W, y=H, fix_x=False, fix_y=False, fix_r=False),
        FrameNode(id="D", x=W, y=0, fix_x=True, fix_y=True, fix_r=True)
    ]
    
    members = [
        # Col AB (A->B)
        FrameMember(id="m_AB", start_node_id="A", end_node_id="B", elastic_modulus=E, moment_of_inertia=2*I_ref, cross_section_area=A_ref),
        # Beam BC (B->C)
        FrameMember(id="m_BC", start_node_id="B", end_node_id="C", elastic_modulus=E, moment_of_inertia=I_ref, cross_section_area=A_ref),
        # Col CD (C->D)
        FrameMember(id="m_CD", start_node_id="C", end_node_id="D", elastic_modulus=E, moment_of_inertia=2*I_ref, cross_section_area=A_ref)
    ]
    
    # Loads
    point_loads = [
        # Col AB: 20kN Right at mid (Member Load)
        FramePointLoad(type="MEMBER_POINT_LOAD", target_id="m_AB", magnitude_y=0, magnitude_x=0, position=H/2), 
        # Wait, magnitude_y is local Y. For vertical col A->B:
        # Local x is along member (Up). Local y is perp (Left).
        # We want load Right (+Global X). That is -Local Y.
        # So magnitude_y should be -20?
        # Let's check transformation.
        # A(0,0) -> B(0,4). dx=0, dy=4. L=4.
        # c = 0, s = 1.
        # T = [[0, 1, 0...], [-1, 0, 0...]]
        # Global Force Fx=+20, Fy=0.
        # Local = T @ Global.
        # fx_local = c*Fx + s*Fy = 0.
        # fy_local = -s*Fx + c*Fy = -1*20 = -20.
        # So YES, magnitude_y = -20 implies Load Right.
        
        # NOTE: FrameSolver `FramePointLoad` has `magnitude_x` and `magnitude_y`. 
        # Are these LOCAL or GLOBAL for MEMBER_POINT_LOAD?
        # Checking solver `_calculate_member_fea`:
        # `P = load.magnitude_y`. It uses magnitude_y directly.
        # So it assumes Local Y.
        
        FramePointLoad(type="MEMBER_POINT_LOAD", target_id="m_AB", magnitude_y=-20.0, position=H/2),
        
        # Col CD: 20kN Left at mid (-Global X).
        # C(5,4) -> D(5,0). dx=0, dy=-4. L=4.
        # c = 0, s = -1.
        # T = [[0, -1, 0...], [1, 0, 0...]]
        # Global Fx=-20.
        # fy_local = -s*Fx + c*Fy = -(-1)*(-20) = -20.
        # So magnitude_y = -20 here too?
        # Let's verify vector.
        # Vector C->D is Down.
        # Local X is Down. Local Y is Right (Right Hand Rule: Z out of page, X x Y = Z). X=Down, Y=Right.
        # We want Load Left (-X global).
        # So Local Y should be Negative? No. Local Y is Right. We want Left. So Local Y is Negative.
        # So magnitude_y = -20.
        
        FramePointLoad(type="MEMBER_POINT_LOAD", target_id="m_CD", magnitude_y=-20.0, position=H/2)
    ]
    
    uniform_loads = [
        # Beam BC: 15 kN/m Down (-Global Y).
        # B(0,4) -> C(5,4). Horizontal.
        # Local X = Right. Local Y = Up.
        # Global Load Down = Local Load Down (-Y).
        FrameUniformLoad(member_id="m_BC", magnitude_y=-15.0)
    ]
    
    request = FrameRequest(
        nodes=nodes,
        members=members,
        point_loads=point_loads,
        uniform_loads=uniform_loads
    )
    
    solver = FrameSolver()
    result_dict = solver.solve(request)
    
    if not result_dict['success']:
        print("Solver Failed!")
        return

    from models import FrameResponse
    result = FrameResponse(**result_dict)
    
    res_AB = next(r for r in result.member_results if r.member_id == "m_AB")
    res_BC = next(r for r in result.member_results if r.member_id == "m_BC")
    
    m_A = res_AB.moment_start
    m_B_col = res_AB.moment_end
    m_B_beam = res_BC.moment_start
    
    print("\nSOLVER RESULTS:")
    print(f"Moment at A (Support): {m_A:.4f} kNm (Expected ~1.14)")
    print(f"Moment at B (Col End): {m_B_col:.4f} kNm")
    print(f"Moment at B (Beam Start): {m_B_beam:.4f} kNm (Expected ~22.71)")
    
    # Check A
    if math.isclose(abs(m_A), 1.14, abs_tol=0.1): # Loose tol first
        print("✅ Support Moment A Verified")
    else:
        print(f"❌ Support Moment A Mismatch. Got {m_A:.4f}, Expected 1.14")
        
    # Check B
    # Note: M_B_beam should be -22.71 (Hogging/CCW?) or +?
    # Stan Academy diagram shows 22.71 at Key points.
    # Check magnitude.
    if math.isclose(abs(m_B_beam), 22.71, abs_tol=0.5):
        print("✅ Joint Moment B Verified")
    else:
        print(f"❌ Joint Moment B Mismatch. Got {m_B_beam:.4f}, Expected 22.71")

    # --- Shear Verification ---
    print("\n--- SHEAR CHECKS ---")
    
    # Beam Shear
    # Stan: 37.5 kN
    v_beam_start = res_BC.shear_start
    print(f"Beam Shear (Start): {v_beam_start:.4f} kN (Expected 37.5)")
    if math.isclose(abs(v_beam_start), 37.5, abs_tol=0.1):
        print("✅ Beam Shear Verified")
    else:
        print(f"❌ Beam Shear Mismatch.")
        
    # Column Shear
    # Stan: 3.36 kN at A, 16.64 kN at B.
    v_col_A = res_AB.shear_start
    v_col_B = res_AB.shear_end
    
    print(f"Column Shear A: {v_col_A:.4f} kN (Expected 3.36)")
    print(f"Column Shear B: {v_col_B:.4f} kN (Expected 16.64)")
    
    # Check Statics on Column:
    # Sum Moments about B = 0 -> M_A + M_B + H_A*4 - P*2 = 0? (Signs vary)
    # My solver results:
    sum_M = m_A + m_B_col + v_col_A * H + (-20 * 2) # Check this eq
    # Just print it to Analyze
    
    if math.isclose(abs(v_col_A), 3.36, abs_tol=0.5):
         print("✅ Col Shear A Verified (Approx)")
    else:
         print("❌ Col Shear A Mismatch.")


    if math.isclose(abs(v_col_A), 3.36, abs_tol=0.5):
         print("✅ Col Shear A Verified (Approx)")
    else:
         print("❌ Col Shear A Mismatch.")


def verify_stan_academy_problem_2():
    print_separator("TEST CASE 4: STAN ACADEMY PROBLEM 2 (SWAY)")
    """
    Fixed-Fixed Portal Frame with Sway.
    H = 4m, W = 6m.
    A(0,0), B(0,4), C(6,4), D(6,0). Supports A, D Fixed.
    Properties: 
      - Cols AB, CD: I = 3I_ref.
      - Beam BC: I = 1.5I_ref.
    Loads:
      - Beam BC: Point Load 18 kN at 2m from B (Eccentric).
    Expected Moments (Magnitudes):
      - M_AB = 3.81 kNm
      - M_BA = 11.62 kNm
      - M_BC = 11.62 kNm
      - M_CB = 8.95 kNm
      - M_CD = 8.95 kNm
      - M_DC = 6.47 kNm
    """
    H = 4.0
    W = 6.0
    E = 200e6
    I_ref = 0.0001
    A_ref = 0.01
    
    # I_col = 3 * I_ref
    # I_beam = 1.5 * I_ref
    
    print(f"Parameters: H={H}m, W={W}m")
    print("Properties: Colon I = 3I, Beam I = 1.5I")
    print("Loads: Beam Point Load 18kN at 2m from B")
    
    nodes = [
        FrameNode(id="A", x=0, y=0, fix_x=True, fix_y=True, fix_r=True),
        FrameNode(id="B", x=0, y=H, fix_x=False, fix_y=False, fix_r=False),
        FrameNode(id="C", x=W, y=H, fix_x=False, fix_y=False, fix_r=False),
        FrameNode(id="D", x=W, y=0, fix_x=True, fix_y=True, fix_r=True)
    ]
    
    members = [
        # Col AB (A->B)
        FrameMember(id="m_AB", start_node_id="A", end_node_id="B", elastic_modulus=E, moment_of_inertia=3*I_ref, cross_section_area=A_ref),
        # Beam BC (B->C)
        FrameMember(id="m_BC", start_node_id="B", end_node_id="C", elastic_modulus=E, moment_of_inertia=1.5*I_ref, cross_section_area=A_ref),
        # Col CD (C->D)
        FrameMember(id="m_CD", start_node_id="C", end_node_id="D", elastic_modulus=E, moment_of_inertia=3*I_ref, cross_section_area=A_ref)
    ]
    
    # Loads
    point_loads = [
        # Beam BC: 18kN Point at 2m from B.
        # Load Down (-Local Y).
        FramePointLoad(type="MEMBER_POINT_LOAD", target_id="m_BC", magnitude_y=-18.0, position=2.0)
    ]
    
    request = FrameRequest(
        nodes=nodes,
        members=members,
        point_loads=point_loads
    )
    
    solver = FrameSolver()
    result_dict = solver.solve(request)
    
    if not result_dict['success']:
        print("Solver Failed!")
        return

    from models import FrameResponse
    result = FrameResponse(**result_dict)
    
    res_AB = next(r for r in result.member_results if r.member_id == "m_AB")
    res_BC = next(r for r in result.member_results if r.member_id == "m_BC")
    res_CD = next(r for r in result.member_results if r.member_id == "m_CD")
    
    m_A = res_AB.moment_start
    m_B_col = res_AB.moment_end
    m_B_beam = res_BC.moment_start
    m_C_beam = res_BC.moment_end
    m_C_col = res_CD.moment_start
    m_D = res_CD.moment_end
    
    print("\nSOLVER RESULTS:")
    print(f"M_AB: {m_A:.4f} kNm (Expected 3.81)")
    print(f"M_BA: {m_B_col:.4f} kNm (Expected 11.62)")
    print(f"M_BC: {m_B_beam:.4f} kNm (Expected 11.62)")
    print(f"M_CB: {m_C_beam:.4f} kNm (Expected 8.95)")
    print(f"M_CD: {m_C_col:.4f} kNm (Expected 8.95)")
    print(f"M_DC: {m_D:.4f} kNm (Expected 6.47)")
    
    expected = {
        'M_AB': 3.81,
        'M_BA': 11.62,
        'M_BC': 11.62,
        'M_CB': 8.95,
        'M_CD': 8.95,
        'M_DC': 6.47
    }
    
    results = {
        'M_AB': abs(m_A),
        'M_BA': abs(m_B_col),
        'M_BC': abs(m_B_beam),
        'M_CB': abs(m_C_beam),
        'M_CD': abs(m_C_col),
        'M_DC': abs(m_D)
    }
    
    passed = True
    for key, val in expected.items():
        if not math.isclose(results[key], val, abs_tol=0.2):
            print(f"❌ {key} Mismatch. Got {results[key]:.4f}, Expected {val}")
            passed = False
        else:
             print(f"✅ {key} Verified")


def verify_stan_academy_problem_3():
    print_separator("TEST CASE 5: STAN ACADEMY PROBLEM 3 (COMPLEX)")
    """
    Frame A-B-C with Col B-D.
    A(0,4) Fixed.
    B(4,4) Joint.
    C(9,4) Pin/Roller.
    D(4,0) Fixed.
    
    Members:
    - AB: L=4m, I=3I.
    - BC: L=5m, I=2I.
    - BD: L=4m, I=I.
    
    Loads:
    - AB: UDL 9 kN/m.
    - BC: Point 24 kN at 3m from B.
    - BD: Point 10 kN (Left) at 2m.
    
    Expected Moments:
    - M_AB = -8.20
    - M_BA = 19.59
    - M_BC = -17.12
    - M_CB = 0
    - M_BD = -2.47
    - M_DB = 6.26
    """
    E = 200e6
    I_ref = 0.0001 # I for BD
    A_ref = 1000.0 # Increased to simulate Axial Rigidity (match manual non-sway assumption)
    
    nodes = [
        FrameNode(id="A", x=0, y=4, fix_x=True, fix_y=True, fix_r=True),
        FrameNode(id="B", x=4, y=4, fix_x=False, fix_y=False, fix_r=False),
        FrameNode(id="C", x=9, y=4, fix_x=False, fix_y=True, fix_r=False), # Roller/Pin
        FrameNode(id="D", x=4, y=0, fix_x=True, fix_y=True, fix_r=True)
    ]
    
    members = [
        # AB: 3I
        FrameMember(id="m_AB", start_node_id="A", end_node_id="B", elastic_modulus=E, moment_of_inertia=3*I_ref, cross_section_area=A_ref),
        # BC: 2I
        FrameMember(id="m_BC", start_node_id="B", end_node_id="C", elastic_modulus=E, moment_of_inertia=2*I_ref, cross_section_area=A_ref),
        # BD: I (Col)
        FrameMember(id="m_BD", start_node_id="B", end_node_id="D", elastic_modulus=E, moment_of_inertia=I_ref, cross_section_area=A_ref)
    ]
    
    # Loads
    point_loads = [
        # BC: 24kN at 3m
        FramePointLoad(type="MEMBER_POINT_LOAD", target_id="m_BC", magnitude_y=-24.0, position=3.0),
        # BD: 10kN Left at 2m.
        # B(4,4) -> D(4,0). Vector Down.
        # Local Y is Right.
        # Load is Left (-Global X). This is -Local Y.
        FramePointLoad(type="MEMBER_POINT_LOAD", target_id="m_BD", magnitude_y=-10.0, position=2.0)
    ]
    
    uniform_loads = [
        # AB: 9 kN/m Down
        FrameUniformLoad(member_id="m_AB", magnitude_y=-9.0)
    ]
    
    request = FrameRequest(
        nodes=nodes,
        members=members,
        point_loads=point_loads,
        uniform_loads=uniform_loads
    )
    
    solver = FrameSolver()
    result_dict = solver.solve(request)
    
    if not result_dict['success']:
        print("Solver Failed!")
        return

    from models import FrameResponse
    result = FrameResponse(**result_dict)
    
    res_AB = next(r for r in result.member_results if r.member_id == "m_AB")
    res_BC = next(r for r in result.member_results if r.member_id == "m_BC")
    res_BD = next(r for r in result.member_results if r.member_id == "m_BD")
    
    vals = {
        'M_AB': abs(res_AB.moment_start),
        'M_BA': abs(res_AB.moment_end),
        'M_BC': abs(res_BC.moment_start),
        'M_CB': abs(res_BC.moment_end),
        'M_BD': abs(res_BD.moment_start),
        'M_DB': abs(res_BD.moment_end)
    }
    
    expected = {
        'M_AB': 8.20,
        'M_BA': 19.59,
        'M_BC': 17.12,
        'M_CB': 0.0,
        'M_BD': 2.47,
        'M_DB': 6.26
    }
    
    print("\nSOLVER RESULTS:")
    for k, v in vals.items():
        print(f"{k}: {v:.4f} kNm (Expected {expected[k]})")
        
    # Check Equilibrium at B (Algebraic Sum)
    # Re-fetch raw values for sum check
    sum_M_B = res_AB.moment_end + res_BC.moment_start + res_BD.moment_start
    print(f"Sum Moments at B (Raw): {sum_M_B:.4f} (Expected 0)")
    
    passed = True
    for key, val in expected.items():
        # Using larger tolerance near zero
        tol = 0.5
        if abs(val) < 1: tol = 0.1
        
        if not math.isclose(vals[key], val, abs_tol=tol):
            print(f"❌ {key} Mismatch.")
            passed = False
        else:
             print(f"✅ {key} Verified")


def verify_stan_academy_problem_4():
    print_separator("TEST CASE 6: STAN ACADEMY PROBLEM 4 (PREDICTION)")
    """
    Frame A-B-C-D.
    A(0,0) Fixed.
    B(0,4) Joint.
    C(4,4) Joint.
    D(4,1) Fixed. (Col CD is 3m long).
    
    Members:
    - AB: L=4m, I=I.
    - BC: L=4m, I=3I.
    - CD: L=3m, I=1.5I.
    
    Loads:
    - AB: UDL 12 kN/m RIGHT.
    - BC: Point 20 kN DOWN at Mid (2m).
    - CD: Point 27 kN LEFT at 2m from C.
    """
    E = 200e6
    I_ref = 0.0001
    A_ref = 1000.0 # Use Rigid assumption
    
    nodes = [
        FrameNode(id="A", x=0, y=0, fix_x=True, fix_y=True, fix_r=True),
        FrameNode(id="B", x=0, y=4, fix_x=False, fix_y=False, fix_r=False),
        FrameNode(id="C", x=4, y=4, fix_x=False, fix_y=False, fix_r=False),
        FrameNode(id="D", x=4, y=1, fix_x=True, fix_y=True, fix_r=True)
    ]
    
    members = [
        # AB: I
        FrameMember(id="m_AB", start_node_id="A", end_node_id="B", elastic_modulus=E, moment_of_inertia=I_ref, cross_section_area=A_ref),
        # BC: 3I
        FrameMember(id="m_BC", start_node_id="B", end_node_id="C", elastic_modulus=E, moment_of_inertia=3*I_ref, cross_section_area=A_ref),
        # CD: 1.5I
        FrameMember(id="m_CD", start_node_id="C", end_node_id="D", elastic_modulus=E, moment_of_inertia=1.5*I_ref, cross_section_area=A_ref)
    ]
    
    # Loads
    point_loads = [
        # BC: 20kN Down at 2m
        FramePointLoad(type="MEMBER_POINT_LOAD", target_id="m_BC", magnitude_y=-20.0, position=2.0),
        # CD: 27kN Left at 2m from C.
        # C(4,4)->D(4,1). Downward.
        # Local Y is RIGHT.
        # Load is LEFT (-Global X). This is -Local Y.
        FramePointLoad(type="MEMBER_POINT_LOAD", target_id="m_CD", magnitude_y=-27.0, position=2.0)
    ]
    
    uniform_loads = [
        # AB: 12 kN/m RIGHT (+Global X).
        # A(0,0)->B(0,4). Upward.
        # Local Y is LEFT (-Global X).
        # Load is Right. So magnitude_y = -12.
        FrameUniformLoad(member_id="m_AB", magnitude_y=-12.0)
    ]
    
    request = FrameRequest(
        nodes=nodes,
        members=members,
        point_loads=point_loads,
        uniform_loads=uniform_loads
    )
    
    solver = FrameSolver()
    result_dict = solver.solve(request)
    
    if not result_dict['success']:
        print("Solver Failed!")
        return

    from models import FrameResponse
    result = FrameResponse(**result_dict)
    
    res_AB = next(r for r in result.member_results if r.member_id == "m_AB")
    res_BC = next(r for r in result.member_results if r.member_id == "m_BC")
    res_CD = next(r for r in result.member_results if r.member_id == "m_CD")
    
    vals = {
        'M_AB': res_AB.moment_start,
        'M_BA': res_AB.moment_end,
        'M_BC': res_BC.moment_start,
        'M_CB': res_BC.moment_end,
        'M_CD': res_CD.moment_start,
        'M_DC': res_CD.moment_end
    }
    
    print("\nSOLVER RESULTS (PREDICTED):")
    for k, v in vals.items():
        print(f"{k}: {v:.4f} kNm")
        
    # Check Equilibrium
    sum_B = vals['M_BA'] + vals['M_BC']
    sum_C = vals['M_CB'] + vals['M_CD']
    
    print(f"Sum Moments at B: {sum_B:.4f}")
    if math.isclose(sum_B, 0, abs_tol=0.1): print("✅ Joint B Equilibrium")
    else: print("❌ Joint B Equilibrium FAIL")
    
    print(f"Sum Moments at C: {sum_C:.4f}")
    if math.isclose(sum_C, 0, abs_tol=0.1): print("✅ Joint C Equilibrium")
    else: print("❌ Joint C Equilibrium FAIL")


if __name__ == "__main__":
    verify_fixed_beam()
    verify_portal_frame()
    verify_stan_academy_problem()
    verify_stan_academy_problem_2()
    verify_stan_academy_problem_3()
    verify_stan_academy_problem_4()
