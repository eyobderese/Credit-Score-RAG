/**
 * API Client for Credit Scoring RAG Backend
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Types
export interface QueryRequest {
    question: string;
    top_k?: number;
    use_reranking?: boolean;
    validate_answer?: boolean;
}

export interface SourceInfo {
    document: string;
    chunk_id: string;
    content: string;
    similarity: number;
    metadata?: Record<string, any>;
}

export interface QueryResponse {
    answer: string;
    sources: SourceInfo[];
    confidence: number;
    query_time_ms: number;
    retrieved_count: number;
    timestamp: string;
}

export interface DocumentInfo {
    id: string;
    filename: string;
    document_type: string;
    chunk_count: number;
    total_characters: number;
    ingested_at: string;
    metadata?: Record<string, any>;
}

export interface DocumentStats {
    total_documents: number;
    total_chunks: number;
    total_characters: number;
    documents_by_type: Record<string, number>;
    last_ingestion?: string;
    vector_store_size_mb?: number;
}

export interface EvaluationMetrics {
    answer_accuracy: number;
    source_accuracy: number;
    hallucination_rate: number;
    citation_coverage: number;
    precision_at_k: number;
    recall_at_k: number;
    mrr: number;
    avg_response_time_ms: number;
    avg_confidence: number;
}

export interface EvaluationResult {
    id: string;
    test_set_name: string;
    run_at: string;
    metrics: EvaluationMetrics;
    results: any[];
    failed_cases: string[];
    error_categories: Record<string, number>;
}

export interface ExperimentConfig {
    name: string;
    description?: string;
    chunk_size: number;
    chunk_overlap: number;
    top_k: number;
    similarity_threshold: number;
    embedding_model: string;
    llm_model: string;
    temperature: number;
    use_reranking?: boolean;
    use_hybrid_search?: boolean;
}

export interface ExperimentResult {
    id: string;
    config: ExperimentConfig;
    metrics: EvaluationMetrics;
    run_at: string;
    duration_seconds: number;
}

// Query API
export const queryAPI = {
    async query(request: QueryRequest): Promise<QueryResponse> {
        const response = await apiClient.post('/api/query', request);
        return response.data;
    },

    async batchQuery(questions: string[], top_k?: number): Promise<{ results: QueryResponse[]; total_time_ms: number }> {
        const response = await apiClient.post('/api/query/batch', { questions, top_k });
        return response.data;
    },

    async submitFeedback(data: {
        question: string;
        answer: string;
        is_helpful: boolean;
        feedback_text?: string;
    }): Promise<void> {
        await apiClient.post('/api/query/feedback', data);
    },
};

// Documents API
export const documentsAPI = {
    async uploadDocument(file: File): Promise<any> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await apiClient.post('/api/documents/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    async listDocuments(): Promise<{ documents: DocumentInfo[]; total_count: number }> {
        const response = await apiClient.get('/api/documents');
        return response.data;
    },

    async deleteDocument(id: string): Promise<void> {
        await apiClient.delete(`/api/documents/${id}`);
    },

    async getStats(): Promise<DocumentStats> {
        const response = await apiClient.get('/api/documents/stats');
        return response.data;
    },
};

// Evaluation API
export const evaluationAPI = {
    async runEvaluation(data: { sample_size?: number }): Promise<EvaluationResult> {
        const response = await apiClient.post('/api/evaluation/run', data);
        return response.data;
    },

    async listResults(): Promise<EvaluationResult[]> {
        const response = await apiClient.get('/api/evaluation/results');
        return response.data;
    },
};

// Experiments API
export const experimentsAPI = {
    async ablationChunkSize(chunk_sizes?: string, sample_size?: number): Promise<any> {
        const response = await apiClient.post('/api/experiments/ablation/chunk-size', null, {
            params: { chunk_sizes, sample_size },
        });
        return response.data;
    },

    async ablationTopK(top_k_values?: string, sample_size?: number): Promise<any> {
        const response = await apiClient.post('/api/experiments/ablation/top-k', null, {
            params: { top_k_values, sample_size },
        });
        return response.data;
    },
};

// Health API
export const healthAPI = {
    async check(): Promise<any> {
        const response = await apiClient.get('/health');
        return response.data;
    },
};

export default apiClient;
