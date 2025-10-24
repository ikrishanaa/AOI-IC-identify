// API Response Types for AOI IC Identify System

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface OCRResult {
  text: string;
  confidence: number;
  bounding_box?: BoundingBox;
}

export interface LogoResult {
  manufacturer: string;
  confidence: number;
  bounding_box?: BoundingBox;
}

export interface VisualSignatureResult {
  similarity: number;
  reference_id?: string;
  embedding?: number[];
}

export interface AnomalyResult {
  score: number;
  is_anomalous: boolean;
  reconstruction_error?: number;
}

export interface InspectionResultData {
  verdict: "pass" | "fail" | "needs_review";
  confidence: number;
  score: number;
  ocr?: OCRResult;
  logo?: LogoResult;
  visual_signature?: VisualSignatureResult;
  anomaly?: AnomalyResult;
  decision_notes: string[];
}

export interface InspectionJob {
  job_id: number;
  status: "pending" | "processing" | "completed" | "failed";
  created_at: string;
  completed_at?: string;
  result?: InspectionResultData;
  error?: string;
}

export interface CreateInspectionRequest {
  image_data: string;
  component_type?: string;
  reference_id?: string;
  metadata?: Record<string, any>;
}

export interface InspectionListResponse {
  total: number;
  limit: number;
  offset: number;
  jobs: Array<{
    id: number;
    status: string;
    created_at?: string;
    completed_at?: string;
  }>;
}

export interface HealthResponse {
  service: string;
  status: string;
  db?: string;
  version?: string;
}

export interface AllHealthResponse {
  inspection?: HealthResponse;
  verification?: HealthResponse;
  decision?: HealthResponse;
  stream?: HealthResponse;
}

// Live stream types
export interface LiveFrameAnalysis {
  frame_id: number;
  timestamp: number;
  verdict?: string;
  confidence?: number;
  ocr_text?: string;
  logo_manufacturer?: string;
  bounding_boxes: any[];
  notes: string[];
}

export interface LiveStreamMessage {
  type: "connected" | "analysis" | "capture_ack" | "error" | "info";
  message?: string;
  data?: LiveFrameAnalysis;
  frame_id?: number;
}
