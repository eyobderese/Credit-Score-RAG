import React, { useState, useEffect } from 'react';
import { PlayCircle } from 'lucide-react';
import { evaluationAPI } from '../services/api';
import type { EvaluationResult } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function EvaluationPage() {
    const [evaluations, setEvaluations] = useState<EvaluationResult[]>([]);
    const [running, setRunning] = useState(false);
    const [latest, setLatest] = useState<EvaluationResult | null>(null);

    useEffect(() => {
        evaluationAPI.listResults().then((data) => {
            setEvaluations(data);
            if (data.length > 0) setLatest(data[0]);
        }).catch(console.error);
    }, []);

    const runEvaluation = async () => {
        setRunning(true);
        try {
            const result = await evaluationAPI.runEvaluation({ sample_size: 5 });
            setLatest(result);
            setEvaluations((prev) => [result, ...prev]);
            alert('Evaluation completed!');
        } catch (err: any) {
            alert('Failed: ' + (err.response?.data?.detail || err.message));
        } finally {
            setRunning(false);
        }
    };

    const getChartData = () => {
        if (!latest) return [];
        const m = latest.metrics;
        return [
            { name: 'Answer Accuracy', value: m.answer_accuracy * 100 },
            { name: 'Source Accuracy', value: m.source_accuracy * 100 },
            { name: 'Citation Coverage', value: m.citation_coverage * 100 },
            { name: 'Hallucination Rate', value: m.hallucination_rate * 100 },
        ];
    };

    return (
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
            <h1 className="page-title">Evaluation Dashboard</h1>
            <p className="page-description">Run evaluations and track RAG system performance</p>

            <div className="card">
                <h2 className="card-title">Run Evaluation</h2>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                    Test the RAG system on sample questions and measure performance metrics.
                </p>
                <button className="btn btn-primary" onClick={runEvaluation} disabled={running}>
                    <PlayCircle size={18} />
                    {running ? 'Running...' : 'Run Evaluation'}
                </button>
            </div>

            {latest && (
                <div className="card">
                    <h2 className="card-title">Latest Results</h2>

                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="stat-value" style={{ color: 'var(--success)' }}>
                                {(latest.metrics.answer_accuracy * 100).toFixed(1)}%
                            </div>
                            <div className="stat-label">Answer Accuracy</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value" style={{ color: 'var(--info)' }}>
                                {(latest.metrics.source_accuracy * 100).toFixed(1)}%
                            </div>
                            <div className="stat-label">Source Accuracy</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value" style={{ color: 'var(--warning)' }}>
                                {(latest.metrics.hallucination_rate * 100).toFixed(1)}%
                            </div>
                            <div className="stat-label">Hallucination Rate</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">
                                {latest.metrics.avg_response_time_ms.toFixed(0)}ms
                            </div>
                            <div className="stat-label">Avg Response Time</div>
                        </div>
                    </div>

                    <div style={{ height: 300, marginTop: '2rem' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={getChartData()}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                                <YAxis />
                                <Tooltip />
                                <Bar dataKey="value" fill="var(--accent-primary)" radius={[4, 4, 0, 0]} />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            <div className="card">
                <h3 className="card-title">Evaluation History ({evaluations.length})</h3>
                {evaluations.length === 0 ? (
                    <p style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>
                        No evaluations yet. Run one to see results!
                    </p>
                ) : (
                    evaluations.map((evalItem) => (
                        <div key={evalItem.id} className="list-item">
                            <div>
                                <div style={{ fontWeight: 600 }}>Evaluation {evalItem.id}</div>
                                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                    {new Date(evalItem.run_at).toLocaleString()}
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '1rem', fontSize: '0.875rem' }}>
                                <span>Accuracy: {(evalItem.metrics.answer_accuracy * 100).toFixed(1)}%</span>
                                <span>Hallucination: {(evalItem.metrics.hallucination_rate * 100).toFixed(1)}%</span>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
