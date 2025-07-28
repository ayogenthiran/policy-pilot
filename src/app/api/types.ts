// Request/Response types for PolicyPilot API routes

export interface ChatRequest {
  question?: string;
  message?: string;
  fileId?: string;
  fileName?: string;
  useHybridSearch?: boolean;
  matchThreshold?: number;
}

export interface ChatResponse {
  answer: string;
  sources?: string[];
}

export interface UploadResponse {
  fileId: string;
  status: string;
}

export interface ErrorResponse {
  error: string;
  message: string;
} 