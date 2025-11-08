import { useState, useRef, useEffect } from 'react';
import { queryService } from '../services/api';

export default function ChatInterface({ selectedDocumentId }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: input.trim(),
            timestamp: new Date(),
        };

        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setLoading(true);

        try {
            const response = await queryService.ask(input.trim(), selectedDocumentId);

            const assistantMessage = {
                id: Date.now() + 1,
                type: 'assistant',
                content: response.answer,
                isAnswerable: response.is_answerable,
                retrievedChunks: response.retrieved_chunks_count,
                tokensUsed: response.tokens_used,
                chunkIds: response.chunk_ids,
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            const errorMessage = {
                id: Date.now() + 1,
                type: 'error',
                content: error.response?.data?.detail || 'Error al procesar la pregunta',
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white rounded-lg shadow-md flex flex-col h-[600px]">
            <div className="p-4 border-b border-gray-200">
                <h2 className="text-2xl font-bold text-gray-800">Chat RAG</h2>
                {selectedDocumentId && (
                    <p className="text-sm text-gray-600 mt-1">
                        Consultando documento especifico
                    </p>
                )}
                {!selectedDocumentId && (
                    <p className="text-sm text-gray-600 mt-1">
                        Consultando todos los documentos
                    </p>
                )}
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && (
                    <div className="text-center text-gray-500 mt-8">
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
                                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                            />
                        </svg>
                        <p>Haz una pregunta sobre tus documentos</p>
                    </div>
                )}

                {messages.map((message) => (
                    <div
                        key={message.id}
                        className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-[80%] rounded-lg p-4 ${
                                message.type === 'user'
                                    ? 'bg-blue-600 text-white'
                                    : message.type === 'error'
                                    ? 'bg-red-50 text-red-800 border border-red-200'
                                    : 'bg-gray-100 text-gray-800'
                            }`}
                        >
                            <p className="whitespace-pre-wrap">{message.content}</p>

                            {message.type === 'assistant' && (
                                <div className="mt-2 pt-2 border-t border-gray-300 text-xs text-gray-600">
                                    <div className="flex items-center space-x-4">
                                        <span>
                                            {message.isAnswerable ? '✓ Respondible' : '⚠ No respondible'}
                                        </span>
                                        <span>📄 {message.retrievedChunks} chunks</span>
                                        <span>🔢 {message.tokensUsed} tokens</span>
                                    </div>
                                </div>
                            )}

                            <div className="mt-1 text-xs opacity-70">
                                {message.timestamp.toLocaleTimeString()}
                            </div>
                        </div>
                    </div>
                ))}

                {loading && (
                    <div className="flex justify-start">
                        <div className="bg-gray-100 rounded-lg p-4">
                            <div className="flex space-x-2">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></div>
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200">
                <div className="flex space-x-2">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Escribe tu pregunta..."
                        className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={loading}
                    />
                    <button
                        type="submit"
                        disabled={!input.trim() || loading}
                        className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                            !input.trim() || loading
                                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                                : 'bg-blue-600 text-white hover:bg-blue-700'
                        }`}
                    >
                        Enviar
                    </button>
                </div>
            </form>
        </div>
    );
}
