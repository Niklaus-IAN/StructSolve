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
        # FEM_left = -wL²/12 (hogging)
        # FEM_right = +wL²/12 (hogging)
        fem = (w * L**2) / 12
        return (-fem, fem)
    
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
            # Coefficient of θ_a is 2k, coefficient of θ_b is k
            K[node_a, node_a] += 2 * k
            K[node_a, node_b] += k
            F[node_a] -= fem_left
            
            # Equilibrium at node B
            # M_ba contributes: k(2θ_b + θ_a) + FEM_ba
            # Coefficient of θ_b is 2k, coefficient of θ_a is k
            K[node_b, node_b] += 2 * k
            K[node_b, node_a] += k
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
        """
        Calculate final end moments and generate diagram data for each span.
        Uses FBD method for reactions and separates FMD, EMD, and BMD.
        """
        span_results = []
        
        for i, span in enumerate(self.spans):
            L = span.length
            EI = span.elastic_modulus * span.moment_of_inertia
            k = (2 * EI) / L
            
            theta_a = rotations[i]
            theta_b = rotations[i + 1]
            fem_left, fem_right = fems[i]
            
            # Slope Deflection equation for end moments
            M_ab = k * (2 * theta_a + theta_b) + fem_left
            M_ba = k * (2 * theta_b + theta_a) + fem_right
            
            # Calculate reactions using FBD method
            R_left, R_right = self._calculate_span_reactions(span, M_ab, M_ba)
            
            # Generate diagram data (SFD, FMD, EMD, BMD)
            diagram_data = self._generate_diagram_data(span, M_ab, M_ba, R_left, R_right)
            
            # Find maximum moment and its location
            bmd_values = diagram_data["bmd_data"].values
            max_moment_idx = np.argmax(np.abs(bmd_values))
            max_moment = bmd_values[max_moment_idx]
            max_location = diagram_data["bmd_data"].x_coords[max_moment_idx]

            
            span_results.append({
                "span_index": i,
                "moment_left": M_ab,
                "moment_right": M_ba,
                "shear_left": R_left,
                "shear_right": -R_right,  # Negative because it acts downward on span
                "max_moment": max_moment,
                "max_moment_location": max_location,
                **diagram_data  # Include sfd_data, fmd_data, emd_data, bmd_data
            })
            
            if self.include_steps:
                self._add_step(
                    f"Span {i+1} analysis",
                    equation=f"M_AB = {k:.2e}(2×{theta_a:.6f} + {theta_b:.6f}) + {fem_left:.2f}",
                    result=f"M_AB = {M_ab:.2f} kN·m, M_BA = {M_ba:.2f} kN·m, R_left = {R_left:.2f} kN, R_right = {R_right:.2f} kN"
                )
        
        return span_results
    
    def _calculate_span_reactions(self, span: 'Span', M_ab: float, M_ba: float) -> Tuple[float, float]:
        """
        Calculate reactions for a span using Free Body Diagram method.
        
        Algorithm:
        1. Isolate the span
        2. Apply end moments as external loads
        3. Sum moments about right support to find left reaction
        4. Sum forces to find right reaction
        
        Args:
            span: Span object with loads
            M_ab: Moment at left end (from Slope Deflection)
            M_ba: Moment at right end (from Slope Deflection)
        
        Returns:
            Tuple of (R_left, R_right) in kN
        """
        L = span.length
        
        # Calculate total load and moment contribution from loads
        total_load = 0.0
        moment_about_right = 0.0  # Moment about right support from loads
        
        for load in span.loads:
            w = load.magnitude
            
            if load.load_type == "UDL":
                # Total load = w * L
                total_load += w * L
                # Acts at center: distance from right = L/2
                moment_about_right += w * L * (L / 2)
            
            elif load.load_type == "POINT_CENTER":
                total_load += w
                moment_about_right += w * (L / 2)
            
            elif load.load_type == "POINT_ARBITRARY":
                a = load.position  # Distance from left
                total_load += w
                moment_about_right += w * (L - a)
            
            elif load.load_type == "TRIANGULAR":
                # Triangular load (zero at left, max at right)
                total_load += (w * L) / 2
                # Centroid at 2L/3 from left, L/3 from right
                moment_about_right += ((w * L) / 2) * (L / 3)
        
        # Sum moments about right support (clockwise positive)
        # Taking moments about B: R_A × L + M_BA - M_AB - moment_from_loads = 0
        # Rearranging: R_A = (M_AB - M_BA + moment_from_loads) / L
        # But we need to be careful with signs:
        # M_AB is the SD moment (negative for hogging)
        # In FBD, we use: R_left × L + M_BA - |M_AB| - moment_from_loads = 0
        # So: R_left = (|M_AB| - M_BA + moment_from_loads) / L
        #     R_left = (-M_AB - M_BA + moment_from_loads) / L
        R_left = (-M_ab - M_ba + moment_about_right) / L
        
        # Sum vertical forces
        R_right = total_load - R_left
        
        return (R_left, R_right)
    
    def _generate_diagram_data(self, span: 'Span', M_ab: float, M_ba: float, 
                              R_left: float, R_right: float) -> Dict:
        """
        Generate data points for SFD, FMD, EMD, and BMD.
        
        Key: Separates Free Moment Diagram (FMD) and End Moment Diagram (EMD),
        then superposes them to get complete BMD.
        
        Sign Convention Translation:
        - Slope Deflection: Clockwise (-), Counter-Clockwise (+)
        - BMD: Sagging (+), Hogging (-)
        """
        L = span.length
        num_points = 100
        x_coords = np.linspace(0, L, num_points).tolist()
        
        sfd_values = []
        fmd_values = []
        emd_values = []
        
        # Calculate simply-supported reaction for FMD
        # (as if there were no end moments)
        R_left_ss = self._calculate_simply_supported_reaction(span)
        
        for x in x_coords:
            # === Shear Force Diagram ===
            shear = self._calculate_shear_at_x(span, x, R_left)
            sfd_values.append(shear)
            
            # === Free Moment Diagram (FMD) - Simply Supported ===
            fmd = self._calculate_free_moment_at_x(span, x, R_left_ss)
            fmd_values.append(fmd)
            
            # === End Moment Diagram (EMD) - Linear variation ===
            # CRITICAL: Sign convention translation
            # Slope Deflection moments need to be converted to BMD convention
            # For hogging (tension on top): negative in BMD
            M_left_bmd = M_ab  # Keep as is (will be negative for hogging)
            M_right_bmd = -M_ba # Negate (SD 'positive' hogging -> BMD 'negative' hogging)
            
            # Linear interpolation
            emd = M_left_bmd + (M_right_bmd - M_left_bmd) * (x / L)
            emd_values.append(emd)
        
        # === Complete BMD = FMD + EMD (Superposition) ===
        bmd_values = [fmd + emd for fmd, emd in zip(fmd_values, emd_values)]
        
        from models import DiagramData
        
        return {
            "sfd_data": DiagramData(x_coords=x_coords, values=sfd_values),
            "fmd_data": DiagramData(x_coords=x_coords, values=fmd_values),
            "emd_data": DiagramData(x_coords=x_coords, values=emd_values),
            "bmd_data": DiagramData(x_coords=x_coords, values=bmd_values)
        }
    
    def _calculate_simply_supported_reaction(self, span: 'Span') -> float:
        """Calculate left reaction as if beam were simply supported (no end moments)."""
        L = span.length
        moment_about_right = 0.0
        
        for load in span.loads:
            w = load.magnitude
            
            if load.load_type == "UDL":
                moment_about_right += w * L * (L / 2)
            elif load.load_type == "POINT_CENTER":
                moment_about_right += w * (L / 2)
            elif load.load_type == "POINT_ARBITRARY":
                a = load.position
                moment_about_right += w * (L - a)
            elif load.load_type == "TRIANGULAR":
                moment_about_right += ((w * L) / 2) * (L / 3)
        
        return moment_about_right / L
    
    def _calculate_shear_at_x(self, span: 'Span', x: float, R_left: float) -> float:
        """Calculate shear force at position x along the span."""
        shear = R_left
        
        for load in span.loads:
            w = load.magnitude
            
            if load.load_type == "UDL":
                # Subtract distributed load up to point x
                shear -= w * x
            
            elif load.load_type == "POINT_CENTER":
                if x > span.length / 2:
                    shear -= w
            
            elif load.load_type == "POINT_ARBITRARY":
                if x > load.position:
                    shear -= w
            
            elif load.load_type == "TRIANGULAR":
                # Triangular load intensity at x: w_x = w * (x / L)
                # Resultant up to x: (w * x / L) * x / 2 = w * x² / (2L)
                shear -= w * x**2 / (2 * span.length)
        
        return shear
    
    def _calculate_free_moment_at_x(self, span: 'Span', x: float, R_left: float) -> float:
        """Calculate free moment (simply supported) at position x."""
        moment = R_left * x
        
        for load in span.loads:
            w = load.magnitude
            
            if load.load_type == "UDL":
                # M = R*x - w*x²/2
                moment -= w * x**2 / 2
            
            elif load.load_type == "POINT_CENTER":
                if x > span.length / 2:
                    moment -= w * (x - span.length / 2)
            
            elif load.load_type == "POINT_ARBITRARY":
                if x > load.position:
                    moment -= w * (x - load.position)
            
            elif load.load_type == "TRIANGULAR":
                # For triangular load, moment contribution is more complex
                # Resultant acts at centroid of triangle up to x
                # M = w * x³ / (6L)
                moment -= w * x**3 / (6 * span.length)
        
        return moment
    
    def _calculate_reactions(self, span_results: List[Dict], 
                            rotations: np.ndarray) -> List[Dict]:
        """
        Calculate support reactions by stitching together span reactions.
        """
        node_results = []
        
        for node_idx in range(self.num_nodes):
            support_type = self.support_map.get(node_idx, "ROLLER")
            
            # Calculate vertical reaction (sum of contributions from adjacent spans)
            reaction = 0.0
            
            # Left span contribution (reaction pointing up)
            if node_idx > 0:
                reaction += -span_results[node_idx - 1]["shear_right"]
            
            # Right span contribution (reaction pointing up)
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

