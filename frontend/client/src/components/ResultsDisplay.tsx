import React, { useState } from 'react';
import { CalculationResult } from '@/lib/types';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface ResultsDisplayProps {
  result: CalculationResult | null;
}

export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ result }) => {
  const [showFMD, setShowFMD] = useState(true);
  const [showEMD, setShowEMD] = useState(true);
  const [showBMD, setShowBMD] = useState(true);

  if (!result) return null;
  if (!result.spans || result.spans.length === 0) {
    return (
      <div className="glass-panel p-6 rounded-2xl">
        <p className="text-white">No results to display</p>
      </div>
    );
  }

  // Common Chart Options
  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    scales: {
      x: {
        type: 'linear',
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        ticks: { color: 'rgba(255, 255, 255, 0.5)' },
        title: { display: true, text: 'Position (m)', color: 'rgba(255, 255, 255, 0.7)' }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        ticks: { color: 'rgba(255, 255, 255, 0.5)' }
      }
    },
    plugins: {
      legend: {
        labels: { color: 'white', font: { size: 12 } }
      },
      tooltip: {
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        titleColor: 'white',
        bodyColor: 'white',
        borderColor: 'rgba(255, 255, 255, 0.2)',
        borderWidth: 1
      }
    }
  };

  // Prepare SFD data (combine all spans)
  const sfdData = {
    datasets: result.spans.map((span, idx) => ({
      label: `Span ${idx + 1} - Shear Force`,
      data: span.sfdData.xCoords.map((x, i) => ({
        x: x + (idx * (result.spans[idx - 1]?.sfdData.xCoords.length ? result.spans.slice(0, idx).reduce((sum, s) => sum + Math.max(...s.sfdData.xCoords), 0) : 0)),
        y: span.sfdData.values[i]
      })),
      borderColor: `hsl(${idx * 120}, 70%, 60%)`,
      backgroundColor: `hsla(${idx * 120}, 70%, 60%, 0.1)`,
      fill: true,
      tension: 0,
      borderWidth: 2
    }))
  };

  // Prepare BMD data with FMD, EMD, and complete BMD
  const bmdDatasets = [];

  result.spans.forEach((span, idx) => {
    const offsetX = idx > 0 ? result.spans.slice(0, idx).reduce((sum, s) => sum + Math.max(...s.bmdData.xCoords), 0) : 0;

    if (showFMD) {
      bmdDatasets.push({
        label: `Span ${idx + 1} - FMD (Simply Supported)`,
        data: span.fmdData.xCoords.map((x, i) => ({ x: x + offsetX, y: span.fmdData.values[i] })),
        borderColor: `hsla(210, 100%, 60%, 0.6)`,
        backgroundColor: 'transparent',
        borderDash: [5, 5],
        borderWidth: 2,
        tension: 0.4,
        pointRadius: 0
      });
    }

    if (showEMD) {
      bmdDatasets.push({
        label: `Span ${idx + 1} - EMD (End Moments)`,
        data: span.emdData.xCoords.map((x, i) => ({ x: x + offsetX, y: span.emdData.values[i] })),
        borderColor: `hsla(0, 100%, 60%, 0.6)`,
        backgroundColor: 'transparent',
        borderDash: [10, 5],
        borderWidth: 2,
        tension: 0,
        pointRadius: 0
      });
    }

    if (showBMD) {
      bmdDatasets.push({
        label: `Span ${idx + 1} - Complete BMD`,
        data: span.bmdData.xCoords.map((x, i) => ({ x: x + offsetX, y: span.bmdData.values[i] })),
        borderColor: `hsl(${idx * 120 + 150}, 70%, 60%)`,
        backgroundColor: `hsla(${idx * 120 + 150}, 70%, 60%, 0.1)`,
        fill: true,
        borderWidth: 3,
        tension: 0.4,
        pointRadius: 0
      });
    }
  });

  const bmdData = { datasets: bmdDatasets };

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-10 duration-500 delay-150">
      {/* Shear Force Diagram */}
      <div className="glass-panel p-6 rounded-2xl">
        <h3 className="text-xl font-bold mb-4 text-white flex items-center gap-2">
          <span className="text-2xl">📊</span>
          Shear Force Diagram (SFD)
        </h3>
        <div className="h-[300px]">
          <Line options={chartOptions} data={sfdData} />
        </div>
      </div>

      {/* Bending Moment Diagram with Controls */}
      <div className="glass-panel p-6 rounded-2xl">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white flex items-center gap-2">
            <span className="text-2xl">📈</span>
            Bending Moment Diagram (BMD)
          </h3>

          {/* Toggle Controls */}
          <div className="flex gap-3 text-sm">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showFMD}
                onChange={(e) => setShowFMD(e.target.checked)}
                className="w-4 h-4 rounded accent-blue-500"
              />
              <span className="text-blue-400">FMD</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showEMD}
                onChange={(e) => setShowEMD(e.target.checked)}
                className="w-4 h-4 rounded accent-red-500"
              />
              <span className="text-red-400">EMD</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={showBMD}
                onChange={(e) => setShowBMD(e.target.checked)}
                className="w-4 h-4 rounded accent-green-500"
              />
              <span className="text-green-400">Complete BMD</span>
            </label>
          </div>
        </div>

        {/* Legend Explanation */}
        <div className="mb-4 p-3 bg-white/5 rounded-lg text-xs text-white/70 space-y-1">
          <p><span className="text-blue-400">FMD (Free Moment)</span>: Moments as if beam were simply supported</p>
          <p><span className="text-red-400">EMD (End Moment)</span>: Linear variation from support moments</p>
          <p><span className="text-green-400">Complete BMD</span>: Superposition of FMD + EMD</p>
        </div>

        <div className="h-[400px]">
          <Line options={chartOptions} data={bmdData} />
        </div>
      </div>

      {/* Numerical Results */}
      <div className="glass-panel p-6 rounded-2xl">
        <h3 className="text-xl font-bold mb-4 text-white flex items-center gap-2">
          <span className="text-2xl">🔢</span>
          Numerical Results
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {result.spans.map((span, idx) => (
            <div key={idx} className="bg-white/5 p-4 rounded-lg">
              <h4 className="font-semibold text-white mb-2">Span {idx + 1}</h4>
              <div className="space-y-1 text-sm text-white/80">
                <p>Left Moment: <span className="text-blue-400 font-mono">{span.momentLeft.toFixed(2)} kN·m</span></p>
                <p>Right Moment: <span className="text-blue-400 font-mono">{span.momentRight.toFixed(2)} kN·m</span></p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
