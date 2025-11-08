import { useState } from 'react';
import DocumentUpload from './components/DocumentUpload';
import DocumentList from './components/DocumentList';
import ChatInterface from './components/ChatInterface';

function App() {
    const [selectedDocumentId, setSelectedDocumentId] = useState(null);
    const [refreshTrigger, setRefreshTrigger] = useState(0);

    const handleUploadSuccess = (document) => {
        setRefreshTrigger((prev) => prev + 1);
    };

    const handleSelectDocument = (documentId) => {
        setSelectedDocumentId(documentId);
    };

    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-white shadow-sm">
                <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between">
                        <h1 className="text-3xl font-bold text-gray-900">
                            Sistema RAG
                        </h1>
                        <div className="flex items-center space-x-2">
                            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                            <span className="text-sm text-gray-600">Conectado</span>
                        </div>
                    </div>
                    <p className="mt-1 text-sm text-gray-600">
                        Recuperacion y Generacion Aumentada para documentos PDF
                    </p>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-1 space-y-6">
                        <DocumentUpload onUploadSuccess={handleUploadSuccess} />
                        <DocumentList
                            onSelectDocument={handleSelectDocument}
                            refreshTrigger={refreshTrigger}
                        />
                    </div>

                    <div className="lg:col-span-2">
                        <ChatInterface selectedDocumentId={selectedDocumentId} />
                    </div>
                </div>
            </main>

            <footer className="bg-white border-t border-gray-200 mt-12">
                <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
                    <p className="text-center text-sm text-gray-500">
                        Sistema RAG - Powered by OpenAI & FastAPI
                    </p>
                </div>
            </footer>
        </div>
    );
}

export default App;
