import React from 'react';
import { Span, LoadType, SupportType } from '@/lib/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Trash2 } from 'lucide-react';

interface SpanInputProps {
  span: Span;
  index: number;
  onChange: (id: string, field: keyof Span, value: any) => void;
  onRemove: (id: string) => void;
}

export const SpanInput: React.FC<SpanInputProps> = ({ span, index, onChange, onRemove }) => {
  return (
    <div className="glass-card p-4 rounded-xl mb-4 animate-in slide-in-from-left-5 duration-300">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-primary">Span {index + 1}</h3>
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={() => onRemove(span.id)}
          className="text-destructive hover:text-destructive/80 hover:bg-destructive/10"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Geometry & Material */}
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Length (m)</label>
            <Input 
              type="number" 
              value={span.length} 
              onChange={(e) => onChange(span.id, 'length', Number(e.target.value))}
              className="glass-input font-mono"
              min={0}
              step={0.1}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Inertia (10⁶ mm⁴)</label>
            <Input 
              type="number" 
              value={span.inertia} 
              onChange={(e) => onChange(span.id, 'inertia', Number(e.target.value))}
              className="glass-input font-mono"
              min={0}
            />
          </div>
        </div>

        {/* Supports */}
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Left Support</label>
            <Select 
              value={span.leftSupport} 
              onValueChange={(val: SupportType) => onChange(span.id, 'leftSupport', val)}
            >
              <SelectTrigger className="glass-input">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="FIXED">Fixed</SelectItem>
                <SelectItem value="PINNED">Pinned</SelectItem>
                <SelectItem value="ROLLER">Roller</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Right Support</label>
            <Select 
              value={span.rightSupport} 
              onValueChange={(val: SupportType) => onChange(span.id, 'rightSupport', val)}
            >
              <SelectTrigger className="glass-input">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="FIXED">Fixed</SelectItem>
                <SelectItem value="PINNED">Pinned</SelectItem>
                <SelectItem value="ROLLER">Roller</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Loading */}
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Load Type</label>
            <Select 
              value={span.loadType} 
              onValueChange={(val: LoadType) => onChange(span.id, 'loadType', val)}
            >
              <SelectTrigger className="glass-input">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="NONE">No Load</SelectItem>
                <SelectItem value="UDL">UDL (Uniform)</SelectItem>
                <SelectItem value="POINT_CENTER">Point (Center)</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {span.loadType !== 'NONE' && (
            <div className="space-y-2 animate-in fade-in zoom-in-95">
              <label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                {span.loadType === 'UDL' ? 'Magnitude (kN/m)' : 'Magnitude (kN)'}
              </label>
              <Input 
                type="number" 
                value={span.loadMagnitude} 
                onChange={(e) => onChange(span.id, 'loadMagnitude', Number(e.target.value))}
                className="glass-input font-mono"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
