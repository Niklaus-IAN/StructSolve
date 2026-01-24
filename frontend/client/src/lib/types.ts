export type LoadType = 'UDL' | 'POINT_CENTER' | 'NONE';
export type SupportType = 'FIXED' | 'PINNED' | 'ROLLER';

export interface Span {
  id: string;
  length: number;
  elasticModulus: number; // E (kN/m2)
  inertia: number;        // I (m4)
  loadType: LoadType;
  loadMagnitude: number;  // kN or kN/m
  leftSupport: SupportType;
  rightSupport: SupportType;
}

export interface CalculationResult {
  spans: SpanResult[];
  reactions: number[];
  maxMoment: number;
  maxShear: number;
}

export interface SpanResult {
  spanId: string;
  stations: number[]; // x coordinates along the span
  shearForce: number[];
  bendingMoment: number[];
  slope: number[];
  deflection: number[];
  momentLeft: number;
  momentRight: number;
}
