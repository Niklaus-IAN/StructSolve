"""
Pydantic models for request/response validation in the Slope Deflection calculator.
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class LoadConfig(BaseModel):
    """Configuration for a load applied to a span."""
    load_type: Literal["UDL", "POINT_CENTER", "POINT_ARBITRARY", "TRIANGULAR", "MOMENT", "NONE"] = Field(
        description="Type of load applied"
    )
    magnitude: float = Field(
        default=0.0,
        description="Load magnitude (kN for forces, kN/m for distributed loads, kN·m for moments)"
    )
    position: Optional[float] = Field(
        default=None,
        description="Position along span for point loads (m from left end)"
    )


class DiagramData(BaseModel):
    """Data points for a diagram (SFD, FMD, EMD, BMD)."""
    x_coords: List[float] = Field(description="X coordinates along span (m)")
    values: List[float] = Field(description="Y values at each x coordinate")


class Span(BaseModel):
    """Represents a single span in the beam/frame."""
    id: str = Field(description="Unique identifier for the span")
    length: float = Field(gt=0, description="Length of span in meters")
    elastic_modulus: float = Field(
        gt=0,
        description="Elastic modulus E in kN/m²",
        alias="elasticModulus"
    )
    moment_of_inertia: float = Field(
        gt=0,
        description="Moment of inertia I in m⁴",
        alias="momentOfInertia"
    )
    loads: List[LoadConfig] = Field(
        default_factory=list,
        description="List of loads applied to this span"
    )

    class Config:
        populate_by_name = True


class Support(BaseModel):
    """Support configuration at a node."""
    node_index: int = Field(ge=0, description="Index of the node (0-based)")
    support_type: Literal["FIXED", "PINNED", "ROLLER"] = Field(
        description="Type of support"
    )


class CalculationRequest(BaseModel):
    """Complete beam/frame configuration for analysis."""
    spans: List[Span] = Field(min_length=1, description="List of spans")
    supports: List[Support] = Field(
        min_length=2,
        description="Support configurations (minimum 2 required)"
    )
    include_steps: bool = Field(
        default=True,
        description="Include step-by-step solution in response"
    )


class SpanResult(BaseModel):
    """Analysis results for a single span."""
    span_index: int
    moment_left: float = Field(description="Bending moment at left end (kN·m)")
    moment_right: float = Field(description="Bending moment at right end (kN·m)")
    shear_left: float = Field(description="Shear force at left end (kN)")
    shear_right: float = Field(description="Shear force at right end (kN)")
    max_moment: float = Field(description="Maximum moment in span (kN·m)")
    max_moment_location: float = Field(description="Location of max moment from left (m)")
    
    # Diagram data for visualization
    sfd_data: DiagramData = Field(description="Shear Force Diagram data")
    fmd_data: DiagramData = Field(description="Free Moment Diagram data (simply supported)")
    emd_data: DiagramData = Field(description="End Moment Diagram data (from support moments)")
    bmd_data: DiagramData = Field(description="Complete Bending Moment Diagram (FMD + EMD)")



class NodeResult(BaseModel):
    """Results at a support node."""
    node_index: int
    rotation: float = Field(description="Rotation at node (radians)")
    reaction: float = Field(description="Vertical reaction force (kN)")
    moment_reaction: Optional[float] = Field(
        default=None,
        description="Moment reaction for fixed supports (kN·m)"
    )


class SolutionStep(BaseModel):
    """A single step in the solution process."""
    step_number: int
    description: str
    equation: Optional[str] = None
    result: Optional[str] = None


class CalculationResponse(BaseModel):
    """Complete analysis results."""
    success: bool
    span_results: List[SpanResult]
    node_results: List[NodeResult]
    solution_steps: Optional[List[SolutionStep]] = None
    error_message: Optional[str] = None
