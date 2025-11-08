import { useState, useEffect } from 'react';
import { documentService } from '../services/api';

export default function DocumentList({ onSelectDocument, refreshTrigger }) {
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedId, setSelectedId] = useState(null);

    const fetchDocuments = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await documentService.list();
            setDocuments(data.documents || []);
        } catch (err) {
            setError('Error al cargar documentos');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDocuments();
    }, [refreshTrigger]);

    const handleSelectDocument = (doc) => {
        const newId = selectedId === doc.id ? null : doc.id;
        setSelectedId(newId);
        onSelectDocument(newId);
    };

    const handleDelete = async (e, docId) => {
        e.stopPropagation();
        if (!confirm('¿Seguro que quieres eliminar este documento?')) return;

        try {
            await documentService.delete(docId);
            fetchDocuments();
            if (selectedId === docId) {
                setSelectedId(null);
                onSelectDocument(null);
            }
        } catch (err) {
            alert('Error al eliminar documento');
        }
    };

    const getStatusBadge = (status) => {
        const badges = {
            ready: 'bg-green-100 text-green-800',
            processing: 'bg-yellow-100 text-yellow-800',
            failed: 'bg-red-100 text-red-800',
        };
        return badges[status] || 'bg-gray-100 text-gray-800';
    };

    const getStatusText = (status) => {
        const texts = {
            ready: 'Listo',
            processing: 'Procesando',
            failed: 'Error',
        };
        return texts[status] || status;
    };

    if (loading) {
        return (
            <div className="bg-white rounded-lg shadow-md p-6">
                <h2 className="text-2xl font-bold mb-4 text-gray-800">Documentos</h2>
                <div className="flex justify-center items-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-800">Documentos</h2>
                <button
                    onClick={fetchDocuments}
                    className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                    Actualizar
                </button>
            </div>

            {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-600">{error}</p>
                </div>
            )}

            {documents.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                    <svg
                        className="mx-auto h-12 w-12 text-gray-400 mb-4"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                    </svg>
                    <p>No hay documentos subidos</p>
                </div>
            ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                    {documents.map((doc) => (
                        <div
                            key={doc.id}
                            onClick={() => handleSelectDocument(doc)}
                            className={`p-4 border rounded-lg cursor-pointer transition-all ${
                                selectedId === doc.id
                                    ? 'border-blue-500 bg-blue-50'
                                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                            }`}
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center space-x-2 mb-2">
                                        <svg
                                            className="h-5 w-5 text-red-500 flex-shrink-0"
                                            fill="currentColor"
                                            viewBox="0 0 20 20"
                                        >
                                            <path
                                                fillRule="evenodd"
                                                d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"
                                                clipRule="evenodd"
                                            />
                                        </svg>
                                        <h3 className="text-sm font-medium text-gray-900 truncate">
                                            {doc.filename}
                                        </h3>
                                    </div>

                                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                                        <span
                                            className={`px-2 py-1 rounded-full ${getStatusBadge(
                                                doc.status
                                            )}`}
                                        >
                                            {getStatusText(doc.status)}
                                        </span>
                                        {doc.total_pages && (
                                            <span>{doc.total_pages} paginas</span>
                                        )}
                                        {doc.total_chunks && (
                                            <span>{doc.total_chunks} chunks</span>
                                        )}
                                    </div>
                                </div>

                                <button
                                    onClick={(e) => handleDelete(e, doc.id)}
                                    className="ml-2 text-gray-400 hover:text-red-600 transition-colors"
                                    title="Eliminar documento"
                                >
                                    <svg
                                        className="h-5 w-5"
                                        fill="none"
                                        viewBox="0 0 24 24"
                                        stroke="currentColor"
                                    >
                                        <path
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                            strokeWidth={2}
                                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                        />
                                    </svg>
                                </button>
                            </div>

                            {selectedId === doc.id && (
                                <div className="mt-2 pt-2 border-t border-blue-200">
                                    <p className="text-xs text-blue-600">
                                        ✓ Chat filtrando por este documento
                                    </p>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
