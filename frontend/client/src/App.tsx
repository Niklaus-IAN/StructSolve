import React, { useState } from 'react';
import { Span, CalculationResult } from '@/lib/types';
import { solveContinuousBeam } from '@/lib/solver';
import { SpanInput } from '@/components/SpanInput';
import { ResultsDisplay } from '@/components/ResultsDisplay';
import { BeamVisualizer } from '@/components/BeamVisualizer';
import { Button } from '@/components/ui/button';
import { Plus, Play, Info } from 'lucide-react';
import { Toaster } from '@/components/ui/toaster';
import { useToast } from '@/hooks/use-toast';

function App() {
  const [spans, setSpans] = useState<Span[]>([
    {
      id: '1',
      length: 5,
      elasticModulus: 200,
      inertia: 500,
      loadType: 'UDL',
      loadMagnitude: 10,
      leftSupport: 'FIXED',
      rightSupport: 'ROLLER'
    },
    {
      id: '2',
      length: 4,
      elasticModulus: 200,
      inertia: 500,
      loadType: 'NONE',
      loadMagnitude: 0,
      leftSupport: 'ROLLER',
      rightSupport: 'PINNED'
    },
  ]);
  const [result, setResult] = useState<CalculationResult | null>(null);
  const { toast } = useToast();

  const handleAddSpan = () => {
    const lastSpan = spans[spans.length - 1];
    const newSpan: Span = {
      id: crypto.randomUUID(),
      length: 5,
      elasticModulus: 200,
      inertia: 500,
      loadType: 'NONE',
      loadMagnitude: 0,
      leftSupport: lastSpan ? lastSpan.rightSupport : 'PINNED',
      rightSupport: 'ROLLER'
    };
    setSpans([...spans, newSpan]);
  };

  const handleRemoveSpan = (id: string) => {
    if (spans.length <= 1) {
      toast({
        title: "Cannot remove span",
        description: "You must have at least one span defined.",
        variant: "destructive"
      });
      return;
    }
    setSpans(spans.filter(s => s.id !== id));
  };

  const handleChangeSpan = (id: string, field: keyof Span, value: any) => {
    setSpans(spans.map(s => s.id === id ? { ...s, [field]: value } : s));
  };

  const handleCalculate = async () => {
    try {
      const res = await solveContinuousBeam(spans);
      setResult(res);
      toast({
        title: "Analysis Complete",
        description: "Slope deflection equations solved successfully.",
      });
    } catch (error) {
      console.error('Calculation error:', error);
      toast({
        title: "Calculation Error",
        description: error instanceof Error ? error.message : "Failed to solve the system.",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-7xl mx-auto space-y-8 pb-20">
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 animate-in slide-in-from-top duration-500">
        <div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            StructSolve
          </h1>
          <p className="text-muted-foreground mt-1">
            Slope Deflection Method & Structural Analysis
          </p>
        </div>
        <Button
          size="lg"
          onClick={handleCalculate}
          className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg hover:shadow-primary/20 transition-all"
        >
          <Play className="mr-2 h-4 w-4" /> Analyze Structure
        </Button>
      </header>

      <main className="space-y-8">
        {/* Input Section */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Info className="h-4 w-4 text-primary" /> Beam Configuration
            </h2>
            <Button onClick={handleAddSpan} variant="outline" className="glass-card hover:bg-white/10">
              <Plus className="mr-2 h-4 w-4" /> Add Span
            </Button>
          </div>

          <div className="grid gap-4">
            {spans.map((span, index) => (
              <SpanInput
                key={span.id}
                span={span}
                index={index}
                onChange={handleChangeSpan}
                onRemove={handleRemoveSpan}
              />
            ))}
          </div>
        </section>

        {/* Visualizer */}
        <BeamVisualizer spans={spans} />

        {/* Results */}
        {result && (
          <section className="space-y-4">
            <h2 className="text-xl font-semibold text-white">Analysis Results</h2>
            <ResultsDisplay result={result} />
          </section>
        )}
      </main>

      <Toaster />
    </div>
  );
}

export default App;
