import React, { useState } from 'react';
import { FrameNode, FrameMember } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Plus, Trash2, Grid, Play } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export function FrameAnalysis() {
    const [nodes, setNodes] = useState<FrameNode[]>([
        { id: '1', x: 0, y: 0, fixX: true, fixY: true, fixR: true }, // Fixed support at origin
        { id: '2', x: 0, y: 3, fixX: false, fixY: false, fixR: false }, // Node at 3m height
    ]);
    const [members, setMembers] = useState<FrameMember[]>([
        { id: '1', startNodeId: '1', endNodeId: '2', elasticModulus: 200, momentOfInertia: 500, crossSectionArea: 0.01 }
    ]);
    const [result, setResult] = useState<any>(null);

    const { toast } = useToast();

    const handleAddNode = () => {
        const lastNode = nodes[nodes.length - 1];
        const newNode: FrameNode = {
            id: crypto.randomUUID().slice(0, 8),
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
        // Check if used in members
        if (members.some(m => m.startNodeId === id || m.endNodeId === id)) {
            toast({ title: "Cannot remove node", description: `Node is connected to a member. Remove member first.`, variant: "destructive" });
            return;
        }
        setNodes(nodes.filter(n => n.id !== id));
    };

    const handleAddMember = () => {
        const startNode = nodes.length >= 2 ? nodes[nodes.length - 2].id : nodes[0]?.id || '';
        const endNode = nodes.length >= 1 ? nodes[nodes.length - 1].id : nodes[0]?.id || '';

        const newMember: FrameMember = {
            id: crypto.randomUUID().slice(0, 8),
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

    const handleCalculate = async () => {
        try {
            const payload = {
                nodes: nodes,
                members: members,
                pointLoads: [], // TODO: Add UI for loads
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
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">2D Frame Analysis</h2>
                    <p className="text-muted-foreground">Define nodes and members for matrix analysis</p>
                </div>
                <Button onClick={handleCalculate} size="lg" className="shadow-lg bg-primary hover:bg-primary/90">
                    <Play className="mr-2 h-4 w-4" /> Analyze Frame
                </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Left Column: Input Tables */}
                <div className="lg:col-span-1 space-y-8">

                    {/* Node Definition */}
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
                                        <TableHead>X (m)</TableHead>
                                        <TableHead>Y (m)</TableHead>
                                        <TableHead className="text-center" title="Fix X">Rx</TableHead>
                                        <TableHead className="text-center" title="Fix Y">Ry</TableHead>
                                        <TableHead className="text-center" title="Fix Rotation">Rr</TableHead>
                                        <TableHead className="w-[40px]"></TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {nodes.map((node) => (
                                        <TableRow key={node.id} className="hover:bg-muted/10 border-border/50">
                                            <TableCell className="font-mono text-xs text-muted-foreground">{node.id.slice(0, 4)}</TableCell>
                                            <TableCell>
                                                <Input
                                                    type="number"
                                                    value={node.x}
                                                    onChange={(e) => updateNode(node.id, 'x', parseFloat(e.target.value))}
                                                    className="h-7 w-16 px-1 text-right"
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <Input
                                                    type="number"
                                                    value={node.y}
                                                    onChange={(e) => updateNode(node.id, 'y', parseFloat(e.target.value))}
                                                    className="h-7 w-16 px-1 text-right"
                                                />
                                            </TableCell>
                                            <TableCell className="text-center">
                                                <Checkbox checked={node.fixX} onCheckedChange={(c) => updateNode(node.id, 'fixX', c === true)} />
                                            </TableCell>
                                            <TableCell className="text-center">
                                                <Checkbox checked={node.fixY} onCheckedChange={(c) => updateNode(node.id, 'fixY', c === true)} />
                                            </TableCell>
                                            <TableCell className="text-center">
                                                <Checkbox checked={node.fixR} onCheckedChange={(c) => updateNode(node.id, 'fixR', c === true)} />
                                            </TableCell>
                                            <TableCell>
                                                <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => removeNode(node.id)}>
                                                    <Trash2 className="h-3 w-3" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </section>

                    {/* Member Definition */}
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
                                            <TableCell className="font-mono text-xs text-muted-foreground">{member.id.slice(0, 4)}</TableCell>
                                            <TableCell>
                                                <Select
                                                    value={member.startNodeId}
                                                    onValueChange={(val) => updateMember(member.id, 'startNodeId', val)}
                                                >
                                                    <SelectTrigger className="h-7 w-[65px] px-1">
                                                        <SelectValue placeholder="Node" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        {nodes.map(n => (
                                                            <SelectItem key={n.id} value={n.id}>{n.id.slice(0, 4)}</SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </TableCell>
                                            <TableCell>
                                                <Select
                                                    value={member.endNodeId}
                                                    onValueChange={(val) => updateMember(member.id, 'endNodeId', val)}
                                                >
                                                    <SelectTrigger className="h-7 w-[65px] px-1">
                                                        <SelectValue placeholder="Node" />
                                                    </SelectTrigger>
                                                    <SelectContent>
                                                        {nodes.map(n => (
                                                            <SelectItem key={n.id} value={n.id}>{n.id.slice(0, 4)}</SelectItem>
                                                        ))}
                                                    </SelectContent>
                                                </Select>
                                            </TableCell>
                                            <TableCell>
                                                <Input
                                                    type="number"
                                                    value={member.elasticModulus}
                                                    onChange={(e) => updateMember(member.id, 'elasticModulus', parseFloat(e.target.value))}
                                                    className="h-7 w-12 px-1 text-right"
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <Input
                                                    type="number"
                                                    value={member.momentOfInertia}
                                                    onChange={(e) => updateMember(member.id, 'momentOfInertia', parseFloat(e.target.value))}
                                                    className="h-7 w-12 px-1 text-right"
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <Input
                                                    type="number"
                                                    value={member.crossSectionArea}
                                                    onChange={(e) => updateMember(member.id, 'crossSectionArea', parseFloat(e.target.value))}
                                                    className="h-7 w-12 px-1 text-right"
                                                />
                                            </TableCell>
                                            <TableCell>
                                                <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-destructive" onClick={() => removeMember(member.id)}>
                                                    <Trash2 className="h-3 w-3" />
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </section>
                </div>

                {/* Right Column: Visualization & Results */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Visualizer (Placeholder) */}
                    <Card className="h-[400px] glass-card border-primary/20 flex flex-col">
                        <CardHeader className="py-4 border-b border-border/50">
                            <CardTitle className="text-lg">Structure Visualization</CardTitle>
                        </CardHeader>
                        <CardContent className="flex-1 flex items-center justify-center relative p-0 overflow-hidden">
                            <div className="absolute inset-0 bg-grid-white/[0.02] bg-[length:20px_20px]" />
                            <p className="text-muted-foreground z-10">2D Frame Visualizer (Coming Next)</p>
                        </CardContent>
                    </Card>

                    {/* Results */}
                    {result && (
                        <Card className="glass-card border-primary/20">
                            <CardHeader>
                                <CardTitle>Analysis Results</CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-6">
                                <div>
                                    <h4 className="text-sm font-semibold mb-2 text-primary">Nodal Displacements</h4>
                                    <Table>
                                        <TableHeader>
                                            <TableRow><TableHead>Type</TableHead><TableHead>Value</TableHead></TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {result.displacements.map((d: number, i: number) => {
                                                // Map index to Node ID and DOF using nodes list
                                                const nodeIdx = Math.floor(i / 3);
                                                if (nodeIdx >= nodes.length) return null;
                                                const node = nodes[nodeIdx];
                                                const dofType = i % 3 === 0 ? 'X' : i % 3 === 1 ? 'Y' : 'Rot';
                                                if (Math.abs(d) < 1e-10) return null; // Hide zero displacements
                                                return (
                                                    <TableRow key={i}>
                                                        <TableCell>{`Node ${node.id.slice(0, 4)} - ${dofType}`}</TableCell>
                                                        <TableCell>{d.toExponential(4)}</TableCell>
                                                    </TableRow>
                                                );
                                            })}
                                        </TableBody>
                                    </Table>
                                </div>

                                <div>
                                    <h4 className="text-sm font-semibold mb-2 text-primary">Reactions</h4>
                                    <Table>
                                        <TableHeader>
                                            <TableRow><TableHead>DOF Index</TableHead><TableHead>Reaction Force</TableHead></TableRow>
                                        </TableHeader>
                                        <TableBody>
                                            {result.reactions.map((r: number, i: number) => {
                                                if (Math.abs(r) < 1e-6) return null;
                                                return (
                                                    <TableRow key={i}>
                                                        <TableCell>{`DOF ${i}`}</TableCell>
                                                        <TableCell>{r.toFixed(4)}</TableCell>
                                                    </TableRow>
                                                )
                                            })}
                                        </TableBody>
                                    </Table>
                                </div>
                            </CardContent>
                        </Card>
                    )}
                </div>
            </div>
        </div>
    );
}
