import React from 'react';
import { Span, SupportType } from '@/lib/types';

interface BeamVisualizerProps {
  spans: Span[];
}

const SupportIcon = ({ type, x, y }: { type: SupportType; x: number; y: number }) => {
  if (type === 'FIXED') {
    return (
      <g>
        <line x1={x} y1={y - 20} x2={x} y2={y + 20} stroke="hsl(var(--primary))" strokeWidth="4" />
        <line x1={x} y1={y - 20} x2={x - 10} y2={y - 25} stroke="hsl(var(--primary))" strokeWidth="1" />
        <line x1={x} y1={y - 10} x2={x - 10} y2={y - 15} stroke="hsl(var(--primary))" strokeWidth="1" />
        <line x1={x} y1={y} x2={x - 10} y2={y - 5} stroke="hsl(var(--primary))" strokeWidth="1" />
        <line x1={x} y1={y + 10} x2={x - 10} y2={y + 5} stroke="hsl(var(--primary))" strokeWidth="1" />
        <line x1={x} y1={y + 20} x2={x - 10} y2={y + 15} stroke="hsl(var(--primary))" strokeWidth="1" />
      </g>
    );
  }
  if (type === 'PINNED') {
    return (
      <path
        d={`M ${x} ${y} L ${x - 12} ${y + 20} L ${x + 12} ${y + 20} Z`}
        fill="hsl(var(--primary))"
      />
    );
  }
  if (type === 'ROLLER') {
    return (
      <g>
        <path
          d={`M ${x} ${y} L ${x - 12} ${y + 15} L ${x + 12} ${y + 15} Z`}
          fill="hsl(var(--primary))"
        />
        <circle cx={x - 6} cy={y + 20} r="3" fill="hsl(var(--primary))" />
        <circle cx={x + 6} cy={y + 20} r="3" fill="hsl(var(--primary))" />
      </g>
    );
  }
  return null;
};

export const BeamVisualizer: React.FC<BeamVisualizerProps> = ({ spans }) => {
  if (spans.length === 0) return null;

  const totalLength = spans.reduce((sum, s) => sum + s.length, 0);
  const scale = 800 / (totalLength || 1);
  const height = 180;
  const beamY = 100;

  let currentX = 50;

  return (
    <div className="glass-panel p-6 rounded-2xl mb-8 overflow-x-auto">
      <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider mb-4">Structural Schematic</h3>
      <div className="min-w-[800px] flex justify-center">
        <svg width="900" height={height} className="overflow-visible">
          {/* Main Beam Line */}
          <line
            x1={50}
            y1={beamY}
            x2={50 + totalLength * scale}
            y2={beamY}
            stroke="hsl(var(--foreground))"
            strokeWidth="4"
            strokeLinecap="round"
          />

          {/* Spans and Supports */}
          {spans.map((span, i) => {
            const startX = currentX;
            const spanWidth = span.length * scale;
            const endX = startX + spanWidth;
            currentX += spanWidth;

            return (
              <g key={span.id}>
                {/* Span Label */}
                <text x={startX + spanWidth / 2} y={beamY + 45} textAnchor="middle" className="fill-muted-foreground text-xs font-mono">
                  {span.length}m
                </text>

                {/* Left Support */}
                <SupportIcon type={span.leftSupport} x={startX} y={beamY} />

                {/* Right Support (only for the very last span) */}
                {i === spans.length - 1 && (
                  <SupportIcon type={span.rightSupport} x={endX} y={beamY} />
                )}

                {/* Loads Visualization */}
                {span.loadType === 'UDL' && (
                  <g>
                    <rect x={startX} y={beamY - 20} width={spanWidth} height={20} fill="hsl(var(--accent))" opacity="0.2" />
                    <text x={startX + spanWidth / 2} y={beamY - 25} textAnchor="middle" className="fill-accent text-xs font-bold">
                      {span.loadMagnitude} kN/m
                    </text>
                  </g>
                )}
                {span.loadType === 'POINT_CENTER' && (
                  <g>
                    <line x1={startX + spanWidth / 2} y1={beamY - 40} x2={startX + spanWidth / 2} y2={beamY} stroke="hsl(var(--accent))" strokeWidth="2" markerEnd="url(#arrow)" />
                    <text x={startX + spanWidth / 2} y={beamY - 45} textAnchor="middle" className="fill-accent text-xs font-bold">
                      {span.loadMagnitude} kN
                    </text>
                  </g>
                )}
                {span.loadType === 'POINT_ARBITRARY' && span.loadPosition !== undefined && (
                  <g>
                    <line x1={startX + (span.loadPosition / span.length) * spanWidth} y1={beamY - 40} x2={startX + (span.loadPosition / span.length) * spanWidth} y2={beamY} stroke="hsl(var(--accent))" strokeWidth="2" markerEnd="url(#arrow)" />
                    <text x={startX + (span.loadPosition / span.length) * spanWidth} y={beamY - 45} textAnchor="middle" className="fill-accent text-xs font-bold">
                      {span.loadMagnitude} kN
                    </text>
                    <text x={startX + (span.loadPosition / span.length) * spanWidth} y={beamY + 60} textAnchor="middle" className="fill-muted-foreground text-xs">
                      @ {span.loadPosition}m
                    </text>
                  </g>
                )}
                {span.loadType === 'TRIANGULAR' && (
                  <g>
                    <polygon
                      points={`${startX},${beamY - 5} ${endX},${beamY - 25} ${endX},${beamY - 5}`}
                      fill="hsl(var(--accent))"
                      opacity="0.3"
                    />
                    <text x={startX + spanWidth / 2} y={beamY - 30} textAnchor="middle" className="fill-accent text-xs font-bold">
                      {span.loadMagnitude} kN/m (Δ)
                    </text>
                  </g>
                )}
                {span.loadType === 'MOMENT' && (
                  <g>
                    <path
                      d={`M ${startX + 15} ${beamY - 25} A 15 15 0 1 1 ${startX + 15} ${beamY - 24.9}`}
                      stroke="hsl(var(--accent))"
                      strokeWidth="2"
                      fill="none"
                      markerEnd="url(#arrow)"
                    />
                    <text x={startX + 35} y={beamY - 25} textAnchor="start" className="fill-accent text-xs font-bold">
                      {span.loadMagnitude} kN·m
                    </text>
                  </g>
                )}
              </g>
            );
          })}

          <defs>
            <marker id="arrow" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto">
              <path d="M0,0 L0,10 L10,5 z" fill="hsl(var(--accent))" />
            </marker>
          </defs>
        </svg>
      </div>
    </div>
  );
};
