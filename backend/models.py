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
    x_coords: List[float] = Field(description="X coordinates along span (m)", alias="xCoords")
    values: List[float] = Field(description="Y values at each x coordinate")

    class Config:
        populate_by_name = True


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
    node_index: int = Field(ge=0, description="Index of the node (0-based)", alias="nodeIndex")
    support_type: Literal["FIXED", "PINNED", "ROLLER"] = Field(
        description="Type of support",
        alias="supportType"
    )

    class Config:
        populate_by_name = True


class CalculationRequest(BaseModel):
    """Complete beam/frame configuration for analysis."""
    spans: List[Span] = Field(min_length=1, description="List of spans")
    supports: List[Support] = Field(
        min_length=2,
        description="Support configurations (minimum 2 required)"
    )
    include_steps: bool = Field(
        default=True,
        description="Include step-by-step solution in response",
        alias="includeSteps"
    )

    class Config:
        populate_by_name = True


class SpanResult(BaseModel):
    """Analysis results for a single span."""
    span_index: int = Field(alias="spanId") # Mapping index to spanId for frontend compatibility
    moment_left: float = Field(description="Bending moment at left end (kN·m)", alias="momentLeft")
    moment_right: float = Field(description="Bending moment at right end (kN·m)", alias="momentRight")
    shear_left: float = Field(description="Shear force at left end (kN)", alias="shearLeft")
    shear_right: float = Field(description="Shear force at right end (kN)", alias="shearRight")
    max_moment: float = Field(description="Maximum moment in span (kN·m)", alias="maxMoment")
    max_moment_location: float = Field(description="Location of max moment from left (m)", alias="maxMomentLocation")
    
    # Diagram data for visualization
    sfd_data: DiagramData = Field(description="Shear Force Diagram data", alias="sfdData")
    fmd_data: DiagramData = Field(description="Free Moment Diagram data (simply supported)", alias="fmdData")
    emd_data: DiagramData = Field(description="End Moment Diagram data (from support moments)", alias="emdData")
    bmd_data: DiagramData = Field(description="Complete Bending Moment Diagram (FMD + EMD)", alias="bmdData")

    class Config:
        populate_by_name = True


class NodeResult(BaseModel):
    """Results at a support node."""
    node_index: int = Field(alias="nodeIndex")
    rotation: float = Field(description="Rotation at node (radians)")
    reaction: float = Field(description="Vertical reaction force (kN)")
    moment_reaction: Optional[float] = Field(
        default=None,
        description="Moment reaction for fixed supports (kN·m)",
        alias="momentReaction"
    )

    class Config:
        populate_by_name = True


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

# === FRAME ANALYSIS MODELS ===

class FrameNode(BaseModel):
    """A node in a 2D frame structure."""
    id: str = Field(description="Unique identifier for the node")
    x: float = Field(description="X coordinate (m)")
    y: float = Field(description="Y coordinate (m)")
    # Support conditions (True = Fixed/Restrained, False = Free)
    fix_x: bool = Field(default=False, description="Fixed in X direction", alias="fixX")
    fix_y: bool = Field(default=False, description="Fixed in Y direction", alias="fixY")
    fix_r: bool = Field(default=False, description="Fixed rotation", alias="fixR")

    class Config:
        populate_by_name = True


class FrameMember(BaseModel):
    """A member connecting two nodes in a 2D frame."""
    id: str = Field(description="Unique identifier for the member")
    start_node_id: str = Field(description="ID of start node", alias="startNodeId")
    end_node_id: str = Field(description="ID of end node", alias="endNodeId")
    elastic_modulus: float = Field(gt=0, description="Elastic modulus E (kN/m²)", alias="elasticModulus")
    moment_of_inertia: float = Field(gt=0, description="Moment of inertia I (m⁴)", alias="momentOfInertia")
    cross_section_area: float = Field(gt=0, description="Cross-sectional area A (m²)", alias="crossSectionArea")
    release_start: bool = Field(default=False, description="Pin start joint", alias="releaseStart")
    release_end: bool = Field(default=False, description="Pin end joint", alias="releaseEnd")

    class Config:
        populate_by_name = True


class FramePointLoad(BaseModel):
    """Point load applied to a node or member."""
    type: Literal["NODE_LOAD", "MEMBER_POINT_LOAD"] = Field(description="Type of point load")
    target_id: str = Field(description="Node ID or Member ID applied to", alias="targetId")
    magnitude_x: float = Field(default=0, description="Force in X direction (kN)", alias="magnitudeX")
    magnitude_y: float = Field(default=0, description="Force in Y direction (kN)", alias="magnitudeY")
    moment: float = Field(default=0, description="Moment (kNm)", alias="moment")
    position: Optional[float] = Field(default=None, description="Distance from start node (for member loads)")

    class Config:
        populate_by_name = True


class FrameUniformLoad(BaseModel):
    """Uniformly distributed load applied to a member."""
    member_id: str = Field(description="ID of member", alias="memberId")
    magnitude_x: float = Field(default=0, description="UDL in local X direction (kN/m)", alias="magnitudeX")
    magnitude_y: float = Field(default=0, description="UDL in local Y direction (kN/m)", alias="magnitudeY")

    class Config:
        populate_by_name = True


class FrameRequest(BaseModel):
    """Complete configuration for 2D Frame Analysis."""
    nodes: List[FrameNode]
    members: List[FrameMember]
    point_loads: List[FramePointLoad] = Field(default_factory=list, alias="pointLoads")
    uniform_loads: List[FrameUniformLoad] = Field(default_factory=list, alias="uniformLoads")

    class Config:
        populate_by_name = True


class FrameMemberResult(BaseModel):
    """Internal forces for a frame member."""
    member_id: str = Field(alias="memberId")
    axial_start: float = Field(alias="axialStart")
    shear_start: float = Field(alias="shearStart")
    moment_start: float = Field(alias="momentStart")
    axial_end: float = Field(alias="axialEnd")
    shear_end: float = Field(alias="shearEnd")
    moment_end: float = Field(alias="momentEnd")
    # Diagram Data
    stations: Optional[List[float]] = None
    n_diagram: Optional[List[float]] = Field(None, alias="nDiagram")
    v_diagram: Optional[List[float]] = Field(None, alias="vDiagram")
    m_diagram: Optional[List[float]] = Field(None, alias="mDiagram")

    class Config:
        populate_by_name = True


class FrameResponse(BaseModel):
    """Results of Frame Analysis."""
    success: bool
    displacements: List[float]
    reactions: List[float]
    member_results: List[FrameMemberResult] = Field(alias="memberResults")
    error_message: Optional[str] = Field(None, alias="errorMessage")

    class Config:
        populate_by_name = True
