// PDF RAG Chatbot Client Application
const API_BASE_URL = 'http://127.0.0.1:8000';

// DOM Elements
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const fileDetails = document.getElementById('fileDetails');
const fileNameSpan = document.getElementById('fileName');
const fileSizeSpan = document.getElementById('fileSize');
const removeFileBtn = document.getElementById('removeFileBtn');
const progressBar = document.getElementById('progressBar');
const statusText = document.getElementById('statusText');

const docPulse = document.getElementById('docPulse');
const activeDocName = document.getElementById('activeDocName');
const clearChatBtn = document.getElementById('clearChatBtn');
const chatFeed = document.getElementById('chatFeed');
const welcomeContainer = document.getElementById('welcomeContainer');

const chatForm = document.getElementById('chatForm');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');

// Global State
let selectedFile = null;
let currentActiveDoc = null;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    setupUploadHandlers();
    setupChatHandlers();
});

// Setup File Upload Logic
function setupUploadHandlers() {
    // Dropzone Click
    dropzone.addEventListener('click', () => fileInput.click());

    // File Input Selection
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Drag and Drop
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    // Remove File click
    removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        resetUploadState();
    });
}

function handleFileSelect(file) {
    if (file.type !== 'application/pdf' && !file.name.endsWith('.pdf')) {
        alert('Please select a valid PDF file.');
        return;
    }

    selectedFile = file;
    fileNameSpan.textContent = file.name;
    fileSizeSpan.textContent = formatBytes(file.size);
    
    // UI toggle
    dropzone.style.display = 'none';
    fileDetails.style.display = 'block';
    progressBar.style.width = '0%';
    
    uploadFile(file);
}

function uploadFile(file) {
    statusText.textContent = 'Uploading...';
    progressBar.style.width = '10%';

    const formData = new FormData();
    formData.append('file', file);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE_URL}/upload`, true);

    // Track Upload Progress
    xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
            // Map 0-100 progress to 10% - 90% space (remaining is backend parsing time)
            const percentComplete = Math.round((e.loaded / e.total) * 80) + 10;
            progressBar.style.width = `${percentComplete}%`;
        }
    };

    xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
            try {
                const response = JSON.parse(xhr.responseText);
                progressBar.style.width = '100%';
                statusText.textContent = 'PDF indexed successfully!';
                statusText.style.color = 'var(--color-success)';
                
                // Set Active Document State
                currentActiveDoc = response.filename;
                activeDocName.textContent = response.filename;
                docPulse.className = 'pulse-indicator online';
                
                // Enable Chat Inputs
                userInput.disabled = false;
                sendBtn.disabled = false;
                userInput.placeholder = "Ask a question about this document...";
                userInput.focus();
            } catch (err) {
                handleUploadFailure('Invalid server response format.');
            }
        } else {
            let errMsg = 'Failed to index document.';
            try {
                const errRes = JSON.parse(xhr.responseText);
                if (errRes.detail) errMsg = errRes.detail;
            } catch(e) {}
            handleUploadFailure(errMsg);
        }
    };

    xhr.onerror = () => {
        handleUploadFailure('Network connection error.');
    };

    xhr.send(formData);
}

function handleUploadFailure(message) {
    statusText.textContent = `Error: ${message}`;
    statusText.style.color = 'var(--color-danger)';
    progressBar.style.width = '100%';
    progressBar.style.backgroundColor = 'var(--color-danger)';
    
    // Reset Chat State
    currentActiveDoc = null;
    activeDocName.textContent = "No document loaded";
    docPulse.className = 'pulse-indicator offline';
    userInput.disabled = true;
    sendBtn.disabled = true;
    userInput.placeholder = "Upload a PDF first to start chatting...";
}

function resetUploadState() {
    selectedFile = null;
    fileInput.value = '';
    dropzone.style.display = 'block';
    fileDetails.style.display = 'none';
    statusText.style.color = 'var(--text-muted)';
    progressBar.style.backgroundColor = '';
    
    // Reset active document
    currentActiveDoc = null;
    activeDocName.textContent = "No document loaded";
    docPulse.className = 'pulse-indicator offline';
    userInput.disabled = true;
    sendBtn.disabled = true;
    userInput.placeholder = "Upload a PDF first to start chatting...";
}

// Setup Chat Logic
function setupChatHandlers() {
    chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = userInput.value.trim();
        if (!query) return;
        
        // Clear input
        userInput.value = '';
        
        // Hide welcome board on first message
        if (welcomeContainer) {
            welcomeContainer.remove();
        }

        // 1. Add User Message
        appendMessage('user', query);
        
        // 2. Add Typing Bubble
        const typingId = appendTypingIndicator();
        chatFeed.scrollTop = chatFeed.scrollHeight;

        // 3. Send API Call
        fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: query })
        })
        .then(res => {
            if (!res.ok) {
                return res.json().then(errData => {
                    throw new Error(errData.detail || 'Server returned an error.');
                });
            }
            return res.json();
        })
        .then(data => {
            removeTypingIndicator(typingId);
            appendMessage('bot', data.answer, data.sources);
        })
        .catch(err => {
            removeTypingIndicator(typingId);
            appendMessage('bot', `Error: ${err.message}. Make sure the server is running and GROQ_API_KEY is configured in your .env.`);
        })
        .finally(() => {
            chatFeed.scrollTop = chatFeed.scrollHeight;
        });
    });

    // Clear Chat click
    clearChatBtn.addEventListener('click', () => {
        if (confirm('Clear entire chat conversation history?')) {
            chatFeed.innerHTML = '';
            appendWelcomeMessage();
        }
    });
}

function appendMessage(sender, text, sources = []) {
    const chatRow = document.createElement('div');
    chatRow.className = `chat-row ${sender}-row`;

    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.innerHTML = sender === 'user' ? '<i class="fa-solid fa-user"></i>' : '<i class="fa-solid fa-robot"></i>';

    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = text;
    wrapper.appendChild(bubble);

    // If there are sources, format them beautifully
    if (sources && sources.length > 0) {
        const sourcesId = `sources-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const sourcesContainer = document.createElement('div');
        sourcesContainer.className = 'sources-container';
        
        const header = document.createElement('div');
        header.className = 'sources-header';
        header.innerHTML = `<i class="fa-solid fa-quote-left"></i> Source Citations (${sources.length})`;
        
        const list = document.createElement('div');
        list.className = 'sources-list';
        list.id = sourcesId;
        list.style.display = 'none'; // Collapsed by default
        
        header.addEventListener('click', () => {
            const isCollapsed = list.style.display === 'none';
            list.style.display = isCollapsed ? 'flex' : 'none';
            header.innerHTML = isCollapsed 
                ? `<i class="fa-solid fa-angle-down"></i> Source Citations (${sources.length})`
                : `<i class="fa-solid fa-quote-left"></i> Source Citations (${sources.length})`;
        });

        sources.forEach((doc) => {
            const card = document.createElement('div');
            card.className = 'source-card';
            
            card.innerHTML = `
                <div class="source-card-header">
                    <span class="source-page">Page ${doc.page}</span>
                    <div class="source-metrics">
                        <span class="metric" title="Similarity Score"><i class="fa-solid fa-gauge-high"></i> Sim: ${doc.similarity_score.toFixed(4)}</span>
                        <span class="metric" title="Cosine Distance"><i class="fa-solid fa-ruler-horizontal"></i> Dist: ${doc.cosine_distance.toFixed(4)}</span>
                    </div>
                </div>
                <div class="source-text">"${doc.text}"</div>
            `;
            list.appendChild(card);
        });

        sourcesContainer.appendChild(header);
        sourcesContainer.appendChild(list);
        wrapper.appendChild(sourcesContainer);
    }

    chatRow.appendChild(avatar);
    chatRow.appendChild(wrapper);
    chatFeed.appendChild(chatRow);
    
    // Smooth scroll to bottom
    chatFeed.scrollTop = chatFeed.scrollHeight;
}

