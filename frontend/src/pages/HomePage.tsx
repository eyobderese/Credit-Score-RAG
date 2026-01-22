import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Brain, MessageSquare, FileText, BarChart3, FlaskConical, ArrowRight, Sparkles, Zap, Shield } from 'lucide-react';
import { healthAPI } from '../services/api';

const features = [
    { icon: MessageSquare, title: 'Query Interface', description: 'Ask natural language questions and get AI-powered answers with source citations.', link: '/query', color: '#6366f1' },
    { icon: FileText, title: 'Document Management', description: 'Upload and manage credit policy documents with automatic indexing.', link: '/documents', color: '#8b5cf6' },
    { icon: BarChart3, title: 'Evaluation Dashboard', description: 'Run comprehensive evaluations and track system performance.', link: '/evaluation', color: '#a855f7' },
    { icon: FlaskConical, title: 'Experiments Lab', description: 'Compare configurations and run ablation studies to optimize.', link: '/experiments', color: '#ec4899' },
];

export default function HomePage() {
    const [health, setHealth] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        healthAPI.check().then(setHealth).catch(console.error).finally(() => setLoading(false));
    }, []);

    return (
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
            {/* Hero Section */}
            <div style={{ textAlign: 'center', padding: '4rem 0', marginBottom: '4rem' }}>
                <div className="animate-float" style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: 120,
                    height: 120,
                    borderRadius: '28px',
                    background: 'var(--gradient-primary)',
                    marginBottom: '2rem',
                    boxShadow: '0 20px 60px rgba(139, 92, 246, 0.4)',
                    position: 'relative'
                }}>
                    <Brain size={56} color="white" />
                    <div style={{
                        position: 'absolute',
                        inset: -2,
                        borderRadius: '30px',
                        background: 'var(--gradient-primary)',
                        opacity: 0.3,
                        filter: 'blur(20px)',
                        zIndex: -1
                    }}></div>
                </div>

                <h1 style={{
                    fontSize: '4rem',
                    fontWeight: 800,
                    marginBottom: '1.25rem',
                    letterSpacing: '-0.03em',
                    lineHeight: 1.1
                }}>
                    Credit Scoring <span className="gradient-text">RAG Platform</span>
                </h1>

                <p style={{
                    fontSize: '1.35rem',
                    color: 'var(--text-secondary)',
                    maxWidth: 650,
                    margin: '0 auto 2.5rem',
                    lineHeight: 1.6
                }}>
                    A production-grade Retrieval-Augmented Generation system for answering credit policy questions with AI precision.
                </p>

                {/* Status Card */}
                {!loading && health && (
                    <div className="animate-fadeIn" style={{
                        background: 'var(--glass-bg)',
                        backdropFilter: 'blur(20px)',
                        borderRadius: 20,
                        padding: '1.75rem 2.5rem',
                        maxWidth: 480,
                        margin: '0 auto 2.5rem',
                        border: '1px solid var(--glass-border)',
                        boxShadow: 'var(--shadow-glow)'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.75rem', marginBottom: '1.25rem' }}>
                            <span className="status-dot"></span>
                            <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>
                                {health.status === 'healthy' ? 'System Online' : 'System Offline'}
                            </span>
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                            <div>
                                <div style={{ fontSize: '2.25rem', fontWeight: 800 }} className="gradient-text">
                                    {health.documents_indexed || 0}
                                </div>
                                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Documents</div>
                            </div>
                            <div>
                                <div style={{ fontSize: '2.25rem', fontWeight: 800 }} className="gradient-text">
                                    {health.chunks_indexed || 0}
                                </div>
                                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontWeight: 500 }}>Indexed Chunks</div>
                            </div>
                        </div>
                    </div>
                )}

                <div style={{ display: 'flex', gap: '1.25rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                    <Link to="/query" className="btn btn-primary" style={{ padding: '1rem 2rem', fontSize: '1.05rem' }}>
                        <Sparkles size={20} /> Start Querying <ArrowRight size={18} />
                    </Link>
                    <Link to="/evaluation" className="btn btn-secondary" style={{ padding: '1rem 2rem', fontSize: '1.05rem' }}>
                        <BarChart3 size={18} /> View Metrics
                    </Link>
                </div>
            </div>

            {/* Features Section */}
            <div style={{ marginBottom: '4rem' }}>
                <div style={{ textAlign: 'center', marginBottom: '3rem' }}>
                    <h2 style={{ fontSize: '2.5rem', fontWeight: 800, marginBottom: '0.75rem', letterSpacing: '-0.02em' }}>
                        Platform <span className="gradient-text">Features</span>
                    </h2>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '1.1rem' }}>
                        Everything you need for intelligent credit policy analysis
                    </p>
                </div>

                <div className="features-grid">
                    {features.map((feature, i) => (
                        <Link key={i} to={feature.link} className="feature-card" style={{ animationDelay: `${i * 0.1}s` }}>
                            <div className="feature-icon" style={{ background: `linear-gradient(135deg, ${feature.color}, ${feature.color}dd)` }}>
                                <feature.icon size={28} />
                            </div>
                            <h3 className="feature-title">{feature.title}</h3>
                            <p className="feature-description">{feature.description}</p>
                            <div style={{ marginTop: '1rem', color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, fontSize: '0.9rem' }}>
                                Explore <ArrowRight size={16} />
                            </div>
                        </Link>
                    ))}
                </div>
            </div>

            {/* Tech Stack */}
            <div style={{ textAlign: 'center', padding: '2rem 0' }}>
                <div style={{ display: 'flex', gap: '3rem', justifyContent: 'center', flexWrap: 'wrap', opacity: 0.7 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Zap size={18} /> FastAPI + LangChain
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Shield size={18} /> ChromaDB Vector Store
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Sparkles size={18} /> Groq LLM Inference
                    </div>
                </div>
            </div>
        </div>
    );
}
