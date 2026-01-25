import React, { useState } from 'react';
import { FrameNode, FrameMember, FramePointLoad } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Trash2, Grid, Play, ArrowDown } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { FrameVisualizer } from '@/components/FrameVisualizer';

export function FrameAnalysis() {
    const [nodes, setNodes] = useState<FrameNode[]>([
        { id: '1', x: 0, y: 0, fixX: true, fixY: true, fixR: true },
        { id: '2', x: 0, y: 3, fixX: false, fixY: false, fixR: false },
    ]);
    const [members, setMembers] = useState<FrameMember[]>([
        { id: '1', startNodeId: '1', endNodeId: '2', elasticModulus: 200, momentOfInertia: 500, crossSectionArea: 0.01 }
    ]);
    const [pointLoads, setPointLoads] = useState<FramePointLoad[]>([]);
    const [result, setResult] = useState<any>(null);

    const { toast } = useToast();

    // --- Nodes Logic ---
    const handleAddNode = () => {
        const lastNode = nodes[nodes.length - 1];
        // Auto-increment ID
        const nextId = (Math.max(...nodes.map(n => parseInt(n.id) || 0), 0) + 1).toString();

        const newNode: FrameNode = {
            id: nextId,
            x: lastNode ? lastNode.x + 3 : 0,
            y: lastNode ? lastNode.y : 0,
            fixX: false,
            fixY: false,
            fixR: false
        };
        setNodes([...nodes, newNode]);
    };

    const updateNode = (id: string, field: keyof FrameNode, value: any) => {
        setNodes(nodes.map(n => n.id === id ? { ...n, [field]: value } : n));
    };

    const removeNode = (id: string) => {
        if (nodes.length <= 1) {
            toast({ title: "Cannot remove node", description: "At least one node is required.", variant: "destructive" });
            return;
        }
        if (members.some(m => m.startNodeId === id || m.endNodeId === id)) {
            toast({ title: "Cannot remove node", description: `Node is connected to a member. Remove member first.`, variant: "destructive" });
            return;
        }
        setNodes(nodes.filter(n => n.id !== id));
        setPointLoads(pointLoads.filter(l => l.targetId !== id));
    };

    // --- Members Logic ---
    const handleAddMember = () => {
        const startNode = nodes.length >= 2 ? nodes[nodes.length - 2].id : nodes[0]?.id || '';
        const endNode = nodes.length >= 1 ? nodes[nodes.length - 1].id : nodes[0]?.id || '';

        // Auto-increment Member ID
        const nextId = (Math.max(...members.map(m => parseInt(m.id) || 0), 0) + 1).toString();

        const newMember: FrameMember = {
            id: nextId,
            startNodeId: startNode,
            endNodeId: endNode,
            elasticModulus: 200,
            momentOfInertia: 500,
            crossSectionArea: 0.01
        };
        setMembers([...members, newMember]);
    };

    const updateMember = (id: string, field: keyof FrameMember, value: any) => {
        setMembers(members.map(m => m.id === id ? { ...m, [field]: value } : m));
    };

    const removeMember = (id: string) => {
        setMembers(members.filter(m => m.id !== id));
    };

    // --- Loads Logic ---
    const handleAddLoad = () => {
        const newLoad: FramePointLoad = {
            id: crypto.randomUUID().slice(0, 8),
            type: 'NODE_LOAD',
            targetId: nodes[nodes.length - 1]?.id || '',
            magnitudeX: 0,
            magnitudeY: -10,
            moment: 0
        };
        setPointLoads([...pointLoads, newLoad]);
    };

    const updateLoad = (id: string, field: keyof FramePointLoad, value: any) => {
        setPointLoads(pointLoads.map(l => l.id === id ? { ...l, [field]: value } : l));
    };

    const removeLoad = (id: string) => {
        setPointLoads(pointLoads.filter(l => l.id !== id));
    };

    // --- Calculation ---
    const handleCalculate = async () => {
        try {
            const payload = {
                nodes,
                members,
                pointLoads,
                uniformLoads: []
            };

            const response = await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/calculate-frame`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.errorMessage || "Calculation failed");
            }

            setResult(data);
            toast({
                title: "Analysis Complete",
                description: "Frame analysis solved successfully.",
            });

        } catch (error) {
            console.error('Calculation error:', error);
            toast({
                title: "Calculation Error",
                description: error instanceof Error ? error.message : "Failed to solve frame.",
                variant: "destructive"
            });
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500 pb-20">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">2D Frame Analysis</h2>
                    <p className="text-muted-foreground">Define geometry and loads</p>
                </div>
                <Button onClick={handleCalculate} size="lg" className="shadow-lg bg-primary hover:bg-primary/90">
                    <Play className="mr-2 h-4 w-4" /> Analyze Frame
                </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Input Tables */}
                <div className="lg:col-span-1 space-y-8">

                    <section className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <Grid className="h-4 w-4 text-primary" /> Nodes
                            </h3>
                            <Button onClick={handleAddNode} size="sm" variant="outline" className="h-8">
                                <Plus className="h-3 w-3 mr-1" /> Add
                            </Button>
                        </div>
                        <div className="rounded-md border border-border/50 overflow-hidden bg-card/50 backdrop-blur-sm">
                            <Table>
                                <TableHeader>
                                    <TableRow className="hover:bg-transparent border-border/50">
                                        <TableHead className="w-[50px]">ID</TableHead>
                                        <TableHead>X <span className="text-xs text-muted-foreground">(m)</span></TableHead>
                                        <TableHead>Y <span className="text-xs text-muted-foreground">(m)</span></TableHead>
                                        <TableHead className="text-center" title="Fix X">Rx</TableHead>
                                        <TableHead className="text-center" title="Fix Y">Ry</TableHead>
                                        <TableHead className="text-center" title="Fix Rotation">Rr</TableHead>
                                        <TableHead className="w-[40px]"></TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {nodes.map((node) => (
                                        <TableRow key={node.id} className="hover:bg-muted/10 border-border/50">
                                            <TableCell className="font-mono text-xs text-muted-foreground font-bold">{node.id}</TableCell>
                                            <TableCell><Input type="number" value={node.x} onChange={(e) => updateNode(node.id, 'x', parseFloat(e.target.value))} className="h-7 w-14 px-1 text-right" /></TableCell>
                                            <TableCell><Input type="number" value={node.y} onChange={(e) => updateNode(node.id, 'y', parseFloat(e.target.value))} className="h-7 w-14 px-1 text-right" /></TableCell>
                                            <TableCell className="text-center"><Checkbox checked={node.fixX} onCheckedChange={(c) => updateNode(node.id, 'fixX', c === true)} /></TableCell>
                                            <TableCell className="text-center"><Checkbox checked={node.fixY} onCheckedChange={(c) => updateNode(node.id, 'fixY', c === true)} /></TableCell>
                                            <TableCell className="text-center"><Checkbox checked={node.fixR} onCheckedChange={(c) => updateNode(node.id, 'fixR', c === true)} /></TableCell>
                                            <TableCell><Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => removeNode(node.id)}><Trash2 className="h-3 w-3" /></Button></TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </section>

                    <section className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <Grid className="h-4 w-4 text-primary" /> Members
                            </h3>
                            <Button onClick={handleAddMember} size="sm" variant="outline" className="h-8">
                                <Plus className="h-3 w-3 mr-1" /> Add
                            </Button>
                        </div>
                        <div className="rounded-md border border-border/50 overflow-hidden bg-card/50 backdrop-blur-sm">
                            <Table>
                                <TableHeader>
                                    <TableRow className="hover:bg-transparent border-border/50">
                                        <TableHead className="w-[50px]">ID</TableHead>
                                        <TableHead className="w-[70px]">Start</TableHead>
                                        <TableHead className="w-[70px]">End</TableHead>
                                        <TableHead>E <span className="text-xs text-muted-foreground">(GPa)</span></TableHead>
                                        <TableHead>I <span className="text-xs text-muted-foreground">(10⁶)</span></TableHead>
                                        <TableHead>A <span className="text-xs text-muted-foreground">(m²)</span></TableHead>
                                        <TableHead className="w-[40px]"></TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {members.map((member) => (
                                        <TableRow key={member.id} className="hover:bg-muted/10 border-border/50">
                                            <TableCell className="font-mono text-xs text-muted-foreground font-bold">M{member.id}</TableCell>
                                            <TableCell>
                                                <Select value={member.startNodeId} onValueChange={(val) => updateMember(member.id, 'startNodeId', val)}>
                                                    <SelectTrigger className="h-7 w-[65px] px-1"><SelectValue placeholder="Node" /></SelectTrigger>
                                                    <SelectContent>{nodes.map(n => <SelectItem key={n.id} value={n.id}>{n.id.slice(0, 4)}</SelectItem>)}</SelectContent>
                                                </Select>
                                            </TableCell>
                                            <TableCell>
                                                <Select value={member.endNodeId} onValueChange={(val) => updateMember(member.id, 'endNodeId', val)}>
                                                    <SelectTrigger className="h-7 w-[65px] px-1"><SelectValue placeholder="Node" /></SelectTrigger>
                                                    <SelectContent>{nodes.map(n => <SelectItem key={n.id} value={n.id}>{n.id.slice(0, 4)}</SelectItem>)}</SelectContent>
                                                </Select>
                                            </TableCell>
                                            <TableCell><Input type="number" value={member.elasticModulus} onChange={(e) => updateMember(member.id, 'elasticModulus', parseFloat(e.target.value))} className="h-7 w-12 px-1 text-right" /></TableCell>
                                            <TableCell><Input type="number" value={member.momentOfInertia} onChange={(e) => updateMember(member.id, 'momentOfInertia', parseFloat(e.target.value))} className="h-7 w-12 px-1 text-right" /></TableCell>
                                            <TableCell><Input type="number" value={member.crossSectionArea} onChange={(e) => updateMember(member.id, 'crossSectionArea', parseFloat(e.target.value))} className="h-7 w-12 px-1 text-right" /></TableCell>
                                            <TableCell><Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => removeMember(member.id)}><Trash2 className="h-3 w-3" /></Button></TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </section>

                    <section className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <ArrowDown className="h-4 w-4 text-primary" /> Nodal Loads
                            </h3>
                            <Button onClick={handleAddLoad} size="sm" variant="outline" className="h-8">
                                <Plus className="h-3 w-3 mr-1" /> Add
                            </Button>
                        </div>
                        <div className="rounded-md border border-border/50 overflow-hidden bg-card/50 backdrop-blur-sm">
                            <Table>
                                <TableHeader>
                                    <TableRow className="hover:bg-transparent border-border/50">
                                        <TableHead className="w-[80px]">Node</TableHead>
                                        <TableHead>Fx <span className="text-xs text-muted-foreground">(kN)</span></TableHead>
                                        <TableHead>Fy <span className="text-xs text-muted-foreground">(kN)</span></TableHead>
                                        <TableHead>M <span className="text-xs text-muted-foreground">(kNm)</span></TableHead>
                                        <TableHead className="w-[40px]"></TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {pointLoads.map((load) => (
                                        <TableRow key={load.id} className="hover:bg-muted/10 border-border/50">
                                            <TableCell>
                                                <Select value={load.targetId} onValueChange={(val) => updateLoad(load.id, 'targetId', val)}>
                                                    <SelectTrigger className="h-7 w-[70px] px-1"><SelectValue placeholder="Node" /></SelectTrigger>
                                                    <SelectContent>{nodes.map(n => <SelectItem key={n.id} value={n.id}>{n.id}</SelectItem>)}</SelectContent>
                                                </Select>
                                            </TableCell>
                                            <TableCell><Input type="number" value={load.magnitudeX} onChange={(e) => updateLoad(load.id, 'magnitudeX', parseFloat(e.target.value))} className="h-7 w-16 px-1 text-right" /></TableCell>
                                            <TableCell><Input type="number" value={load.magnitudeY} onChange={(e) => updateLoad(load.id, 'magnitudeY', parseFloat(e.target.value))} className="h-7 w-16 px-1 text-right" /></TableCell>
                                            <TableCell><Input type="number" value={load.moment} onChange={(e) => updateLoad(load.id, 'moment', parseFloat(e.target.value))} className="h-7 w-16 px-1 text-right" /></TableCell>
                                            <TableCell><Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => removeLoad(load.id)}><Trash2 className="h-3 w-3" /></Button></TableCell>
                                        </TableRow>
                                    ))}
                                    {pointLoads.length === 0 && (
                                        <TableRow>
                                            <TableCell colSpan={5} className="text-center text-muted-foreground h-12">No loads defined</TableCell>
                                        </TableRow>
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </section>

                </div>

                {/* Right Column: Visualization & Results */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Visualizer */}
                    <Card className="h-[500px] glass-card border-primary/20 flex flex-col overflow-hidden">
                        <CardHeader className="py-4 border-b border-border/50 bg-slate-950/50">
                            <CardTitle className="text-lg">Structure Visualization</CardTitle>
                        </CardHeader>
                        <div className="flex-1 relative bg-slate-950">
                            <FrameVisualizer
                                nodes={nodes}
                                members={members}
                                pointLoads={pointLoads}
                                displacements={result?.displacements}
                                scale={100} // Default deformation scale
                            />
                        </div>
                    </Card>

                    {/* Results */}
                    {result && (
                        <Card className="glass-card border-primary/20 animate-in slide-in-from-bottom-10 duration-500">
                            <CardHeader>
                                <CardTitle>Analysis Results</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div>
                                    <h4 className="text-sm font-semibold mb-2 text-primary">Nodal Displacements</h4>
                                    <div className="rounded-md border border-border/50 overflow-hidden">
                                        <Table>
                                            <TableHeader>
                                                <TableRow className="hover:bg-transparent bg-muted/20"><TableHead>Node</TableHead><TableHead className="text-right">Dx (mm)</TableHead><TableHead className="text-right">Dy (mm)</TableHead><TableHead className="text-right">Rotation (rad)</TableHead></TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {nodes.map((node, idx) => {
                                                    const baseIdx = idx * 3;
                                                    const dx = result.displacements[baseIdx];
                                                    const dy = result.displacements[baseIdx + 1];
                                                    const rot = result.displacements[baseIdx + 2];
                                                    return (
                                                        <TableRow key={node.id} className="hover:bg-transparent">
                                                            <TableCell className="font-mono text-xs">{node.id}</TableCell>
                                                            <TableCell className={`text-right ${Math.abs(dx) > 1e-6 ? 'text-white' : 'text-muted-foreground'}`}>{(dx * 1000).toFixed(4)}</TableCell>
                                                            <TableCell className={`text-right ${Math.abs(dy) > 1e-6 ? 'text-white' : 'text-muted-foreground'}`}>{(dy * 1000).toFixed(4)}</TableCell>
                                                            <TableCell className={`text-right ${Math.abs(rot) > 1e-6 ? 'text-white' : 'text-muted-foreground'}`}>{rot.toExponential(4)}</TableCell>
                                                        </TableRow>
                                                    );
                                                })}
                                            </TableBody>
                                        </Table>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="text-sm font-semibold mb-2 text-primary">Support Reactions</h4>
                                    <div className="rounded-md border border-border/50 overflow-hidden">
                                        <Table>
                                            <TableHeader>
                                                <TableRow className="hover:bg-transparent bg-muted/20"><TableHead>Node</TableHead><TableHead className="text-right">Rx (kN)</TableHead><TableHead className="text-right">Ry (kN)</TableHead><TableHead className="text-right">Moment (kNm)</TableHead></TableRow>
                                            </TableHeader>
                                            <TableBody>
                                                {nodes.map((node, idx) => {
                                                    const baseIdx = idx * 3;
                                                    const rx = result.reactions[baseIdx];
                                                    const ry = result.reactions[baseIdx + 1];
                                                    const rm = result.reactions[baseIdx + 2];

                                                    if (!node.fixX && !node.fixY && !node.fixR) return null;

                                                    return (
                                                        <TableRow key={node.id} className="hover:bg-transparent">
                                                            <TableCell className="font-mono text-xs">{node.id}</TableCell>
                                                            <TableCell className="text-right text-accent">{node.fixX ? rx.toFixed(3) : '-'}</TableCell>
                                                            <TableCell className="text-right text-accent">{node.fixY ? ry.toFixed(3) : '-'}</TableCell>
                                                            <TableCell className="text-right text-accent">{node.fixR ? rm.toFixed(3) : '-'}</TableCell>
                                                        </TableRow>
                                                    );
                                                })}
                                            </TableBody>
                                        </Table>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    );
}
