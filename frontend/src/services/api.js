const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
    const res = await fetch(`${BASE_URL}${path}`, options);
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        const err = new Error(error.detail || 'Request failed');
        err.response = { data: error };
        throw err;
    }
    return res.json();
}

export const documentService = {
    list: () => request('/documents/'),
    upload: (file) => {
        const form = new FormData();
        form.append('file', file);
        return request('/documents/upload', { method: 'POST', body: form });
    },
    delete: (id) => request(`/documents/${id}`, { method: 'DELETE' }),
};

export const queryService = {
    ask: (question, document_id = null) =>
        request('/query/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, document_id }),
        }),
};
