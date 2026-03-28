export interface FIIHistory {
  month: string;
  price: number;
  dividend: number;
}

export interface FIIData {
  ticker: string;
  name: string;
  type: string;
  segment: string;
  price: number;
  dy: number;
  pvp: number;
  liquidity: number;
  vacancy: number;
  shareholders: number;
  netWorth: number;
  history: FIIHistory[];
  managementReport: string;
}

export interface AIAnalysis {
  pros: string[];
  cons: string[];
  diagnosis: "FII Forte" | "FII Moderado" | "FII Arriscado";
  recommendation: string;
  explanation: string;
  reportAnalysis: string;
  score: number;
}

export interface ReportAnalysisResult {
  summary: string;
  managementTone: "Otimista" | "Neutro" | "Pessimista";
  dividendGuidance: string;
  risks: string[];
  highlights: string[];
}
