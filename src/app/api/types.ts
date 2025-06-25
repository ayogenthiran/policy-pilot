// Request/Response types for PolicyPilot API routes

export interface ChatRequest {
  question: string;
  fileId?: string;
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