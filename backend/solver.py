"""
Core structural analysis solver using the Slope Deflection Method.
Handles continuous beams and frames with various load types.
"""
import numpy as np
from typing import List, Tuple, Dict
from models import Span, Support, LoadConfig, SolutionStep


def calculate_fem(load: LoadConfig, length: float) -> Tuple[float, float]:
    """
    Calculate Fixed End Moments for various load types.
    
    Sign Convention: Clockwise moment is NEGATIVE, Counter-clockwise is POSITIVE
    
    Args:
        load: Load configuration
        length: Span length in meters
    
    Returns:
        Tuple of (FEM_left, FEM_right) in kN·m
    """
    L = length
    w = load.magnitude
    
    if load.load_type == "UDL":
        # Uniformly Distributed Load: wL²/12
        fem = (w * L**2) / 12
        return (fem, -fem)
    
    elif load.load_type == "POINT_CENTER":
        # Point load at center: PL/8
        fem = (w * L) / 8
        return (fem, -fem)
    
    elif load.load_type == "POINT_ARBITRARY":
        # Point load at arbitrary position
        a = load.position  # Distance from left
        b = L - a  # Distance from right
        
        # FEM_left = -Pab²/L²
        # FEM_right = Pa²b/L²
        fem_left = -(w * a * b**2) / L**2
        fem_right = (w * a**2 * b) / L**2
        return (fem_left, fem_right)
    
    elif load.load_type == "TRIANGULAR":
        # Triangular load (zero at left, maximum at right)
        # FEM_left = wL²/30
        # FEM_right = -wL²/20
        fem_left = (w * L**2) / 30
        fem_right = -(w * L**2) / 20
        return (fem_left, fem_right)
    
    elif load.load_type == "MOMENT":
        # Applied moment at left end
        return (w, 0)
    
    else:  # NONE
        return (0.0, 0.0)


def calculate_total_fem(loads: List[LoadConfig], length: float) -> Tuple[float, float]:
    """
    Calculate total Fixed End Moments from multiple loads on a span.
    
    Args:
        loads: List of load configurations
        length: Span length
    
    Returns:
        Total (FEM_left, FEM_right)
    """
    fem_left_total = 0.0
    fem_right_total = 0.0
    
    for load in loads:
        fem_l, fem_r = calculate_fem(load, length)
        fem_left_total += fem_l
        fem_right_total += fem_r
    
    return (fem_left_total, fem_right_total)


