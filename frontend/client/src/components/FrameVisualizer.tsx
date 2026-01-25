import React, { useMemo } from 'react';
import { FrameNode, FrameMember, FramePointLoad } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface FrameVisualizerProps {
    nodes: FrameNode[];
    members: FrameMember[];
    pointLoads: FramePointLoad[];
    displacements?: number[]; // Flattened [u1, v1, r1, u2, ...]
    memberResults?: any[]; // Results containing diagrams
    scale?: number; // Deformation scale factor
    showBMD?: boolean;
    showSFD?: boolean;
}

export function FrameVisualizer({ nodes, members, pointLoads, displacements, memberResults, scale = 100, showBMD = false, showSFD = false }: FrameVisualizerProps) {
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

    const maxMomentVal = useMemo(() => {
        if (!memberResults) return 1;
        let max = 0;
        memberResults.forEach(r => {
            if (r.m_diagram) max = Math.max(max, ...r.m_diagram.map(Math.abs));
        });
        return max || 1;
    }, [memberResults]);

    const maxShearVal = useMemo(() => {
        if (!memberResults) return 1;
        let max = 0;
        memberResults.forEach(r => {
            if (r.v_diagram) max = Math.max(max, ...r.v_diagram.map(Math.abs));
        });
        return max || 1;
    }, [memberResults]);

    // Dynamic Scale: Target ~50px max height on screen
    const bmdScale = 50 / maxMomentVal;
    const sfdScale = 50 / maxShearVal;

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

                {/* SFD Logic (Blue) */}
                {showSFD && memberResults && memberResults.map(res => {
                    const member = members.find(m => m.id === res.member_id);
                    if (!member || !res.v_diagram) return null;

                    const startIdx = nodes.findIndex(n => n.id === member.startNodeId);
                    const endIdx = nodes.findIndex(n => n.id === member.endNodeId);
                    if (startIdx === -1 || endIdx === -1) return null;

                    const start = nodes[startIdx];
                    const end = nodes[endIdx];
                    const s = toSVG(start.x, start.y);
                    const e = toSVG(end.x, end.y);

                    const dx_screen = e.sx - s.sx;
                    const dy_screen = e.sy - s.sy;
                    const len_screen = Math.sqrt(dx_screen ** 2 + dy_screen ** 2);
                    const ux = -dy_screen / len_screen;
                    const uy = dx_screen / len_screen;

                    const vals = res.v_diagram;
                    let pathData = `M ${s.sx} ${s.sy}`;

                    vals.forEach((v: number, i: number) => {
                        const t = i / (vals.length - 1);
                        const px = s.sx + dx_screen * t;
                        const py = s.sy + dy_screen * t;
                        const offX = px + ux * v * sfdScale;
                        const offY = py + uy * v * sfdScale;
                        pathData += ` L ${offX} ${offY}`;
                    });

                    pathData += ` L ${e.sx} ${e.sy} L ${s.sx} ${s.sy}`;

                    return (
                        <path key={`sfd-${res.member_id}`} d={pathData} fill="rgba(56, 189, 248, 0.3)" stroke="#38bdf8" strokeWidth="1" />
                    );
                })}

                {/* BMD Logic (Red) */}
                {showBMD && memberResults && memberResults.map(res => {
                    const member = members.find(m => m.id === res.member_id);
                    if (!member || !res.m_diagram) return null;

                    const startIdx = nodes.findIndex(n => n.id === member.startNodeId);
                    const endIdx = nodes.findIndex(n => n.id === member.endNodeId);
                    if (startIdx === -1 || endIdx === -1) return null;

                    const start = nodes[startIdx];
                    const end = nodes[endIdx];
                    const s = toSVG(start.x, start.y);
                    const e = toSVG(end.x, end.y);

                    const dx_screen = e.sx - s.sx;
                    const dy_screen = e.sy - s.sy;
                    const len_screen = Math.sqrt(dx_screen ** 2 + dy_screen ** 2);
                    const ux = -dy_screen / len_screen;
                    const uy = dx_screen / len_screen;

                    const vals = res.m_diagram;
                    let pathData = `M ${s.sx} ${s.sy}`;

                    vals.forEach((v: number, i: number) => {
                        const t = i / (vals.length - 1);
                        const px = s.sx + dx_screen * t;
                        const py = s.sy + dy_screen * t;
                        // For Frames, usually plot moments on "Tension Side" or consistent local axis.
                        // We use local axis convention.
                        const offX = px + ux * v * bmdScale;
                        const offY = py + uy * v * bmdScale;
                        pathData += ` L ${offX} ${offY}`;
                    });

                    pathData += ` L ${e.sx} ${e.sy} L ${s.sx} ${s.sy}`;

                    return (
                        <path key={`bmd-${res.member_id}`} d={pathData} fill="rgba(255, 99, 71, 0.3)" stroke="red" strokeWidth="1" />
                    );
                })}

                {/* Deformed Shape (Dashed) */}
                {displacements && deformedNodes && members.map(m => {
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
                            <circle cx={sx} cy={sy} r="4" fill="white" stroke="hsl(210, 100%, 60%)" strokeWidth="2" />
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

                    // Simple arrow logic
                    return (
                        <g key={l.id}>
                            <line x1={sx - l.magnitudeX * 2} y1={sy + l.magnitudeY * 2} x2={sx} y2={sy} stroke="hsl(0, 84%, 60%)" strokeWidth="3" markerEnd="url(#arrowhead)" />
                        </g>
                    );
                })}

            </svg>
        </div>
    );
}
