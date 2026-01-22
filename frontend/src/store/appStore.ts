import { create } from 'zustand';
import type { QueryResponse, DocumentInfo, EvaluationResult, ExperimentResult } from '../services/api';

interface AppState {
    darkMode: boolean;
    sidebarOpen: boolean;
    currentQuery: string;
    queryHistory: QueryResponse[];
    isQuerying: boolean;
    documents: DocumentInfo[];
    evaluations: EvaluationResult[];
    experiments: ExperimentResult[];

    toggleDarkMode: () => void;
    toggleSidebar: () => void;
    setCurrentQuery: (query: string) => void;
    addQueryToHistory: (response: QueryResponse) => void;
    setQuerying: (isQuerying: boolean) => void;
    setDocuments: (documents: DocumentInfo[]) => void;
    setEvaluations: (evaluations: EvaluationResult[]) => void;
}

export const useAppStore = create<AppState>((set) => ({
    darkMode: true,
    sidebarOpen: true,
    currentQuery: '',
    queryHistory: [],
    isQuerying: false,
    documents: [],
    evaluations: [],
    experiments: [],

    toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),
    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
    setCurrentQuery: (query) => set({ currentQuery: query }),
    addQueryToHistory: (response) => set((state) => ({
        queryHistory: [response, ...state.queryHistory].slice(0, 50),
    })),
    setQuerying: (isQuerying) => set({ isQuerying }),
    setDocuments: (documents) => set({ documents }),
    setEvaluations: (evaluations) => set({ evaluations }),
}));
