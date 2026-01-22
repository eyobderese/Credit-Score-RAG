import React, { useState } from 'react';
import { Send, Loader2, FileText, ThumbsUp, ThumbsDown, Sparkles, Clock, CheckCircle2 } from 'lucide-react';
import { queryAPI } from '../services/api';
import type { QueryResponse } from '../services/api';

const sampleQuestions = [
    'What is the minimum credit score for FHA loans?',
    'What is the maximum DTI ratio for conventional mortgages?',
    'What is the waiting period after bankruptcy?',
];

export default function QueryPage() {
    const [question, setQuestion] = useState('');
    const [response, setResponse] = useState<QueryResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleQuery = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!question.trim() || loading) return;

        setLoading(true);
        setError('');
        setResponse(null);

        try {
            const result = await queryAPI.query({ question: question.trim() });
            setResponse(result);
        } catch (err: any) {
            setError(err.response?.data?.detail || err.message || 'Query failed');
        } finally {
            setLoading(false);
        }
    };

    const getConfidenceColor = (confidence: number) => {
        if (confidence >= 80) return 'var(--success)';
        if (confidence >= 60) return 'var(--warning)';
        return 'var(--error)';
    };

    const getConfidenceGradient = (confidence: number) => {
        if (confidence >= 80) return 'var(--gradient-success)';
        if (confidence >= 60) return 'var(--gradient-warning)';
        return 'var(--gradient-error)';
    };

    return (
        <div style={{ maxWidth: 950, margin: '0 auto' }}>
            <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
                <h1 className="page-title" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', justifyContent: 'center' }}>
                    <Sparkles size={36} /> Ask a Question
                </h1>
                <p className="page-description" style={{ margin: '0 auto' }}>
                    Get AI-powered answers about credit policies with source citations
                </p>
            </div>

            <div className="card" style={{ padding: '2.5rem' }}>
                <form onSubmit={handleQuery}>
                    <div style={{ position: 'relative', marginBottom: '1.5rem' }}>
                        <textarea
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            placeholder="Ask about credit scoring policies, DTI requirements, documentation needs..."
                            className="form-input"
                            style={{
                                width: '100%',
                                minHeight: 140,
                                fontSize: '1.05rem',
                                paddingRight: '1.25rem'
                            }}
                            disabled={loading}
                        />
                    </div>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <div style={{ fontSize: '0.875rem', color: 'var(--text-tertiary)', marginBottom: '0.75rem', fontWeight: 500 }}>
                            Try a sample question:
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.625rem' }}>
                            {sampleQuestions.map((q, i) => (
                                <button
                                    key={i}
                                    type="button"
                                    onClick={() => setQuestion(q)}
                                    disabled={loading}
                                    style={{
                                        padding: '0.625rem 1rem',
                                        background: 'rgba(139, 92, 246, 0.1)',
                                        border: '1px solid rgba(139, 92, 246, 0.2)',
                                        borderRadius: 10,
                                        color: 'var(--text-secondary)',
                                        fontSize: '0.875rem',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s ease'
                                    }}
                                >
                                    {q}
                                </button>
                            ))}
                        </div>
                    </div>

                    <button type="submit" className="btn btn-primary" style={{ padding: '1rem 2rem' }} disabled={!question.trim() || loading}>
                        {loading ? (
                            <><Loader2 size={20} className="animate-spin" /> Processing...</>
                        ) : (
                            <><Send size={20} /> Ask Question</>
                        )}
                    </button>
                </form>
            </div>

            {error && (
                <div className="animate-fadeIn" style={{
                    background: 'rgba(239, 68, 68, 0.1)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    borderRadius: 14,
                    padding: '1.25rem 1.5rem',
                    color: 'var(--error)',
                    marginBottom: '1.75rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem'
                }}>
                    <span style={{ fontWeight: 600 }}>Error:</span> {error}
                </div>
            )}

            {response && (
                <div className="card animate-fadeIn" style={{ padding: '2.5rem' }}>
                    {/* Header */}
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <CheckCircle2 size={24} style={{ color: 'var(--success)' }} />
                            <h2 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Answer</h2>
                        </div>
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                            <div style={{
                                padding: '0.625rem 1.25rem',
                                background: 'rgba(0, 0, 0, 0.3)',
                                borderRadius: 10,
                                fontWeight: 600,
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem'
                            }}>
                                Confidence:
                                <span style={{
                                    background: getConfidenceGradient(response.confidence),
                                    WebkitBackgroundClip: 'text',
                                    WebkitTextFillColor: 'transparent',
                                    fontWeight: 800
                                }}>
                                    {response.confidence}%
                                </span>
                            </div>
                            <div style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.375rem',
                                color: 'var(--text-tertiary)',
                                fontSize: '0.9rem'
                            }}>
                                <Clock size={16} />
                                {response.query_time_ms.toFixed(0)}ms
                            </div>
                        </div>
                    </div>

                    {/* Answer */}
                    <div style={{
                        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(99, 102, 241, 0.05))',
                        borderLeft: '4px solid var(--accent-primary)',
                        padding: '1.75rem 2rem',
                        borderRadius: '0 14px 14px 0',
                        marginBottom: '2rem',
                        fontSize: '1.15rem',
                        lineHeight: 1.8
                    }}>
                        {response.answer}
                    </div>

                    {/* Sources */}
                    <div>
                        <h3 style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.625rem',
                            marginBottom: '1.25rem',
                            fontSize: '1.15rem',
                            fontWeight: 700
                        }}>
                            <FileText size={22} style={{ color: 'var(--accent-primary)' }} />
                            Sources ({response.sources.length})
                        </h3>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
                            {response.sources.map((source, i) => (
                                <div key={i} className="list-item" style={{
                                    flexDirection: 'column',
                                    alignItems: 'flex-start',
                                    padding: '1.25rem 1.5rem'
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', marginBottom: '0.75rem', alignItems: 'center' }}>
                                        <span style={{
                                            fontWeight: 700,
                                            color: 'var(--accent-primary)',
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.5rem'
                                        }}>
                                            <FileText size={16} /> {source.document}
                                        </span>
                                        <span style={{
                                            fontSize: '0.8rem',
                                            background: 'rgba(139, 92, 246, 0.15)',
                                            padding: '0.375rem 0.75rem',
                                            borderRadius: 8,
                                            fontWeight: 600,
                                            color: 'var(--accent-primary)'
                                        }}>
                                            {(source.similarity * 100).toFixed(1)}% match
                                        </span>
                                    </div>
                                    <p style={{
                                        fontSize: '0.925rem',
                                        color: 'var(--text-secondary)',
                                        lineHeight: 1.7
                                    }}>
                                        {source.content}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
