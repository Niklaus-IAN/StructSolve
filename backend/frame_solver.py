
import numpy as np
import math
from typing import List, Dict, Tuple
from models import FrameRequest, FrameNode, FrameMember, FramePointLoad, FrameUniformLoad, DiagramData

class FrameSolver:
    def solve(self, request: FrameRequest):
        # 1. Setup degrees of freedom (DOF)
        # Each node has 3 DOFs: u (x-disp), v (y-disp), theta (rotation)
        # Global DOF mapping: node_id -> [dof_u, dof_v, dof_theta]
        node_dof_map = self._map_dofs(request.nodes)
        total_dof = 3 * len(request.nodes)
        
        # 2. Assemble Global Stiffness Matrix [K]
        K_global = np.zeros((total_dof, total_dof))
        
        for member in request.members:
            k_global_member = self._calculate_member_global_stiffness(member, request.nodes, node_dof_map)
            
            # Add to system matrix (Scatter)
            start_dofs = node_dof_map[member.start_node_id]
            end_dofs = node_dof_map[member.end_node_id]
            member_dofs = start_dofs + end_dofs # List concatenation [u1, v1, r1, u2, v2, r2]
            
            for i in range(6):
                for j in range(6):
                    row = member_dofs[i]
                    col = member_dofs[j]
                    K_global[row, col] += k_global_member[i, j]
                    
        # 3. Assemble Load Vector {F}
        F_global = np.zeros(total_dof)
        
        # Apply nodal loads directly
        for pl in request.point_loads:
            if pl.type == "NODE_LOAD":
                dofs = node_dof_map[pl.target_id]
                F_global[dofs[0]] += pl.magnitude_x
                F_global[dofs[1]] += pl.magnitude_y
                F_global[dofs[2]] += pl.moment
                
        # Handle member loads (Fixed End Actions converted to equivalent nodal loads)
        # TODO: Add member load handling (FEM conversion)
        
        # 4. Apply Boundary Conditions (Partitioning)
        # Identify free and restrained DOFs
        free_dofs = []
        restrained_dofs = []
        
        for node in request.nodes:
            dofs = node_dof_map[node.id]
            # X-direction
            if not node.fix_x: free_dofs.append(dofs[0])
            else: restrained_dofs.append(dofs[0])
            # Y-direction
            if not node.fix_y: free_dofs.append(dofs[1])
            else: restrained_dofs.append(dofs[1])
            # Rotation
            if not node.fix_r: free_dofs.append(dofs[2])
            else: restrained_dofs.append(dofs[2])
            
        # 5. Solve for Displacements {u} = [K_ff]^-1 ({F_f} - [K_fr]{u_r})
        # Assuming u_r (support displacements) are zero
        
        if not free_dofs:
            raise ValueError("Structure is fully restrained (no free degrees of freedom)")
            
        K_ff = K_global[np.ix_(free_dofs, free_dofs)]
        F_f = F_global[free_dofs]
        
        try:
            u_free = np.linalg.solve(K_ff, F_f)
        except np.linalg.LinAlgError:
            raise ValueError("Structure is unstable or mechanism detected (singular stiffness matrix)")
            
        # Reconstruct full displacement vector
        u_total = np.zeros(total_dof)
        u_total[free_dofs] = u_free
        
        # 6. Post-Processing: Calculate Reactions and Member Forces
        # Reactions {R} = [K_rf]{u_f} + [K_rr]{u_r} - {F_equivalent_restrained}
        reactions = np.zeros(total_dof)
        if restrained_dofs:
            K_rf = K_global[np.ix_(restrained_dofs, free_dofs)]
            reactions[restrained_dofs] = K_rf @ u_free
            # Subtract equivalent nodal loads from reactions to get physical reaction? 
            # R_actual = K*u - F_applied
            reactions = K_global @ u_total - F_global
            
        # Member Forces (Local coordinates)
        member_results = []
        for member in request.members:
            result = self._calculate_member_forces(member, request.nodes, node_dof_map, u_total)
            member_results.append(result)
            
        return {
            "displacements": u_total.tolist(),
            "reactions": reactions.tolist(),
            "member_results": member_results
        }

    def _map_dofs(self, nodes: List[FrameNode]) -> Dict[str, List[int]]:
        """Assign global DOF indices to each node."""
        mapping = {}
        for i, node in enumerate(nodes):
            # 3 DOFs per node (u, v, theta)
            start_index = i * 3
            mapping[node.id] = [start_index, start_index + 1, start_index + 2]
        return mapping

    def _calculate_member_global_stiffness(self, member: FrameMember, nodes: List[FrameNode], dof_map: Dict):
        # Get coordinates
        start_node = next(n for n in nodes if n.id == member.start_node_id)
        end_node = next(n for n in nodes if n.id == member.end_node_id)
        
        dx = end_node.x - start_node.x
        dy = end_node.y - start_node.y
        L = math.sqrt(dx**2 + dy**2)
        
        if L == 0:
            raise ValueError(f"Member {member.id} has zero length")
            
        # Direction cosines
        c = dx / L # cos theta
        s = dy / L # sin theta
        
        # Element properties
        E = member.elastic_modulus * 1e6 # Convert GPa to kN/m2 if needed, assume input is consistent?
        # Inputs: E (kN/m2 or MPa?), I (m4 or mm4?), A (m2 or mm2?)
        # Let's enforce standard SI units in models or conversions here.
        # Frontend defaults: E=200 GPa, I=500 10^6 mm4, A=0.01 m2
        # E input is labeled "E (GPa)" in UI -> convert to kN/m2 (x 1e6)
        # I input is labeled "I (10^6 mm4)" -> convert to m4 (x 1e-6)
        # A input is labeled "A (m2)" -> no conversion
        
        # Actually in models.py descriptions:
        # E (kN/m²), I (m⁴), A (m²)
        # So we assume incoming values are already in base SI (kN, m)
        # But UI labels say otherwise. I need to match UI conversion layers or assume UI converts.
        # Let's assume input to backend IS base units.
        
        E = member.elastic_modulus
        I = member.moment_of_inertia
        A = member.cross_section_area
        
        # Local Stiffness Matrix [k'] (6x6)
        # standard frame element
        k_local = np.array([
            [E*A/L,  0,        0,         -E*A/L, 0,        0],
            [0,      12*E*I/L**3, 6*E*I/L**2, 0,      -12*E*I/L**3, 6*E*I/L**2],
            [0,      6*E*I/L**2,  4*E*I/L,    0,      -6*E*I/L**2,  2*E*I/L],
            [-E*A/L, 0,        0,         E*A/L,  0,        0],
            [0,      -12*E*I/L**3, -6*E*I/L**2, 0,      12*E*I/L**3, -6*E*I/L**2],
            [0,      6*E*I/L**2,   2*E*I/L,     0,      -6*E*I/L**2,  4*E*I/L]
        ])
        
        # Transformation Matrix [T]
        T = np.zeros((6, 6))
        sub_T = np.array([
            [c,  s, 0],
            [-s, c, 0],
            [0,  0, 1]
        ])
        T[0:3, 0:3] = sub_T
        T[3:6, 3:6] = sub_T
        
        # Global Stiffness [k] = [T]^T [k'] [T]
        k_global = T.T @ k_local @ T
        return k_global

    def _calculate_member_forces(self, member: FrameMember, nodes: List[FrameNode], dof_map: Dict, u_total: np.ndarray):
        start_dofs = dof_map[member.start_node_id]
        end_dofs = dof_map[member.end_node_id]
        indices = start_dofs + end_dofs
        
        # Member global displacements
        u_global_member = u_total[indices]
        
        # Calculate local displacements
        start_node = next(n for n in nodes if n.id == member.start_node_id)
        end_node = next(n for n in nodes if n.id == member.end_node_id)
        dx = end_node.x - start_node.x
        dy = end_node.y - start_node.y
        L = math.sqrt(dx**2 + dy**2)
        c = dx / L
        s = dy / L
        
        T = np.zeros((6, 6))
        sub_T = np.array([
            [c,  s, 0],
            [-s, c, 0],
            [0,  0, 1]
        ])
        T[0:3, 0:3] = sub_T
        T[3:6, 3:6] = sub_T
        
        u_local = T @ u_global_member
        
        # Calculate member local forces {f'} = [k']{u'}
        E = member.elastic_modulus
        I = member.moment_of_inertia
        A = member.cross_section_area
        
        k_local = np.array([
            [E*A/L,  0,        0,         -E*A/L, 0,        0],
            [0,      12*E*I/L**3, 6*E*I/L**2, 0,      -12*E*I/L**3, 6*E*I/L**2],
            [0,      6*E*I/L**2,  4*E*I/L,    0,      -6*E*I/L**2,  2*E*I/L],
            [-E*A/L, 0,        0,         E*A/L,  0,        0],
            [0,      -12*E*I/L**3, -6*E*I/L**2, 0,      12*E*I/L**3, -6*E*I/L**2],
            [0,      6*E*I/L**2,   2*E*I/L,     0,      -6*E*I/L**2,  4*E*I/L]
        ])
        
        f_local = k_local @ u_local
        
        # f_local format: [Nx1, Vy1, Mz1, Nx2, Vy2, Mz2]
        # N = Axial, Vy = Shear, Mz = Moment
        
        return {
            "member_id": member.id,
            "axial_start": f_local[0],
            "shear_start": f_local[1],
            "moment_start": f_local[2],
            "axial_end": f_local[3],
            "shear_end": f_local[4],
            "moment_end": f_local[5]
        }