class SlopeDeflectionSolver:
    """Solver for continuous beams using the Slope Deflection Method."""
    
    def __init__(self, spans: List[Span], supports: List[Support]):
        self.spans = spans
        self.supports = supports
        self.num_spans = len(spans)
        self.num_nodes = self.num_spans + 1
        self.solution_steps: List[SolutionStep] = []
        
        # Create support lookup
        self.support_map: Dict[int, str] = {}
        for support in supports:
            self.support_map[support.node_index] = support.support_type
    
    def solve(self, include_steps: bool = True) -> Dict:
        """
        Main solver method.
        
        Returns:
            Dictionary with span_results, node_results, and solution_steps
        """
        self.include_steps = include_steps
        self.step_counter = 1
        
        # Step 1: Calculate Fixed End Moments
        self._add_step("Calculate Fixed End Moments (FEMs) for each span")
        fems = self._calculate_all_fems()
        
        # Step 2: Assemble stiffness matrix
        self._add_step("Assemble global stiffness matrix using Slope Deflection equations")
        K, F = self._assemble_system(fems)
        
        # Step 3: Apply boundary conditions
        self._add_step("Apply boundary conditions (zero rotation at fixed supports)")
        K_reduced, F_reduced, free_dofs = self._apply_boundary_conditions(K, F)
        
        # Step 4: Solve for unknown rotations
        self._add_step("Solve system of equations for unknown rotations")
        rotations = self._solve_rotations(K_reduced, F_reduced, free_dofs)
        
        # Step 5: Calculate final moments
        self._add_step("Calculate final end moments using Slope Deflection equation")
        span_results = self._calculate_moments(rotations, fems)
        
        # Step 6: Calculate reactions
        self._add_step("Calculate support reactions using equilibrium")
        node_results = self._calculate_reactions(span_results, rotations)
        
        return {
            "span_results": span_results,
            "node_results": node_results,
            "solution_steps": self.solution_steps if include_steps else None
        }
    
    def _add_step(self, description: str, equation: str = None, result: str = None):
        """Add a solution step for educational output."""
        if self.include_steps:
            self.solution_steps.append(SolutionStep(
                step_number=self.step_counter,
                description=description,
                equation=equation,
                result=result
            ))
            self.step_counter += 1
    
    def _calculate_all_fems(self) -> List[Tuple[float, float]]:
        """Calculate FEMs for all spans."""
        fems = []
        for i, span in enumerate(self.spans):
            fem_l, fem_r = calculate_total_fem(span.loads, span.length)
            fems.append((fem_l, fem_r))
            
            if self.include_steps:
                self._add_step(
                    f"Span {i+1}: L={span.length}m, EI={span.elastic_modulus * span.moment_of_inertia:.2e}",
                    equation=f"FEM_left = {fem_l:.2f} kN·m, FEM_right = {fem_r:.2f} kN·m"
                )
        
        return fems
    
    def _assemble_system(self, fems: List[Tuple[float, float]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Assemble global stiffness matrix and force vector.
        
        Slope Deflection Equation:
        M_ij = (2EI/L)(2θ_i + θ_j - 3ψ) + FEM_ij
        
        For beams without sway (ψ = 0):
        M_ij = (2EI/L)(2θ_i + θ_j) + FEM_ij
        """
        K = np.zeros((self.num_nodes, self.num_nodes))
        F = np.zeros(self.num_nodes)
        
        for i, span in enumerate(self.spans):
            L = span.length
            EI = span.elastic_modulus * span.moment_of_inertia
            k = (2 * EI) / L
            
            fem_left, fem_right = fems[i]
            
            # Node indices
            node_a = i
            node_b = i + 1
            
            # Equilibrium at node A: Sum of moments = 0
            # M_ab contributes: k(2θ_a + θ_b) + FEM_ab
            K[node_a, node_a] += 4 * k
            K[node_a, node_b] += 2 * k
            F[node_a] -= fem_left
            
            # Equilibrium at node B
            # M_ba contributes: k(2θ_b + θ_a) + FEM_ba
            K[node_b, node_b] += 4 * k
            K[node_b, node_a] += 2 * k
            F[node_b] -= fem_right
        
        return K, F
    
    def _apply_boundary_conditions(self, K: np.ndarray, F: np.ndarray) -> Tuple[np.ndarray, np.ndarray, List[int]]:
        """
        Apply boundary conditions by removing rows/columns for fixed supports.
        
        Returns:
            Reduced K matrix, reduced F vector, and list of free DOFs
        """
        free_dofs = []
        
        for node_idx in range(self.num_nodes):
            support_type = self.support_map.get(node_idx, "ROLLER")
            
            # Fixed supports have zero rotation (known), so remove from unknowns
            # Pinned and Roller supports have unknown rotation (free DOF)
            if support_type in ["PINNED", "ROLLER"]:
                free_dofs.append(node_idx)
        
        # Extract reduced system
        K_reduced = K[np.ix_(free_dofs, free_dofs)]
        F_reduced = F[free_dofs]
        
        return K_reduced, F_reduced, free_dofs
    
    def _solve_rotations(self, K_reduced: np.ndarray, F_reduced: np.ndarray, 
                        free_dofs: List[int]) -> np.ndarray:
        """Solve for unknown rotations."""
        rotations = np.zeros(self.num_nodes)
        
        if len(free_dofs) > 0:
            # Solve reduced system
            theta_free = np.linalg.solve(K_reduced, F_reduced)
            
            # Map back to full rotation vector
            for i, dof in enumerate(free_dofs):
                rotations[dof] = theta_free[i]
                
                if self.include_steps:
                    self._add_step(
                        f"Node {dof}: θ = {theta_free[i]:.6f} radians"
                    )
        
        return rotations
    
    def _calculate_moments(self, rotations: np.ndarray, 
                          fems: List[Tuple[float, float]]) -> List[Dict]:
        """Calculate final end moments for each span."""
        span_results = []
        
        for i, span in enumerate(self.spans):
            L = span.length
            EI = span.elastic_modulus * span.moment_of_inertia
            k = (2 * EI) / L
            
            theta_a = rotations[i]
            theta_b = rotations[i + 1]
            fem_left, fem_right = fems[i]
            
            # Slope Deflection equation
            M_ab = k * (2 * theta_a + theta_b) + fem_left
            M_ba = k * (2 * theta_b + theta_a) + fem_right
            
            # Calculate shear forces (simplified - assumes no axial loads)
            V_a = (M_ab + M_ba) / L
            V_b = -V_a
            
            # Find maximum moment location (simplified for UDL)
            max_moment = max(abs(M_ab), abs(M_ba))
            max_location = L / 2  # Simplified
            
            span_results.append({
                "span_index": i,
                "moment_left": M_ab,
                "moment_right": M_ba,
                "shear_left": V_a,
                "shear_right": V_b,
                "max_moment": max_moment,
                "max_moment_location": max_location
            })
            
            if self.include_steps:
                self._add_step(
                    f"Span {i+1} moments",
                    equation=f"M_AB = {k:.2e}(2×{theta_a:.6f} + {theta_b:.6f}) + {fem_left:.2f}",
                    result=f"M_AB = {M_ab:.2f} kN·m, M_BA = {M_ba:.2f} kN·m"
                )
        
        return span_results
    
    def _calculate_reactions(self, span_results: List[Dict], 
                            rotations: np.ndarray) -> List[Dict]:
        """Calculate support reactions."""
        node_results = []
        
        for node_idx in range(self.num_nodes):
            support_type = self.support_map.get(node_idx, "ROLLER")
            
            # Calculate vertical reaction (sum of shears at node)
            reaction = 0.0
            
            # Left span contribution
            if node_idx > 0:
                reaction += span_results[node_idx - 1]["shear_right"]
            
            # Right span contribution
            if node_idx < self.num_spans:
                reaction += span_results[node_idx]["shear_left"]
            
            # Moment reaction for fixed supports
            moment_reaction = None
            if support_type == "FIXED":
                if node_idx > 0:
                    moment_reaction = span_results[node_idx - 1]["moment_right"]
                elif node_idx < self.num_spans:
                    moment_reaction = span_results[node_idx]["moment_left"]
            
            node_results.append({
                "node_index": node_idx,
                "rotation": rotations[node_idx],
                "reaction": reaction,
                "moment_reaction": moment_reaction
            })
        
        return node_results
