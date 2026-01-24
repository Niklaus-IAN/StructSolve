import { Span, CalculationResult } from './types';

// Use environment variable in production, fallback to localhost in development
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Solve continuous beam using the Python FastAPI backend.
 * This calls the accurate Slope Deflection Method solver implemented in Python with NumPy.
 */
export async function solveContinuousBeam(spans: Span[]): Promise<CalculationResult> {
  try {
    // Convert frontend span format to backend API format
    const backendSpans = spans.map((span, index) => ({
      id: span.id,
      length: span.length,
      elasticModulus: span.elasticModulus * 1000000, // Convert to kN/m² (GPa to kN/m²)
      momentOfInertia: span.inertia / 1000000, // Convert to m⁴ (cm⁴ to m⁴)
      loads: [{
        load_type: span.loadType === 'UDL' ? 'UDL' :
          span.loadType === 'POINT_CENTER' ? 'POINT_CENTER' :
            span.loadType === 'POINT_ARBITRARY' ? 'POINT_ARBITRARY' :
              span.loadType === 'TRIANGULAR' ? 'TRIANGULAR' :
                span.loadType === 'MOMENT' ? 'MOMENT' : 'NONE',
        magnitude: span.loadMagnitude,
        position: span.loadType === 'POINT_ARBITRARY' ? span.loadPosition : undefined
      }]
    }));

    // Build supports array from span support types
    const supports = [];
    spans.forEach((span, index) => {
      // Add left support for first span
      if (index === 0) {
        supports.push({
          node_index: 0,
          support_type: span.leftSupport
        });
      }
      // Add right support for each span
      supports.push({
        node_index: index + 1,
        support_type: span.rightSupport
      });
    });

    // Call Python backend API
    const response = await fetch(`${API_URL}/api/calculate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        spans: backendSpans,
        supports: supports,
        include_steps: false // Set to true if you want step-by-step solution
      })
    });

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`);
    }

    const data = await response.json();

    console.log('Backend response:', data); // Debug logging

    if (!data.success) {
      throw new Error(data.error_message || 'Calculation failed');
    }

    if (!data.span_results || data.span_results.length === 0) {
      throw new Error('No span results returned from backend');
    }

    // Convert backend response to frontend format
    const results: CalculationResult = {
      spans: data.span_results.map((spanResult: any, index: number) => {
        const span = spans[index];
        const steps = 20;
        const dx = span.length / steps;

        // Generate stations for plotting
        const stations: number[] = [];
        const shearForce: number[] = [];
        const bendingMoment: number[] = [];

        let currentX = spans.slice(0, index).reduce((sum, s) => sum + s.length, 0);

        // Create smooth curves for visualization
        for (let i = 0; i <= steps; i++) {
          const x = i * dx;
          stations.push(currentX + x);

          // Linear interpolation for bending moment
          const t = i / steps;
          const moment = spanResult.moment_left * (1 - t) + spanResult.moment_right * t;
          bendingMoment.push(moment);

          // Approximate shear (constant for now, could be improved)
          const shear = i < steps / 2 ? spanResult.shear_left : spanResult.shear_right;
          shearForce.push(shear);
        }

        return {
          spanId: span.id,
          stations,
          shearForce,
          bendingMoment,
          slope: new Array(steps + 1).fill(0), // Not calculated yet
          deflection: new Array(steps + 1).fill(0), // Not calculated yet
          momentLeft: spanResult.moment_left,
          momentRight: spanResult.moment_right
        };
      }),
      reactions: data.node_results.map((node: any) => node.reaction),
      maxMoment: Math.max(...data.span_results.map((s: any) => s.max_moment)),
      maxShear: Math.max(...data.span_results.map((s: any) => Math.max(
        Math.abs(s.shear_left),
        Math.abs(s.shear_right)
      )))
    };

    return results;

  } catch (error) {
    console.error('Error calling Python backend:', error);

    // Provide helpful error message
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error(
        'Cannot connect to Python backend. Make sure it is running on port 8000.\n' +
        'Start it with: cd backend && python main.py'
      );
    }

    throw error;
  }
}
