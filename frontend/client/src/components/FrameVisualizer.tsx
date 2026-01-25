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
    memberPointLoads?: any[];
    uniformLoads?: any[];
}

export function FrameVisualizer({ nodes, members, pointLoads, memberPointLoads = [], uniformLoads = [], displacements, memberResults, scale = 100, showBMD = false, showSFD = false }: FrameVisualizerProps) {
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

    // Helper to get Member geometric properties (start, end, angle, length)
    const getMemberGeo = (m: FrameMember) => {
        const start = nodes.find(n => n.id === m.startNodeId);
        const end = nodes.find(n => n.id === m.endNodeId);
        if (!start || !end) return null;
        return { start, end };
    };

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
                <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="hsl(0, 84%, 60%)" />
                    </marker>
                     <marker id="arrowhead-blue" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="hsl(217, 91%, 60%)" />
                    </marker>
                     <pattern id="hatch" width="4" height="4" patternTransform="rotate(45 0 0)" patternUnits="userSpaceOnUse">
                        <line x1="0" y1="0" x2="0" y2="4" style={{ stroke: 'white', strokeWidth: 1 }} />
                    </pattern>
                </defs>

                {/* Members */}
                {members.map(m => {
                   const geo = getMemberGeo(m);
                   if (!geo) return null;
                   const { start, end } = geo;
                   const s = toSVG(start.x, start.y);
                   const e = toSVG(end.x, end.y);
                   
                   return (
                        <g key={m.id}>
                            <line x1={s.sx} y1={s.sy} x2={e.sx} y2={e.sy} stroke="hsl(210, 100%, 60%)" strokeWidth="4" strokeLinecap="round" />
                            <text x={(s.sx + e.sx) / 2} y={(s.sy + e.sy) / 2 - 10} fill="gray" fontSize="12" textAnchor="middle">M{m.id}</text>
                        </g>
                    );
                })}

                {/* SFD Logic (Blue) */}
                {showSFD && memberResults && memberResults.map(res => {
                    const member = members.find(m => m.id === res.member_id);
                    if (!member || !res.v_diagram) return null;
                    const geo = getMemberGeo(member); if (!geo) return null;
                    const { start, end } = geo;
                    const s = toSVG(start.x, start.y);
                    const e = toSVG(end.x, end.y);
                    const dx_screen = e.sx - s.sx;
                    const dy_screen = e.sy - s.sy;
                    const len_screen = Math.sqrt(dx_screen ** 2 + dy_screen ** 2);
                    const ux = -dy_screen / len_screen; const uy = dx_screen / len_screen;
                    const vals = res.v_diagram;
                    let pathData = `M ${s.sx} ${s.sy}`;
                    vals.forEach((v: number, i: number) => {
                         const t = i / (vals.length - 1);
                         const px = s.sx + dx_screen * t;
                         const py = s.sy + dy_screen * t;
                         pathData += ` L ${px + ux * v * sfdScale} ${py + uy * v * sfdScale}`;
                    });
                    pathData += ` L ${e.sx} ${e.sy} L ${s.sx} ${s.sy}`;
                    return <path key={`sfd-${res.member_id}`} d={pathData} fill="rgba(56, 189, 248, 0.3)" stroke="#38bdf8" strokeWidth="1" />;
                })}

                {/* BMD Logic (Red) */}
                {showBMD && memberResults && memberResults.map(res => {
                    const member = members.find(m => m.id === res.member_id);
                    if (!member || !res.m_diagram) return null;
                    const geo = getMemberGeo(member); if (!geo) return null;
                    const { start, end } = geo;
                    const s = toSVG(start.x, start.y);
                    const e = toSVG(end.x, end.y);
                    const dx_screen = e.sx - s.sx;
                    const dy_screen = e.sy - s.sy;
                    const len_screen = Math.sqrt(dx_screen ** 2 + dy_screen ** 2);
                    const ux = -dy_screen / len_screen; const uy = dx_screen / len_screen;
                    const vals = res.m_diagram;
                    let pathData = `M ${s.sx} ${s.sy}`;
                    vals.forEach((v: number, i: number) => {
                         const t = i / (vals.length - 1);
                         const px = s.sx + dx_screen * t;
                         const py = s.sy + dy_screen * t;
                         pathData += ` L ${px + ux * v * bmdScale} ${py + uy * v * bmdScale}`;
                    });
                    pathData += ` L ${e.sx} ${e.sy} L ${s.sx} ${s.sy}`;
                    return <path key={`bmd-${res.member_id}`} d={pathData} fill="rgba(255, 99, 71, 0.3)" stroke="red" strokeWidth="1" />;
                })}

                {/* Deformed Shape (Dashed) */}
                {displacements && deformedNodes && members.map(m => {
                    const start = deformedNodes.find(n => n.id === m.startNodeId);
                    const end = deformedNodes.find(n => n.id === m.endNodeId);
                    if (!start || !end) return null;
                    const s = toSVG(start.x, start.y);
                    const e = toSVG(end.x, end.y);
                    return <line key={`def-${m.id}`} x1={s.sx} y1={s.sy} x2={e.sx} y2={e.sy} stroke="hsl(142, 71%, 45%)" strokeWidth="2" strokeDasharray="5,5" opacity="0.8" />;
                })}

                {/* Supports */}
                {nodes.map(n => {
                    const { sx, sy } = toSVG(n.x, n.y);
                     return (
                        <g key={`supp-${n.id}`} transform={`translate(${sx},${sy})`}>
                            {n.fixX && n.fixY && n.fixR && ( <rect x="-10" y="5" width="20" height="10" fill="url(#hatch)" stroke="white" strokeWidth="2" /> )}
                            {n.fixX && n.fixY && !n.fixR && ( <polygon points="0,0 -8,12 8,12" fill="#e2e8f0" stroke="white" strokeWidth="2" /> )}
                            {(!n.fixX || !n.fixY) && (n.fixX || n.fixY) && ( <circle cx="0" cy="8" r="6" fill="#e2e8f0" stroke="white" strokeWidth="2" /> )}
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

                {/* --- Member Point Loads Visualization --- */}
                {memberPointLoads.map(l => {
                    const member = members.find(m => m.id === l.targetId);
                    if (!member) return null;
                    const geo = getMemberGeo(member); if (!geo) return null;
                    const { start, end } = geo;
                    const s = toSVG(start.x, start.y);
                    const e = toSVG(end.x, end.y);
                    
                    // Geometry
                    const dx = end.x - start.x;
                    const dy = end.y - start.y;
                    const len = Math.sqrt(dx*dx + dy*dy);
                    if (len === 0) return null;
                    
                    // Ratio t for position
                    const t = Math.max(0, Math.min(1, l.position / len));
                    
                    // Screen Coords
                    const dx_screen = e.sx - s.sx;
                    const dy_screen = e.sy - s.sy;
                    
                    // Load Point on Screen
                    const lx = s.sx + dx_screen * t;
                    const ly = s.sy + dy_screen * t;

                    // Direction Vectors
                    // Screen Axis: X right, Y down.
                    // Unit Vector along member in Screen Space
                    const len_screen = Math.sqrt(dx_screen*dx_screen + dy_screen*dy_screen);
                    const u_axial_x = dx_screen / len_screen;
                    const u_axial_y = dy_screen / len_screen;
                    
                    // Unit Transverse (Perp). Rot -90 deg?
                    // Structure: X right, Y up. Member Angle.
                    // Screen: Y inverted.
                    // Let's just use component logic.
                    // Local X load = magnitudeX. Local Y load = magnitudeY.
                    
                    // We need a visual vector. 
                    // Visual Scale
                    const arrowLen = 40; 
                    
                    // Local Y (Perp) vector in screen space?
                    // Vector (-uy, ux) is usually perp.
                    const u_perp_x = -u_axial_y;
                    const u_perp_y = u_axial_x;
                    
                    // Composite Load Vector in Screen Basis
                    // l.magnitudeX is Axial. l.magnitudeY is Perp.
                    // Note: magnitudeY > 0 usually means "Up" in local Y.
                    // If we want to show the arrow pointing in direction of force.
                    
                    // We need to verify orientation. "Standard" structural:
                    // Member A->B. Local x A->B. Local y Rotated 90 deg CCW.
                    // If Member is Horizontal (left to right). x=(1,0). y=(0,1) (Up).
                    // Screen: x=(1,0). y=(0,-1) (Up is -Y).
                    
                    // Let's rely on simple perp logic:
                    // If load is -20 (Right on Vert Col). It points Right.
                    // Vert Col (Up). Local y is Left. -20 is Right.
                    // So we draw arrow pointing Right.
                    
                    // Simplified:
                    // Just draw arrow from (lx, ly) in direction of load?
                    // No, usually draw arrow pointing TO (lx, ly).
                    // Calculate Tail position.
                    
                    // Force Vector in Global Screen Coords?
                    // We need to know Global Angle of Member.
                    // angle = atan2(dy, dx).
                    // Global Load Vector:
                    // F_glob_x = Px * cos - Py * sin
                    // F_glob_y = Px * sin + Py * cos 
                    // (Standard 2D Rotation R * F_loc)
                    
                    const angle = Math.atan2(dy, dx); 
                    const Fgx = l.magnitudeX * Math.cos(angle) - l.magnitudeY * Math.sin(angle);
                    const Fgy = l.magnitudeX * Math.sin(angle) + l.magnitudeY * Math.cos(angle);
                    
                    // Screen Vector (Y inverted for screen y)
                    // F_screen_x = Fgx
                    // F_screen_y = -Fgy (Since Up is -Y)
                    const Fsx = Fgx;
                    const Fsy = -Fgy;
                    
                    const mag = Math.sqrt(Fsx*Fsx + Fsy*Fsy);
                    if (mag < 0.001) return null;
                    
                    // Unit direction
                    const ux_load = Fsx / mag;
                    const uy_load = Fsy / mag;
                    
                    // Tail position (Arrow points TO lx, ly)
                    const tailX = lx - ux_load * arrowLen;
                    const tailY = ly - uy_load * arrowLen;
                    
                     return (
                         <g key={l.id}>
                             <line x1={tailX} y1={tailY} x2={lx} y2={ly} stroke="hsl(262, 83%, 58%)" strokeWidth="2" markerEnd="url(#arrowhead)" />
                             <text x={tailX} y={tailY - 5} fill="hsl(262, 83%, 58%)" fontSize="10">{Math.abs(l.magnitudeX + l.magnitudeY).toFixed(0)}</text>
                         </g>
                     );
                })}

                {/* --- Uniform Loads Visualization --- */}
                {uniformLoads.map(l => {
                     const member = members.find(m => m.id === l.memberId);
                    if (!member) return null;
                    const geo = getMemberGeo(member); if (!geo) return null;
                    const { start, end } = geo;
                    const s = toSVG(start.x, start.y);
                    const e = toSVG(end.x, end.y);
                    
                    // Draw a series of arrows along the member
                    // Only handling Wy for now (Transverse UDL)
                    // magnitudeY.
                    if (Math.abs(l.magnitudeY) < 0.01) return null;
                    
                    const dx_screen = e.sx - s.sx;
                    const dy_screen = e.sy - s.sy;
                    const len_screen = Math.sqrt(dx_screen**2 + dy_screen**2);
                    
                     // Perpendicular Vector (Screen)
                    const u_axial_x = dx_screen / len_screen;
                    const u_axial_y = dy_screen / len_screen;
                    const u_perp_x = -u_axial_y;
                    const u_perp_y = u_axial_x;
                    
                    // If Wy < 0 (Down/Right), arrow points against normal?
                    // Standard: Wy < 0 means "Down" relative to member (Gravity).
                    // If Horizontal Member: Down is +ScreenY.
                    // u_perp for horiz (1,0) is (0,1). Pointing Down.
                    // So if Wy < 0, we want arrows pointing Down involved?
                    // Actually usually Wy < 0 means -Y local.
                    // Let's assume Wy < 0 points in direction of u_perp (if u_perp is "Local Y").
                    // Wait, u_perp (-u_axial_y, u_axial_x) corresponds to +90 deg rotation (CCW). That is Local +Y.
                    // So if Wy is negative, it points opposite to u_perp.
                    
                    const sign = Math.sign(l.magnitudeY);
                    const arrowDirX = sign * u_perp_x; 
                    const arrowDirY = sign * u_perp_y;
                    
                    // Wait. If Wy = -15. sign = -1. ArrowDir = -u_perp. (Opposite to Local Y).
                    // For Horiz Member: u_perp is Up (screen -Y). -u_perp is Down (screen +Y).
                    // Correct. Arrows point Down.
                    
                    const arrowLen = 20;
                    const spacing = 40;
                    const count = Math.floor(len_screen / spacing);
                    
                    const arrows = [];
                    for(let i=0; i<=count; i++) {
                        const t = i/count;
                        const bx = s.sx + dx_screen * t;
                        const by = s.sy + dy_screen * t;
                        
                        // Arrow Tip at member? Or Tail at member?
                        // Usually Tip at member for pressure.
                        const tailX = bx - arrowDirX * arrowLen;
                        const tailY = by - arrowDirY * arrowLen; // Inverted Y logic already handled by u_perp?
                        // Screen Y is Down.
                        // u_perp for Vert Col (Up). u_axial=(0,-1). u_perp=(1,0). (Right).
                        // If Wy < 0 (Left Load). sign=-1. ArrowDir=(-1,0). (Left).
                         // Tip at bx,by. Tail at bx+20, by. Arrow points Left.
                        // Correct.
                        
                        arrows.push(
                             <line key={i} x1={tailX} y1={tailY} x2={bx} y2={by} stroke="hsl(217, 91%, 60%)" strokeWidth="1" markerEnd="url(#arrowhead-blue)" />
                        );
                    }
                    
                    // Draw connecting bar at tails?
                    const tStart = 0; const tEnd = 1;
                    const bXs = s.sx + dx_screen*tStart - arrowDirX * arrowLen;
                    const bYs = s.sy + dy_screen*tStart - arrowDirY * arrowLen;
                    const bXe = s.sx + dx_screen*tEnd - arrowDirX * arrowLen;
                    const bYe = s.sy + dy_screen*tEnd - arrowDirY * arrowLen;
                    
                    return (
                        <g key={l.id}>
                            {arrows}
                            <line x1={bXs} y1={bYs} x2={bXe} y2={bYe} stroke="hsl(217, 91%, 60%)" strokeWidth="1" />
                        </g>
                    );
                })}

                {/* Point Loads (Node Loads) */}
                {pointLoads.map(l => {
                     const node = nodes.find(n => n.id === l.targetId);
                    if (!node) return null;
                    const { sx, sy } = toSVG(node.x, node.y);
                    const mag = Math.sqrt(l.magnitudeX ** 2 + l.magnitudeY ** 2);
                    if (mag === 0) return null;
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
