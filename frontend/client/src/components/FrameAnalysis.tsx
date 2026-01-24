import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Construction } from 'lucide-react';

export function FrameAnalysis() {
    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">2D Frame Analysis</h2>
                    <p className="text-muted-foreground">Analyze 2D frames using Direct Stiffness Method</p>
                </div>
            </div>

            <Card className="glass-card border-primary/20">
                <CardHeader className="text-center pb-2">
                    <div className="mx-auto bg-primary/20 p-4 rounded-full w-fit mb-4">
                        <Construction className="h-12 w-12 text-primary" />
                    </div>
                    <CardTitle className="text-2xl text-white">Under Construction</CardTitle>
                    <CardDescription className="text-lg">
                        Phase 2: Frame Analysis module is currently being built.
                    </CardDescription>
                </CardHeader>
                <CardContent className="text-center text-muted-foreground max-w-lg mx-auto">
                    <p>
                        This module will support:
                    </p>
                    <ul className="list-disc text-left mt-4 space-y-2 pl-8">
                        <li>Arbitrary 2D Node Coordinates (X, Y)</li>
                        <li>Frame Members with Axial & Bending stiffness</li>
                        <li>Sway Support (DX, DY, Rotation)</li>
                        <li>Global Stiffness Matrix Solver</li>
                    </ul>
                </CardContent>
            </Card>
        </div>
    );
}
