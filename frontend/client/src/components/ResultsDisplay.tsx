import React from 'react';
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
  if (!result) return null;
  if (!result.spans || result.spans.length === 0) {
    return (
      <div className="glass-panel p-6 rounded-2xl">
        <p className="text-white">No results to display</p>
      </div>
    );
  }

  // Flatten data for continuous plotting
  const allStations = result.spans.flatMap(s => s.stations);
  const allShear = result.spans.flatMap(s => s.shearForce);
  const allMoment = result.spans.flatMap(s => s.bendingMoment);

  // Common Chart Options
  const options: ChartOptions<'line'> = {
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
        title: { display: true, text: 'Position (m)', color: 'rgba(255, 255, 255, 0.5)' }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        ticks: { color: 'rgba(255, 255, 255, 0.5)' }
      }
    },
    plugins: {
      legend: {
        labels: { color: 'white' }
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

  const shearData = {
    labels: allStations,
    datasets: [
      {
        label: 'Shear Force (kN)',
        data: allStations.map((x, i) => ({ x, y: allShear[i] })),
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        fill: true,
        tension: 0.1
      }
    ]
  };

  const momentData = {
    labels: allStations,
    datasets: [
      {
        label: 'Bending Moment (kN·m)',
        data: allStations.map((x, i) => ({ x, y: allMoment[i] })),
        borderColor: 'rgb(53, 162, 235)',
        backgroundColor: 'rgba(53, 162, 235, 0.2)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  return (
    <div className="space-y-6 animate-in slide-in-from-bottom-10 duration-500 delay-150">
      <div className="glass-panel p-6 rounded-2xl">
        <h3 className="text-xl font-bold mb-4 text-white">Shear Force Diagram (SFD)</h3>
        <div className="h-[300px]">
          <Line options={options} data={shearData} />
        </div>
      </div>

      <div className="glass-panel p-6 rounded-2xl">
        <h3 className="text-xl font-bold mb-4 text-white">Bending Moment Diagram (BMD)</h3>
        <div className="h-[300px]">
          <Line options={options} data={momentData} />
        </div>
      </div>
    </div>
  );
};
