import React, { useState } from 'react';
import { FrameNode, FrameMember } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Plus, Trash2, Grid, Info } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

export function FrameAnalysis() {
    const [nodes, setNodes] = useState<FrameNode[]>([
        { id: '1', x: 0, y: 0, fixX: true, fixY: true, fixR: true }, // Fixed support at origin
        { id: '2', x: 0, y: 3, fixX: false, fixY: false, fixR: false }, // Node at 3m height
    ]);
    const [members, setMembers] = useState<FrameMember[]>([
        { id: '1', startNodeId: '1', endNodeId: '2', elasticModulus: 200, momentOfInertia: 500, crossSectionArea: 0.01 }
    ]);

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
            toast({ title: "Cannot remove node", description: "Node is connected to a member. Remove member first.", variant: "destructive" });
            return;
        }
        setNodes(nodes.filter(n => n.id !== id));
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">2D Frame Analysis</h2>
                    <p className="text-muted-foreground">Define nodes and members for matrix analysis</p>
                </div>
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

                    {/* Members (Placeholder for next step) */}
                    <section className="space-y-4 opacity-50">
                        <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <Grid className="h-4 w-4 text-primary" /> Members
                            </h3>
                        </div>
                        <div className="p-4 border border-dashed border-border/50 rounded-lg text-center text-sm text-muted-foreground">
                            Define nodes first, then connect them with members.
                        </div>
                    </section>
                </div>

                {/* Right Column: Visualization */}
                <div className="lg:col-span-2">
                    <Card className="h-[500px] glass-card border-primary/20 flex items-center justify-center">
                        <p className="text-muted-foreground">2D Frame Visualizer (Coming Soon)</p>
                    </Card>
                </div>
            </div>
        </div>
    );
}
