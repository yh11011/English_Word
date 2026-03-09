// Extracted JS helpers from templates/vocabmaster.html
// This file is a compacted version containing API helpers that include CSRF token header

function getCsrfToken(){
    const el = document.querySelector('meta[name="csrf-token"]');
    return el ? el.getAttribute('content') : null;
}

async function apiFetch(url, opts){
    opts = opts || {};
    opts.headers = opts.headers || {};
    // If not using Bearer token, attach CSRF token for browser flows
    if(!opts.headers['Authorization']){
        const token = getCsrfToken();
        if(token) opts.headers['X-CSRF-Token'] = token;
        opts.credentials = 'same-origin';
    }
    const res = await fetch(url, opts);
    return res.json();
}

async function apiGet(path){ return apiFetch(path, { method: 'GET' }); }
async function apiPost(path, body){ return apiFetch(path, { method:'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) }); }
async function apiDelete(path){ return apiFetch(path, { method:'DELETE' }); }
async function apiPut(path, body){ return apiFetch(path, { method:'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) }); }

// Small helper used by the UI; original template JS is still present in templates/ and will work with these helpers.
window.vm_api = { get: apiGet, post: apiPost, delete: apiDelete, put: apiPut };
