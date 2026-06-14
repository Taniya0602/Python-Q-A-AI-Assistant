export interface Source {
  title: string;
  score: number;
  snippet: string;
}

export interface AnswerResponse {
  question: string;
  answer: string;
  sources: Source[];
  model: string;
  latency_ms: number;
  timestamp: string;
}

export interface HealthResponse {
  status: string;
  vector_store_loaded: boolean;
  total_documents: number;
  model: string;
  version: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  latency_ms?: number;
  model?: string;
  timestamp: Date;
}
