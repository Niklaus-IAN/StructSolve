export type LoadType = 'UDL' | 'POINT_CENTER' | 'POINT_ARBITRARY' | 'TRIANGULAR' | 'MOMENT' | 'NONE';
export type SupportType = 'FIXED' | 'PINNED' | 'ROLLER';

export interface DiagramData {
  xCoords: number[];
  values: number[];
}

export interface Span {
  id: string;
  length: number;
  elasticModulus: number; // E (kN/m2)
  inertia: number;        // I (m4)
  loadType: LoadType;
  loadMagnitude: number;  // kN or kN/m
  loadPosition?: number;  // Position from left for POINT_ARBITRARY (m)
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
  momentLeft: number;
  momentRight: number;

  // Diagram data (new)
  sfdData: DiagramData;  // Shear Force Diagram
  fmdData: DiagramData;  // Free Moment Diagram (simply supported)
  emdData: DiagramData;  // End Moment Diagram (from support moments)
  bmdData: DiagramData;  // Complete BMD = FMD + EMD

  // Legacy fields for backward compatibility
  stations?: number[];
  shearForce?: number[];
  bendingMoment?: number[];
  slope?: number[];

// === FRAME ANALYSIS TYPES ===

export interface FrameNode {
  id: string;
  x: number;
  y: number;
  fixX: boolean; // Restrained in X
  fixY: boolean; // Restrained in Y
  fixR: boolean; // Restrained Rotation
}

export interface FrameMember {
  id: string;
  startNodeId: string;
  endNodeId: string;
  elasticModulus: number; // E (kN/m²)
  momentOfInertia: number; // I (m⁴)
  crossSectionArea: number; // A (m²)
}

export type FrameLoadType = 'NODE_LOAD' | 'MEMBER_POINT_LOAD';

export interface FramePointLoad {
  id: string;
  type: FrameLoadType;
  targetId: string; // Node ID or Member ID
  magnitudeX: number; // kN
  magnitudeY: number; // kN
  moment: number; // kNm
  position?: number; // m (from start node, for member loads)
}

export interface FrameUniformLoad {
  id: string;
  memberId: string;
  magnitudeX: number; // kN/m (Local axis)
  magnitudeY: number; // kN/m (Local axis)
}

export interface FrameAnalysisRequest {
  nodes: FrameNode[];
  members: FrameMember[];
  pointLoads: FramePointLoad[];
  uniformLoads: FrameUniformLoad[];
}
