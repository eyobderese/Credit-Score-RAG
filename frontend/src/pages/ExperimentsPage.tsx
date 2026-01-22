import React, { useState } from 'react';
import { FlaskConical, Play } from 'lucide-react';
import { experimentsAPI } from '../services/api';

export default function ExperimentsPage() {
    const [running, setRunning] = useState(false);
    const [result, setResult] = useState<any>(null);

    const runChunkSizeAblation = async () => {
        setRunning(true);
        try {
            const data = await experimentsAPI.ablationChunkSize('500,1000,2000', 3);
            setResult(data);
        } catch (err: any) {
            alert('Failed: ' + (err.response?.data?.detail || err.message));
        } finally {
            setRunning(false);
        }
    };

    const runTopKAblation = async () => {
        setRunning(true);
        try {
            const data = await experimentsAPI.ablationTopK('3,5,7,10', 3);
            setResult(data);
        } catch (err: any) {
            alert('Failed: ' + (err.response?.data?.detail || err.message));
        } finally {
            setRunning(false);
        }
    };

    return (
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
            <h1 className="page-title">
                <FlaskConical style={{ display: 'inline', verticalAlign: 'middle', marginRight: '0.5rem' }} />
                Experiments
            </h1>
            <p className="page-description">Run ablation studies and compare RAG configurations</p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
                <div className="card">
                    <h3 className="card-title">Chunk Size Ablation</h3>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.875rem' }}>
                        Test different chunk sizes: 500, 1000, 2000 characters
                    </p>
                    <button className="btn btn-primary" style={{ width: '100%' }} onClick={runChunkSizeAblation} disabled={running}>
                        <Play size={16} /> Run Experiment
                    </button>
                </div>

                <div className="card">
                    <h3 className="card-title">Top-K Ablation</h3>
                    <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.875rem' }}>
                        Test retrieval counts: 3, 5, 7, 10 chunks
                    </p>
                    <button className="btn btn-primary" style={{ width: '100%' }} onClick={runTopKAblation} disabled={running}>
                        <Play size={16} /> Run Experiment
                    </button>
                </div>
            </div>

            {result && (
                <div className="card">
                    <h3 className="card-title">Result: {result.ablation_type}</h3>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <div style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Best Configuration:</div>
                        <div style={{ fontSize: '2rem', color: 'var(--success)' }}>
                            {result.ablation_type === 'chunk_size' ? `${result.best_value} characters` : `Top-${result.best_value}`}
                        </div>
                        <div style={{ color: 'var(--text-secondary)' }}>
                            Accuracy: {(result.best_accuracy * 100).toFixed(1)}%
                        </div>
                    </div>

                    <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: 8 }}>
                        <div style={{ fontWeight: 600, marginBottom: '0.75rem' }}>All Results:</div>
                        {result.results.map((r: any, i: number) => (
                            <div key={i} className="list-item" style={{ marginBottom: '0.5rem' }}>
                                <span>{result.ablation_type === 'chunk_size' ? `${r.size} chars` : `Top-${r.top_k}`}</span>
                                <span style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>
                                    {(r.accuracy * 100).toFixed(1)}%
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
