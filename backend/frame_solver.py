
import numpy as np
import math
from typing import List, Dict, Tuple
from models import FrameRequest, FrameNode, FrameMember, FramePointLoad, FrameUniformLoad, DiagramData


import numpy as np
import math
from typing import List, Dict, Tuple
from models import FrameRequest, FrameNode, FrameMember, FramePointLoad, FrameUniformLoad, DiagramData

class FrameSolver:
    def solve(self, request: FrameRequest):
        # 1. Setup degrees of freedom (DOF)
        node_dof_map = self._map_dofs(request.nodes)
        total_dof = 3 * len(request.nodes)
        
        # 2. Assemble Global Stiffness Matrix [K]
        K_global = np.zeros((total_dof, total_dof))
        
        for member in request.members:
            k_global_member = self._calculate_member_global_stiffness(member, request.nodes)
            
            # Add to system matrix (Scatter)
            start_dofs = node_dof_map[member.start_node_id]
            end_dofs = node_dof_map[member.end_node_id]
            member_dofs = start_dofs + end_dofs 
            
            for i in range(6):
                for j in range(6):
                    row = member_dofs[i]
                    col = member_dofs[j]
                    K_global[row, col] += k_global_member[i, j]
                    
        # 3. Assemble Load Vector {F}
        F_global = np.zeros(total_dof)
        
        # 3a. Apply Nodal Loads directly
        for pl in request.point_loads:
            if pl.type == "NODE_LOAD":
                if pl.target_id in node_dof_map:
                    dofs = node_dof_map[pl.target_id]
                    F_global[dofs[0]] += pl.magnitude_x
                    F_global[dofs[1]] += pl.magnitude_y
                    F_global[dofs[2]] += pl.moment
        
        # 3b. Handle Member Loads (Equivalent Nodal Loads)
        # We calculate Fixed End Actions (FEA) and SUBTRACT them from F_global (Action -> Reaction)
        # Note: F_global = F_nodal - R_fixed_end
        
        
        member_fixed_actions = {} # Store for post-processing: member_id -> np.array(6) local
        
        for member in request.members:
            # Gather all loads on this member
            member_loads = []
            # Point loads on member
            for pl in request.point_loads:
                if pl.type == "MEMBER_POINT_LOAD" and pl.target_id == member.id:
                    member_loads.append(pl)
            # Uniform loads on member
            for ul in request.uniform_loads:
                if ul.member_id == member.id:
                    member_loads.append(ul)
            
            if member_loads:
                # Calculate FEA in Local System
                fea_local = self._calculate_member_fea(member, member_loads, request.nodes)
                member_fixed_actions[member.id] = fea_local
                
                # Transform to Global
                T = self._get_transformation_matrix(member, request.nodes)
                fea_global = T.T @ fea_local
                
                # Subtract from Global Force Vector
                start_dofs = node_dof_map[member.start_node_id]
                end_dofs = node_dof_map[member.end_node_id]
                indices = start_dofs + end_dofs
                
                for i in range(6):
                    dof_idx = indices[i]
                    F_global[dof_idx] -= fea_global[i]
        
        # 4. Apply Boundary Conditions
        free_dofs = []
        restrained_dofs = []
        
        for node in request.nodes:
            dofs = node_dof_map[node.id]
            if not node.fix_x: free_dofs.append(dofs[0])
            else: restrained_dofs.append(dofs[0])
            
            if not node.fix_y: free_dofs.append(dofs[1])
            else: restrained_dofs.append(dofs[1])
            
            if not node.fix_r: free_dofs.append(dofs[2])
            else: restrained_dofs.append(dofs[2])
            
        # 5. Solve for Displacements
        # if not free_dofs:
        #    raise ValueError("Structure is fully restrained")
        
        if free_dofs:    
            K_ff = K_global[np.ix_(free_dofs, free_dofs)]
            F_f = F_global[free_dofs]
            
            # Stability Check
            det = np.linalg.det(K_ff) if K_ff.shape[0] < 100 else 1.0 
            # (Determinant check is expensive for large matrices, but useful for small ones)
            
            try:
                u_free = np.linalg.solve(K_ff, F_f)
            except np.linalg.LinAlgError:
                raise ValueError("Structure is unstable (singular stiffness matrix)")
        else:
            u_free = np.array([])
            
        u_total = np.zeros(total_dof)
        if free_dofs:
            u_total[free_dofs] = u_free
        
        # 6. Post-Processing: Reactions and Forces
        reactions = np.zeros(total_dof)
        if restrained_dofs:
            # R = K_total * u - F_applied (excluding reactions)
            # More robustly: R = K_row * u - F_row
            # F_row here must include the nodal loads and FEA contributions
            reactions = K_global @ u_total - F_global
            
        member_results = []
        for member in request.members:
            # Get FEA if exists, else zero
            fea_local = member_fixed_actions.get(member.id, np.zeros(6))
            result = self._calculate_member_forces(member, request.nodes, node_dof_map, u_total, fea_local, request)
            member_results.append(result)
            
        return {
            "success": True,
            "displacements": u_total.tolist(),
            "reactions": reactions.tolist(),
            "member_results": member_results
        }
    
    def _map_dofs(self, nodes: List[FrameNode]) -> Dict[str, List[int]]:
        mapping = {}
        for i, node in enumerate(nodes):
            start = i * 3
            mapping[node.id] = [start, start + 1, start + 2]
        return mapping

    def _get_geometry(self, member: FrameMember, nodes: List[FrameNode]):
        start = next(n for n in nodes if n.id == member.start_node_id)
        end = next(n for n in nodes if n.id == member.end_node_id)
        dx = end.x - start.x
        dy = end.y - start.y
        L = math.sqrt(dx**2 + dy**2)
        return L, dx, dy

    def _get_transformation_matrix(self, member: FrameMember, nodes: List[FrameNode]):
        L, dx, dy = self._get_geometry(member, nodes)
        c = dx / L
        s = dy / L
        
        T = np.zeros((6, 6))
        sub_T = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])
        T[0:3, 0:3] = sub_T
        T[3:6, 3:6] = sub_T
        return T

    def _calculate_member_global_stiffness(self, member: FrameMember, nodes: List[FrameNode]):
        L, dx, dy = self._get_geometry(member, nodes)
        
        E = member.elastic_modulus # Assume kN/m2 or consistent
        I = member.moment_of_inertia
        A = member.cross_section_area
        
        # Standard Rigidity Terms
        k_axial = E * A / L
        k1 = 12 * E * I / L**3
        k2 = 6 * E * I / L**2
        k3 = 4 * E * I / L # 4EI/L
        k4 = 2 * E * I / L # 2EI/L
        
        # Local Stiffness k' (Standard Rigid-Rigid)
        k_local = np.array([
            [k_axial, 0, 0, -k_axial, 0, 0],
            [0, k1, k2, 0, -k1, k2],
            [0, k2, k3, 0, -k2, k4],
            [-k_axial, 0, 0, k_axial, 0, 0],
            [0, -k1, -k2, 0, k1, -k2],
            [0, k2, k4, 0, -k2, k3]
        ])
        
        # Apply Releases (Static Condensation / Modified Stiffness)
        # If pinned at start (M1=0), pinned at end (M2=0)
        
        if member.release_start and member.release_end:
            # Truss Element (Axial only, effectively) for bending
            # Modified k' for Pin-Pin
            # Bending terms become zero, only Axial remains
            # Wait, shear can still exist if it's a beam, but no moments.
            # Actually for Pin-Pin: 
            # [ 0, 0, 0 ... ] for rotation rows/cols?
            # Standard Truss Matrix:
            k_local_pin_pin = np.zeros((6,6))
            k_local_pin_pin[0,0] = k_axial; k_local_pin_pin[0,3] = -k_axial
            k_local_pin_pin[3,0] = -k_axial; k_local_pin_pin[3,3] = k_axial
            # What about transverse stiffness (Shear)? rigid body mode?
            # A pin-pin beam CANNOT carry shear if there are no intermediate loads? 
            # In matrix method, pin-pin is usually treated as Truss element.
            k_local = k_local_pin_pin
            
        elif member.release_start:
            # Pinned-Fixed
            # Modify 3rd row/col (Rotation start) to be zero? No, condense it.
            # Modified stiffness:
            # k'33 becomes 3EI/L
            k3_mod = 3 * E * I / L # 3EI/L
            k2_mod = 3 * E * I / L**2 
            k1_mod = 3 * E * I / L**3
            
            # Rebuild bending part
            # u2, v2, th2 affected
            k_local = np.zeros((6,6))
            # Axial
            k_local[0,0] = k_axial; k_local[0,3] = -k_axial
            k_local[3,0] = -k_axial; k_local[3,3] = k_axial
            
            # Transverse/Rotation (Targeting [1,2, 4,5])
            # v1, th1(released), v2, th2
            # Relation: M1 = 0.
            # Resulting stiffness matrix for Propped Cantilever (Pin-Fix)
            k_local[1,1] = k1_mod;  k_local[1,4] = -k1_mod; k_local[1,5] = k2_mod
            k_local[4,1] = -k1_mod; k_local[4,4] = k1_mod;  k_local[4,5] = -k2_mod
            k_local[5,1] = k2_mod;  k_local[5,4] = -k2_mod; k_local[5,5] = k3_mod
            
        elif member.release_end:
            # Fixed-Pinned
            # Same as above but mirror
            k3_mod = 3 * E * I / L
            k2_mod = 3 * E * I / L**2
            k1_mod = 3 * E * I / L**3
            
            k_local = np.zeros((6,6))
            # Axial
            k_local[0,0] = k_axial; k_local[0,3] = -k_axial
            k_local[3,0] = -k_axial; k_local[3,3] = k_axial
            
            # Transverse/Rotation
            # v1, th1, v2, th2(released)
            k_local[1,1] = k1_mod;  k_local[1,2] = k2_mod;  k_local[1,4] = -k1_mod
            k_local[2,1] = k2_mod;  k_local[2,2] = k3_mod;  k_local[2,4] = -k2_mod
            k_local[4,1] = -k1_mod; k_local[4,2] = -k2_mod; k_local[4,4] = k1_mod
            
        # Global Transform
        T = self._get_transformation_matrix(member, nodes)
        return T.T @ k_local @ T

    def _calculate_member_fea(self, member: FrameMember, loads: List, nodes: List[FrameNode]) -> np.ndarray:
        """Calculate Fixed End Actions (Force/Moment) in Local System."""
        fea = np.zeros(6) # [fx1, fy1, m1, fx2, fy2, m2]
        L, _, _ = self._get_geometry(member, nodes)
        
        for load in loads:
            # UDL
            if isinstance(load, FrameUniformLoad):
                w = load.magnitude_y # Assuming local y (perpendicular)
                # Fixed-Fixed
                # Load w (signed). If w is Negative (Down), Start Moment should be Positive (CCW).
                # Previous: m_start = (w * L**2) / 12 -> Negative. Incorrect.
                # Correct: m_start = -(w * L**2) / 12 -> Positive.
                m_start = -(w * L**2) / 12
                m_end = (w * L**2) / 12
                # Shear Reactions
                # If w is Negative (Down), Reaction should be Positive (Up).
                # Previous: fy_start = (w * L) / 2 -> Negative. Incorrect.
                fy_start = -(w * L) / 2
                fy_end = -(w * L) / 2
                
                # Adjust for releases for Moment (Shear adjusted below?)
                if member.release_start and member.release_end:
                    # Simply supported
                    m_start = 0; m_end = 0
                    fy_start = w*L/2; fy_end = w*L/2
                elif member.release_start:
                    # Pin-Fix (Propped)
                    m_start = 0
                    m_end = -(w * L**2) / 8
                    fy_start = 3 * w * L / 8
                    fy_end = 5 * w * L / 8
                elif member.release_end:
                    # Fix-Pin
                    m_start = (w * L**2) / 8
                    m_end = 0
                    fy_start = 5 * w * L / 8
                    fy_end = 3 * w * L / 8
                
                fea[1] += fy_start
                fea[2] += m_start
                fea[4] += fy_end
                fea[5] += m_end
                
            elif isinstance(load, FramePointLoad):
                if load.type == "MEMBER_POINT_LOAD":
                    P = load.magnitude_y
                    # Default to center if position not provided
                    a = load.position if load.position is not None else L / 2
                    b = L - a
                    
                    # Fixed-Fixed Moments (Pab^2/L^2 and Pba^2/L^2)
                    # M_start (CCW+) = + P a b^2 / L^2 
                    # Wait, standard beam loading Down (-P):
                    # Left Moment is CCW (+). Right is CW (-).
                    # My P is signed. acts in Y.
                    # If P is negative (down):
                    # Left Reaction goes Up (+). Left Moment is CCW (+).
                    # Formula: M1 = + P * a * b^2 / L^2  (This gives + for Down load? strictly No. Magnitude P is usually positive in textbook)
                    # Let's derive signs.
                    # Load Down (-P). Left Support pushes Up (+). Beam sags (Hogging at ends).
                    # Left End: Hogging = Tension Top. Moment Vector is CCW (+). OK.
                    # So for Negative P, we want Positive M1.
                    # Formula M = - P a b^2 / L^2 ? If P is -10 -> M = +10... Yes.
                    
                    m_start = -(P * a * b**2) / L**2
                    m_end = (P * b * a**2) / L**2
                    
                    # Vertical Reactions
                    # R1 = Pb^2(3a+b)/L^3 * P ? No.
                    # Simple statics: R1 = (Pb + M1 + M2)/L
                    # Let's use superposition formulas or re-derive.
                    # Fixed-Fixed Shear:
                    # Ry1 = -P * b^2 * (3*a + b) / L**3
                    # Wait, if P is neg, Ry1 should be pos.
                    # -(-10) = +10. Correct.
                    
                    fy_start = -(P * b**2 * (3*a + b)) / L**3
                    fy_end = -(P * a**2 * (3*b + a)) / L**3
                    
                    # Releases (Superposition or Switch)
                    if member.release_start and member.release_end:
                        # Pin-Pin (Simple Beam)
                        m_start = 0
                        m_end = 0
                        fy_start = -P * b / L
                        fy_end = -P * a / L
                        
                    elif member.release_start:
                        # Pin-Fix
                        m_start = 0
                        # M2 = Pab(L+b)/(2L^2). (Standard Check)
                        # For P down (-), M2 should be CW (-).
                        # Formula: M2 = P * a * (L**2 - a**2) / (2*L**2) Is valid?
                        # Let's trust coefficients.
                        # R1 (Pin) = ...
                        # Let's use the "Remove Moment" method.
                        # Original Fixed-Fixed: M1_fix, M2_fix
                        # Release Node 1: Apply -M1_fix. CoFactor to Node 2 is 0.5.
                        # New M2 = M2_fix + 0.5 * (-M1_fix) = M2_fix - 0.5 M1_fix.
                        # New R1 arises from equilibrium changes.
                        
                        m_fix_1 = -(P * a * b**2) / L**2
                        m_fix_2 = (P * b * a**2) / L**2
                        
                        m_start = 0
                        m_end = m_fix_2 - 0.5 * m_fix_1
                        
                        # Recalculate shears from statics
                        # Sum M_about_2 = 0: R1*L + M_start(0) + M_end + P*b = 0
                        # R1*L + m_end + P*b = 0 -> R1 = -(m_end + P*b)/L
                        # Note: P is signed. if P=-10 (down), P*b is negative moment. m_end is negative moment.
                        # R1 = -(-M - 10b)/L = +
                        fy_start = -(m_end + P * b) / L
                        fy_end = -P - fy_start
                        
                    elif member.release_end:
                        # Fix-Pin
                        m_fix_1 = -(P * a * b**2) / L**2
                        m_fix_2 = (P * b * a**2) / L**2
                        
                        m_end = 0
                        m_start = m_fix_1 - 0.5 * m_fix_2
                        
                        # Sum M_about_1 = 0: R2*L + M_start + P*a = 0
                        fy_end = -(m_start + P * a) / L
                        fy_start = -P - fy_end
                    
                    fea[1] += fy_start
                    fea[2] += m_start
                    fea[4] += fy_end
                    fea[5] += m_end
                
                
        return fea

    def _calculate_member_forces(self, member: FrameMember, nodes: List[FrameNode], dof_map: Dict, u_total: np.ndarray, fea_local: np.ndarray, request: FrameRequest = None):
        start_dofs = dof_map[member.start_node_id]
        end_dofs = dof_map[member.end_node_id]
        indices = start_dofs + end_dofs
        u_global_member = u_total[indices]
        
        T = self._get_transformation_matrix(member, nodes)
        u_local = T @ u_global_member
        
        # Recalculate k_local (needed)
        k_local_matrix_temp = self._calculate_member_global_stiffness(member, nodes)
        k_local = T @ k_local_matrix_temp @ T.T
        
        # Calculate forces at ends (End Actions)
        f_local = k_local @ u_local + fea_local
        
        # Discretize member for diagram data (20 segments)
        stations = 21
        L, _, _ = self._get_geometry(member, nodes)
        x_vals = np.linspace(0, L, stations)
        
        n_vals = []
        v_vals = []
        m_vals = []
        
        for x in x_vals:
            n = -f_local[0]
            v = f_local[1]
            m = -f_local[2] + f_local[1] * x
            
            # Add effects of loads along span
            if request:
                for ul in request.uniform_loads:
                    if ul.member_id == member.id:
                        w = ul.magnitude_y 
                        # Apply if x > 0
                        if x > 0:
                            v += w * x
                            m += w * x**2 / 2
                
                for pl in request.point_loads:
                    if pl.type == "MEMBER_POINT_LOAD" and pl.target_id == member.id:
                        P = pl.magnitude_y
                        a = pl.position if pl.position is not None else L/2
                        # Macaulay Step Function: Only add if x > a
                        if x > a:
                            v += P
                            m += P * (x - a)

            n_vals.append(n)
            v_vals.append(v)
            m_vals.append(m)

        # EMD and FMD Calculation
        # EMD: Linear interpolation of end moments.
        # Note on Signs: f_local[2] is Moment at Start (Counter-Clockwise).
        # f_local[5] is Moment at End (Counter-Clockwise).
        # Beam Sign Convention (Sagging Positive):
        # M(x) due to End Moments:
        # M_start_beam = -f_local[2] (Internal Moment just inside start).
        # M_end_beam = f_local[5] (Internal Moment just inside end).
        # Linear Interp: M_emd(x) = M_start_beam + (M_end_beam - M_start_beam) * (x/L).
        
        # Wait, let's stick to the solver's internal sign convention for `m_vals` which is likely consistent.
        # In loop: m = -f_local[2] + f_local[1] * x + LoadTerms.
        # -f_local[2] is the moment from the start node reaction.
        # f_local[1] * x is the moment from the start node shear.
        # This describes the TOTAL moment.
        # The "End Moment Diagram" usually implies the moment diagram IF there were NO span loads (only end moments/shears balanced).
        # But End Shears depend on Span Loads.
        # Definition:
        # FMD = Moment on Simply Supported Beam with same Span Loads.
        # EMD = Total BMD - FMD. (The "Fixing" Moments).
        
        emd_vals = []
        fmd_vals = []
        
        # We can calculate FMD by assuming simple supports:
        # Reactions for Simple Beam:
        # R_start_simple, R_end_simple.
        # Calculate Moment(x) using these.
        
        # Step 1: Calculate Simple Support Reactions for Span Loads
        r_simple_start_y = 0.0
        r_simple_end_y = 0.0
        
        if request:
             for ul in request.uniform_loads:
                if ul.member_id == member.id:
                    w = ul.magnitude_y
                    # Total Load W = w*L
                    # R = -Total_Load / 2 (Opposing load)
                    # if w is negative (down), R should be positive (up)
                    r_simple_start_y -= w * L / 2
                    r_simple_end_y -= w * L / 2
                    
             for pl in request.point_loads:
                if pl.type == "MEMBER_POINT_LOAD" and pl.target_id == member.id:
                    P = pl.magnitude_y
                    a = pl.position if pl.position is not None else L/2
                    b = L - a
                    # R_start = -P*b/L
                    # R_end = -P*a/L
                    r_simple_start_y -= P * b / L
                    r_simple_end_y -= P * a / L

        # Step 2: Iterate and Calc FMD
        for i, x in enumerate(x_vals):
            # FMD (Simple Beam Moment)
            # M_simple = R_start * x + Load_Terms
            # Note: R is Up (+). Load terms are usually Down (-).
            # Sign convention: Sagging Positive.
            # My solver convention `m`: Check loop (m = -f_local[2] ...).
            # If f_local[2] (Reaction M) is CCW (+). -f_local[2] is starting internal moment?
            # Let's align FMD with `m_vals` convention.
            
            m_fmd = r_simple_start_y * x
            
            # Add Load Effects (Same as Total Loop)
            if request:
                for ul in request.uniform_loads:
                    if ul.member_id == member.id:
                        w = ul.magnitude_y 
                        if x > 0:
                            # Load is w. Moment arm x/2.
                            # w is signed (usually -).
                            # If w is -, force is Down. Moment is Hogging (-).
                            # + w*x * x/2. (Negative result).
                            m_fmd += w * x**2 / 2
                
                for pl in request.point_loads:
                    if pl.type == "MEMBER_POINT_LOAD" and pl.target_id == member.id:
                        P = pl.magnitude_y
                        a = pl.position if pl.position is not None else L/2
                        if x > a:
                            m_fmd += P * (x - a)
            
            fmd_vals.append(m_fmd)
            
            # EMD = Total - FMD
            # This ensures EMD + FMD = Total exactly.
            m_total = m_vals[i]
            emd_vals.append(m_total - m_fmd)

        return {
            "member_id": member.id,
            "axial_start": f_local[0],
            "shear_start": f_local[1],
            "moment_start": f_local[2],
            "axial_end": f_local[3],
            "shear_end": f_local[4],
            "moment_end": f_local[5],
            "stations": x_vals.tolist(),
            "n_diagram": n_vals.tolist() if hasattr(n_vals, 'tolist') else n_vals,
            "v_diagram": v_vals.tolist() if hasattr(v_vals, 'tolist') else v_vals,
            "m_diagram": m_vals.tolist() if hasattr(m_vals, 'tolist') else m_vals,
            "fmd_diagram": fmd_vals if isinstance(fmd_vals, list) else fmd_vals.tolist(),
            "emd_diagram": emd_vals if isinstance(emd_vals, list) else emd_vals.tolist()
        }

