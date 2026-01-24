import React, { useState } from 'react';
import { BeamAnalysis } from '@/components/BeamAnalysis';
import { FrameAnalysis } from '@/components/FrameAnalysis';
import { Toaster } from '@/components/ui/toaster';
import { Button } from '@/components/ui/button';
import { GitBranch, Layers } from 'lucide-react';

type AnalysisMode = 'BEAM' | 'FRAME';

function App() {
  const [mode, setMode] = useState<AnalysisMode>('BEAM');

  return (
    <div className="min-h-screen p-4 md:p-8 max-w-7xl mx-auto space-y-8 pb-20">
      {/* Header & Mode Selector */}
      <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 animate-in slide-in-from-top duration-500 border-b border-border/40 pb-6">
        <div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            StructSolve
          </h1>
          <p className="text-muted-foreground mt-1">
            Advanced Structural Analysis Platform
          </p>
        </div>

        <div className="flex p-1 bg-muted/30 rounded-lg border border-border/50">
          <Button
            variant={mode === 'BEAM' ? 'default' : 'ghost'}
            onClick={() => setMode('BEAM')}
            className={`gap-2 ${mode === 'BEAM' ? 'shadow-md' : 'text-muted-foreground hover:text-white'}`}
          >
            <Layers className="h-4 w-4" />
            Continuous Beam
          </Button>
          <Button
            variant={mode === 'FRAME' ? 'default' : 'ghost'}
            onClick={() => setMode('FRAME')}
            className={`gap-2 ${mode === 'FRAME' ? 'shadow-md' : 'text-muted-foreground hover:text-white'}`}
          >
            <GitBranch className="h-4 w-4" />
            2D Frame
          </Button>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="animate-in fade-in zoom-in-95 duration-300">
        {mode === 'BEAM' ? (
          <BeamAnalysis />
        ) : (
          <FrameAnalysis />
        )}
      </main>

      <Toaster />
    </div>
  );
}

export default App;
