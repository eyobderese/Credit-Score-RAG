import React, { useState, useEffect, useRef } from 'react';
import { Upload, FileText, Trash2, RefreshCw } from 'lucide-react';
import { documentsAPI } from '../services/api';
import type { DocumentInfo, DocumentStats } from '../services/api';

export default function DocumentsPage() {
    const [documents, setDocuments] = useState<DocumentInfo[]>([]);
    const [stats, setStats] = useState<DocumentStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const loadData = async () => {
        setLoading(true);
        try {
            const [docsRes, statsRes] = await Promise.all([
                documentsAPI.listDocuments(),
                documentsAPI.getStats()
            ]);
            setDocuments(docsRes.documents);
            setStats(statsRes);
        } catch (err) {
            console.error('Failed to load documents:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files?.length) return;

        setUploading(true);
        try {
            for (const file of Array.from(files)) {
                await documentsAPI.uploadDocument(file);
            }
            await loadData();
            alert('Documents uploaded!');
        } catch (err: any) {
            alert('Upload failed: ' + (err.response?.data?.detail || err.message));
        } finally {
            setUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm('Delete this document?')) return;
        try {
            await documentsAPI.deleteDocument(id);
            await loadData();
        } catch (err) {
            alert('Delete failed');
        }
    };

    return (
        <div style={{ maxWidth: 1000, margin: '0 auto' }}>
            <h1 className="page-title">Document Management</h1>
            <p className="page-description">Upload and manage credit policy documents</p>

            {stats && (
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-value">{stats.total_documents}</div>
                        <div className="stat-label">Documents</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{stats.total_chunks}</div>
                        <div className="stat-label">Chunks</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{(stats.total_characters / 1000).toFixed(1)}K</div>
                        <div className="stat-label">Characters</div>
                    </div>
                </div>
            )}

            <div className="card" style={{ textAlign: 'center' }}>
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.md,.txt"
                    multiple
                    onChange={handleUpload}
                    style={{ display: 'none' }}
                />
                <Upload size={40} style={{ color: 'var(--accent-primary)', marginBottom: '1rem' }} />
                <h3 style={{ marginBottom: '0.5rem' }}>Upload Documents</h3>
                <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>Supported: PDF, Markdown, Text</p>
                <button
                    className="btn btn-primary"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                >
                    {uploading ? 'Uploading...' : 'Choose Files'}
                </button>
            </div>

            <div className="card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h2 className="card-title" style={{ margin: 0 }}>Documents ({documents.length})</h2>
                    <button className="btn btn-secondary" onClick={loadData} disabled={loading}>
                        <RefreshCw size={16} /> Refresh
                    </button>
                </div>

                {loading ? (
                    <p style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>Loading...</p>
                ) : documents.length === 0 ? (
                    <p style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No documents yet. Upload some!</p>
                ) : (
                    documents.map((doc) => (
                        <div key={doc.id} className="list-item">
                            <div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                                    <FileText size={18} style={{ color: 'var(--accent-primary)' }} />
                                    <span style={{ fontWeight: 600 }}>{doc.filename}</span>
                                </div>
                                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                                    {doc.chunk_count} chunks • {(doc.total_characters / 1000).toFixed(1)}K chars
                                </div>
                            </div>
                            <button
                                onClick={() => handleDelete(doc.id)}
                                style={{
                                    padding: '0.5rem',
                                    background: 'transparent',
                                    border: '1px solid var(--error)',
                                    borderRadius: 6,
                                    color: 'var(--error)',
                                    cursor: 'pointer'
                                }}
                            >
                                <Trash2 size={16} />
                            </button>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
