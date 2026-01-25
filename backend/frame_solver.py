
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
        if not free_dofs:
            raise ValueError("Structure is fully restrained")
            
        K_ff = K_global[np.ix_(free_dofs, free_dofs)]
        F_f = F_global[free_dofs]
        
        # Stability Check
        det = np.linalg.det(K_ff) if K_ff.shape[0] < 100 else 1.0 
        # (Determinant check is expensive for large matrices, but useful for small ones)
        
        try:
            u_free = np.linalg.solve(K_ff, F_f)
        except np.linalg.LinAlgError:
            raise ValueError("Structure is unstable (singular stiffness matrix)")
            
        u_total = np.zeros(total_dof)
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
            result = self._calculate_member_forces(member, request.nodes, node_dof_map, u_total, fea_local)
            member_results.append(result)
            
        return {
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
                m_start = (w * L**2) / 12
                m_end = -(w * L**2) / 12
                fy_start = (w * L) / 2
                fy_end = (w * L) / 2
                
                # Adjust for releases
                if member.release_start and member.release_end:
                    # Simply supported
                    m_start = 0; m_end = 0
                    fy_start = w*L/2; fy_end = w*L/2
                elif member.release_start:
                    # Pin-Fix (Propped)
                    # Moment at pin is 0. Moment at fix increases to wL^2/8
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
                # Assuming simple point load P at magnitude_y
                # Only handling perpendicular loads for now
                P = load.magnitude_y
                # Position? FramePointLoad doesn't assume position along member in API yet?
                # Wait, FramePointLoad on member needs a position. 
                # Currently FramePointLoad in models.py is mainly for NODES.
                # If we use it for members, we need 'location'. 
                # Assuming center for now if generic, or check model update.
                # IMPLEMENTATION NOTE: Only UDL is robustly defined in this plan.
                pass
                
        return fea

    def _calculate_member_forces(self, member: FrameMember, nodes: List[FrameNode], dof_map: Dict, u_total: np.ndarray, fea_local: np.ndarray):
        start_dofs = dof_map[member.start_node_id]
        end_dofs = dof_map[member.end_node_id]
        indices = start_dofs + end_dofs
        u_global_member = u_total[indices]
        
        T = self._get_transformation_matrix(member, nodes)
        u_local = T @ u_global_member
        
        # Recalculate k_local (needed)
        # Performance optim: could cache this. Re-computing for simplicity
        # We need the UN-MODIFIED k_local for Fixed-Fixed, BUT if we used Releases, we must use the Released k_local
        # because the internal Displacement u_local respects the release.
        # Actually: Member Forces = k_local_released * u_local + FEA_released
        
        k_local_matrix_temp = self._calculate_member_global_stiffness(member, nodes) # This returns Global.
        # We need Local.
        # Re-derive local logic or invert transform?
        # k_local = T @ k_global @ T.T ? Yes.
        k_local = T @ k_local_matrix_temp @ T.T
        
        # Calculate forces
        f_local = k_local @ u_local + fea_local
        
        return {
            "member_id": member.id,
            "axial_start": f_local[0],
            "shear_start": f_local[1],
            "moment_start": f_local[2],
            "axial_end": f_local[3],
            "shear_end": f_local[4], # Note: Check sign convention
            "moment_end": f_local[5]
        }