function appendTypingIndicator() {
    const id = `typing-${Date.now()}`;
    const chatRow = document.createElement('div');
    chatRow.className = 'chat-row bot-row';
    chatRow.id = id;

    const avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.innerHTML = '<i class="fa-solid fa-robot"></i>';

    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = `
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    `;
    
    bubble.appendChild(indicator);
    wrapper.appendChild(bubble);
    chatRow.appendChild(avatar);
    chatRow.appendChild(wrapper);
    chatFeed.appendChild(chatRow);
    
    return id;
}

function removeTypingIndicator(id) {
    const indicator = document.getElementById(id);
    if (indicator) {
        indicator.remove();
    }
}

function appendWelcomeMessage() {
    const welcome = document.createElement('div');
    welcome.className = 'welcome-container';
    welcome.id = 'welcomeContainer';
    welcome.innerHTML = `
        <div class="welcome-card">
            <div class="avatar-large">
                <i class="fa-solid fa-robot"></i>
            </div>
            <h1>Welcome to PDF RAG Agent</h1>
            <p>Upload a document on the left panel. Once indexed into the local FAISS store, you can query it here. The chatbot will search the document and cite pages and similarity scores.</p>
            
            <div class="feature-highlights">
                <div class="highlight-item">
                    <i class="fa-solid fa-magnifying-glass-location"></i>
                    <h3>Semantic Retrieval</h3>
                    <p>Finds accurate answers using sentence embedding models.</p>
                </div>
                <div class="highlight-item">
                    <i class="fa-solid fa-list-ol"></i>
                    <h3>Page Citations</h3>
                    <p>Cites the exact pages where the information is written.</p>
                </div>
                <div class="highlight-item">
                    <i class="fa-solid fa-chart-line"></i>
                    <h3>Similarity Scores</h3>
                    <p>Shows exact cosine similarity metrics and distances.</p>
                </div>
            </div>
        </div>
    `;
    chatFeed.appendChild(welcome);
}

// Utilities
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
