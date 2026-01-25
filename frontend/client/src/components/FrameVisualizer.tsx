import React, { useMemo } from 'react';
import { FrameNode, FrameMember, FramePointLoad } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface FrameVisualizerProps {
    nodes: FrameNode[];
    members: FrameMember[];
    pointLoads: FramePointLoad[];
    displacements?: number[]; // Flattened [u1, v1, r1, u2, ...]
    scale?: number; // Deformation scale factor
}

export function FrameVisualizer({ nodes, members, pointLoads, displacements, scale = 100 }: FrameVisualizerProps) {
    // 1. Calculate Bounding Box for Auto-Scaling
    const { minX, maxX, minY, maxY, width, height } = useMemo(() => {
        if (nodes.length === 0) return { minX: 0, maxX: 10, minY: 0, maxY: 10, width: 10, height: 10 };

        const xs = nodes.map(n => n.x);
        const ys = nodes.map(n => n.y);
        const minX = Math.min(...xs);
        const maxX = Math.max(...xs);
        const minY = Math.min(...ys);
        const maxY = Math.max(...ys);

        // Add padding (10% or at least 1m)
        const paddingX = Math.max((maxX - minX) * 0.1, 1);
        const paddingY = Math.max((maxY - minY) * 0.1, 1);

        return {
            minX: minX - paddingX,
            maxX: maxX + paddingX,
            minY: minY - paddingY,
            maxY: maxY + paddingY,
            width: (maxX - minX) + 2 * paddingX,
            height: (maxY - minY) + 2 * paddingY
        };
    }, [nodes]);

    // Coordinate Transform: World (x, y) -> SVG (px, py)
    // SVG Origin is Top-Left. Structure Y is usually Up. We need to invert Y.
    const svgWidth = 800;
    const svgHeight = 600;

    const toSVG = (x: number, y: number) => {
        const scaleX = svgWidth / width;
        const scaleY = svgHeight / height;
        const finalScale = Math.min(scaleX, scaleY) * 0.8; // Keep aspect ratio, use 80% space

        // Center the structure
        const offsetX = (svgWidth - width * finalScale) / 2;
        const offsetY = (svgHeight - height * finalScale) / 2;

        return {
            sx: (x - minX) * finalScale + offsetX,
            sy: svgHeight - ((y - minY) * finalScale + offsetY) // Invert Y
        };
    };

    // 2. Prepare Deformed Shape (if results exist)
    const deformedNodes = useMemo(() => {
        if (!displacements || displacements.length === 0) return null;

        return nodes.map((n, i) => {
            const idx = i * 3;
            const dx = displacements[idx] || 0;
            const dy = displacements[idx + 1] || 0;
            return {
                ...n,
                x: n.x + dx * scale,
                y: n.y + dy * scale
            };
        });
    }, [nodes, displacements, scale]);

    return (
        <div className="w-full h-full bg-slate-950 rounded-lg overflow-hidden border border-border/20 shadow-inner relative">
            {/* Grid Background */}
            <div className="absolute inset-0 pointer-events-none opacity-20"
                style={{
                    backgroundImage: 'radial-gradient(circle, #333 1px, transparent 1px)',
                    backgroundSize: '20px 20px'
                }}
            />

            <svg width="100%" height="100%" viewBox={`0 0 ${svgWidth} ${svgHeight}`} preserveAspectRatio="xMidYMid meet">

                {/* Members */}
                {members.map(m => {
                    const start = nodes.find(n => n.id === m.startNodeId);
                    const end = nodes.find(n => n.id === m.endNodeId);
                    if (!start || !end) return null;

                    const s = toSVG(start.x, start.y);
                    const e = toSVG(end.x, end.y);

                    return (
                        <g key={m.id}>
                            <line x1={s.sx} y1={s.sy} x2={e.sx} y2={e.sy} stroke="hsl(210, 100%, 60%)" strokeWidth="4" strokeLinecap="round" />
                            {/* ID Label */}
                            <text x={(s.sx + e.sx) / 2} y={(s.sy + e.sy) / 2 - 10} fill="gray" fontSize="12" textAnchor="middle">M{m.id}</text>
                        </g>
                    );
                })}

                {/* Deformed Shape (Dashed) */}
                {deformedNodes && members.map(m => {
                    const startIdx = nodes.findIndex(n => n.id === m.startNodeId);
                    const endIdx = nodes.findIndex(n => n.id === m.endNodeId);
                    if (startIdx === -1 || endIdx === -1) return null;

                    const start = deformedNodes[startIdx];
                    const end = deformedNodes[endIdx];

                    const s = toSVG(start.x, start.y);
                    const e = toSVG(end.x, end.y);

                    return (
                        <line key={`def-${m.id}`} x1={s.sx} y1={s.sy} x2={e.sx} y2={e.sy} stroke="hsl(142, 71%, 45%)" strokeWidth="2" strokeDasharray="5,5" opacity="0.8" />
                    );
                })}

                {/* Supports */}
                {nodes.map(n => {
                    const { sx, sy } = toSVG(n.x, n.y);
                    return (
                        <g key={`supp-${n.id}`} transform={`translate(${sx},${sy})`}>
                            {/* Fixed Support (Rectangle hatch) */}
                            {n.fixX && n.fixY && n.fixR && (
                                <rect x="-10" y="5" width="20" height="10" fill="url(#hatch)" stroke="white" strokeWidth="2" />
                            )}
                            {/* Pinned Support (Triangle) */}
                            {n.fixX && n.fixY && !n.fixR && (
                                <polygon points="0,0 -8,12 8,12" fill="#e2e8f0" stroke="white" strokeWidth="2" />
                            )}
                            {/* Roller Support (Circle) */}
                            {(!n.fixX || !n.fixY) && (n.fixX || n.fixY) && (
                                <circle cx="0" cy="8" r="6" fill="#e2e8f0" stroke="white" strokeWidth="2" />
                            )}
                        </g>
                    );
                })}

                {/* Nodes */}
                {nodes.map(n => {
                    const { sx, sy } = toSVG(n.x, n.y);
                    return (
                        <g key={n.id}>
                            <circle cx={sx} cy={sy} r="6" fill="white" stroke="hsl(210, 100%, 60%)" strokeWidth="2" />
                            <text x={sx} y={sy - 15} fill="white" fontSize="12" textAnchor="middle" fontWeight="bold">{n.id}</text>
                        </g>
                    );
                })}

                {/* Loads */}
                {pointLoads.map(l => {
                    const node = nodes.find(n => n.id === l.targetId);
                    if (!node) return null;
                    const { sx, sy } = toSVG(node.x, node.y);

                    // Scale arrow length by magnitude (logarithmic or clamped)
                    const mag = Math.sqrt(l.magnitudeX ** 2 + l.magnitudeY ** 2);
                    if (mag === 0) return null;
                    const arrowLen = Math.min(Math.max(mag * 5, 30), 80);
                    const angle = Math.atan2(-l.magnitudeY, l.magnitudeX); // SVG Y is down, Force Y is Up? No, Force Y is Up usually. 
                    // If Load Y is -10 (Down), svg angle should be positive?
                    // SVG Y increases Down. 
                    // Force vector (Fx, Fy). 
                    // Arrow start: (sx, sy). Arrow end: (sx + Fx, sy - Fy) (Visual direction)
                    // Actually arrows usually point TO the node.
                    // Let's draw arrow tip at node.

                    const tailX = sx - Math.cos(Math.atan2(-l.magnitudeY, l.magnitudeX)) * arrowLen;
                    const tailY = sy - Math.sin(Math.atan2(-l.magnitudeY, l.magnitudeX)) * arrowLen; // Check sign?

                    // Simpler: Just map vector directions.
                    // If Fy = -10 (Down). We want arrow pointing Down.
                    // Arrow Tip at (sx, sy).
                    // Arrow Tail at (sx - Fx_vis, sy - Fy_vis)
                    // Fy=-10 => Down. SVG Y increases Down. So vector is (0, +10).

                    return (
                        <g key={l.id}>
                            <defs>
                                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                                    <polygon points="0 0, 10 3.5, 0 7" fill="hsl(0, 84%, 60%)" />
                                </marker>
                            </defs>
                            <line
                                x1={sx - l.magnitudeX * 5}
                                y1={sy + l.magnitudeY * 5} // Flip Y for visualization? If Y=-10, we want it above? No.
                                // Let's rely on simple direction check.
                                // If load is (0, -10), it points DOWN. Arrow tip should be at node. Tail should be ABOVE.
                                // Tail Y = sy - 40.

                                x2={sx}
                                y2={sy}
                                stroke="hsl(0, 84%, 60%)"
                                strokeWidth="3"
                                markerEnd="url(#arrowhead)"
                            />
                            <text x={sx - l.magnitudeX * 5} y={sy + l.magnitudeY * 5 - 5} fill="hsl(0, 84%, 60%)" fontSize="12">
                                {mag.toFixed(1)} kN
                            </text>
                        </g>
                    );
                })}

            </svg>
        </div>
    );
}
