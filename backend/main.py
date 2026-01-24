"""
FastAPI application for Slope Deflection Method calculator.
Provides REST API for structural analysis calculations.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import CalculationRequest, CalculationResponse, SpanResult, NodeResult, FrameRequest, FrameResponse
from solver import SlopeDeflectionSolver
import traceback

app = FastAPI(
    title="Slope Deflection Calculator API",
    description="Structural analysis API for continuous beams and frames",
    version="1.0.0"
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Slope Deflection Calculator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "slope-deflection-calculator"
    }


@app.post("/api/calculate", response_model=CalculationResponse)
async def calculate(request: CalculationRequest):
    """
    Perform Slope Deflection analysis on the provided beam/frame configuration.
    
    Args:
        request: Beam configuration with spans, supports, and loads
    
    Returns:
        Analysis results with moments, shear, reactions, and optional solution steps
    """
    try:
        # Validate input
        if len(request.spans) < 1:
            raise HTTPException(
                status_code=400,
                detail="At least one span is required"
            )
        
        if len(request.supports) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least two supports are required"
            )
        
        # Create solver instance
        solver = SlopeDeflectionSolver(
            spans=request.spans,
            supports=request.supports
        )
        
        # Solve
        results = solver.solve(include_steps=request.include_steps)
        
        # Format response
        return CalculationResponse(
            success=True,
            span_results=[SpanResult(**r) for r in results["span_results"]],
            node_results=[NodeResult(**r) for r in results["node_results"]],
            solution_steps=results["solution_steps"]
        )
    
    except Exception as e:
        # Log error for debugging
        error_trace = traceback.format_exc()
        print(f"Calculation error: {error_trace}")
        
        return CalculationResponse(
            success=False,
            span_results=[],
            node_results=[],
            error_message=f"Calculation failed: {str(e)}"
        )


@app.post("/api/calculate-frame", response_model=FrameResponse)
async def calculate_frame(request: FrameRequest):
    """
    Perform Direct Stiffness Method analysis on 2D frame.
    """
    try:
        from frame_solver import FrameSolver
        from models import FrameMemberResult, FrameResponse
        
        solver = FrameSolver()
        results = solver.solve(request)
        
        # Convert member results dicts to Pydantic models
        member_results = [
            FrameMemberResult(
                memberId=r["member_id"],
                axialStart=r["axial_start"],
                shearStart=r["shear_start"],
                momentStart=r["moment_start"],
                axialEnd=r["axial_end"],
                shearEnd=r["shear_end"],
                momentEnd=r["moment_end"]
            )
            for r in results["member_results"]
        ]
        
        return FrameResponse(
            success=True,
            displacements=results["displacements"],
            reactions=results["reactions"],
            memberResults=member_results
        )
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Frame calculation error: {error_trace}")
        return FrameResponse(
            success=False,
            displacements=[],
            reactions=[],
            memberResults=[],
            errorMessage=f"Calculation failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
