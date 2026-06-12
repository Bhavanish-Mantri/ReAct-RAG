document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const searchForm = document.getElementById('search-form');
    const queryInput = document.getElementById('query-input');
    const submitBtn = document.getElementById('submit-btn');
    const statusPanel = document.getElementById('status-panel');
    const geminiStatus = document.getElementById('gemini-status');
    const tmdbStatus = document.getElementById('tmdb-status');
    const apiAlert = document.getElementById('api-alert');
    
    const welcomeCard = document.getElementById('welcome-card');
    const loadingCard = document.getElementById('loading-card');
    const loadingStatus = document.getElementById('loading-status');
    const resultsContainer = document.getElementById('results-container');
    
    const finalAnswer = document.getElementById('final-answer');
    const moviesGrid = document.getElementById('movies-grid');
    const traceConsole = document.getElementById('trace-console');
    const tagButtons = document.querySelectorAll('.tag-btn');

    // Loader Messages to cycle through for active feel
    const loadingMessages = [
        "Initializing ReAct agent executor...",
        "Analyzing prompt and extracting constraints...",
        "Translating informal periods (e.g., '90s' to 1990-1999)...",
        "Formulating database search parameters...",
        "Executing TMDB database lookup tool...",
        "Analyzing search results against user constraints...",
        "Selecting best recommendation and composing reasoning..."
    ];
    let messageInterval = null;

    // 1. Check API Status on Load
    async function checkStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            
            // Gemini Status
            if (data.gemini_key_configured) {
                geminiStatus.className = 'status-badge connected';
                geminiStatus.innerHTML = '<span class="dot"></span> Gemini API: Ready';
                apiAlert.style.display = 'none';
            } else {
                geminiStatus.className = 'status-badge disconnected';
                geminiStatus.innerHTML = '<span class="dot"></span> Gemini API: Key Missing';
                apiAlert.style.display = 'flex';
            }
            
            // TMDB Status
            if (data.tmdb_key_configured) {
                tmdbStatus.className = 'status-badge connected';
                tmdbStatus.innerHTML = '<span class="dot"></span> DB: TMDB Live API';
            } else {
                tmdbStatus.className = 'status-badge connected';
                tmdbStatus.innerHTML = '<span class="dot"></span> DB: Mock Database';
                tmdbStatus.title = "No TMDB key found. Running with local mock database.";
            }
        } catch (err) {
            console.error('Failed to connect to API backend status endpoint:', err);
        }
    }
    
    checkStatus();

    // 2. Setup Suggestion Buttons
    tagButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const query = btn.getAttribute('data-query');
            queryInput.value = query;
            submitQuery(query);
        });
    });

    // 3. Form Submit Handler
    searchForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (query) {
            submitQuery(query);
        }
    });

    // 4. Submit Query Function
    async function submitQuery(query) {
        // Toggle States
        welcomeCard.style.display = 'none';
        resultsContainer.style.display = 'none';
        loadingCard.style.display = 'flex';
        submitBtn.disabled = true;
        
        // Cycle loading messages
        let messageIdx = 0;
        loadingStatus.innerText = loadingMessages[0];
        messageInterval = setInterval(() => {
            messageIdx = (messageIdx + 1) % loadingMessages.length;
            loadingStatus.innerText = loadingMessages[messageIdx];
        }, 3000);

        try {
            const res = await fetch('/api/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });

            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || 'Failed to execute recommendation.');
            }

            const result = await res.json();
            
            // Stop Loading and Show Output
            clearInterval(messageInterval);
            loadingCard.style.display = 'none';
            resultsContainer.style.display = 'flex';
            
            // Render Results
            renderResults(result);

        } catch (err) {
            clearInterval(messageInterval);
            loadingCard.style.display = 'none';
            welcomeCard.style.display = 'flex';
            alert(`Error: ${err.message}`);
        } finally {
            submitBtn.disabled = false;
        }
    }

    // 5. Render Output Data
    function renderResults(result) {
        // A. Final Answer
        finalAnswer.innerHTML = formatMarkdown(result.final_answer);
        
        // B. Clear grids
        moviesGrid.innerHTML = '';
        traceConsole.innerHTML = '';
        
        // C. Render Movie Cards
        if (result.movies && result.movies.length > 0) {
            result.movies.forEach(movie => {
                const card = document.createElement('div');
                card.className = 'movie-card glass';
                
                // Poster image fallback
                const posterUrl = movie.poster_path || 'https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop';
                
                // Rating format
                const rating = movie.rating ? parseFloat(movie.rating).toFixed(1) : 'N/A';
                
                // Certification class
                const certClass = movie.certification === 'R' ? 'tag-cert' : 'tag-genre';
                
                // Watch providers
                let providersHTML = '';
                if (movie.watch_providers && movie.watch_providers.length > 0) {
                    providersHTML = `
                        <div class="movie-providers-box">
                            <span class="providers-label">Streaming platforms</span>
                            <div class="providers-list">
                                ${movie.watch_providers.map(p => `<span class="provider-badge">${p}</span>`).join('')}
                            </div>
                        </div>
                    `;
                }

                card.innerHTML = `
                    <div class="movie-poster-wrapper">
                        <img src="${posterUrl}" alt="${movie.title}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1594909122845-11baa439b7bf?q=80&w=500&auto=format&fit=crop';">
                        <div class="movie-rating-badge">
                            <i class="fa-solid fa-star"></i> ${rating}
                        </div>
                    </div>
                    <div class="movie-details">
                        <div class="movie-title-row">
                            <h4 class="movie-title">${movie.title}</h4>
                            <span class="movie-year">${movie.year || ''}</span>
                        </div>
                        <div class="movie-meta-tags">
                            <span class="meta-tag ${certClass}">${movie.certification || 'N/A'}</span>
                            ${movie.genres ? movie.genres.slice(0, 2).map(g => `<span class="meta-tag tag-genre">${g}</span>`).join('') : ''}
                        </div>
                        <p class="movie-overview">${movie.overview || 'No overview available.'}</p>
                        ${providersHTML}
                    </div>
                `;
                moviesGrid.appendChild(card);
            });
        } else {
            moviesGrid.innerHTML = `
                <div class="no-movies glass" style="grid-column: 1/-1; padding: 2rem; text-align: center; color: var(--text-secondary);">
                    <i class="fa-solid fa-face-frown" style="font-size: 2rem; margin-bottom: 0.5rem; color: var(--text-muted);"></i>
                    <p>No structured movie details could be parsed from the agent's output. Please read the final response for instructions.</p>
                </div>
            `;
        }
        
        // D. Render ReAct steps
        if (result.steps && result.steps.length > 0) {
            result.steps.forEach((step, idx) => {
                const stepEl = document.createElement('div');
                stepEl.className = `trace-step step-${step.type}`;
                
                let iconClass = 'fa-brain';
                if (step.type === 'tool_call') iconClass = 'fa-terminal';
                if (step.type === 'observation') iconClass = 'fa-database';
                
                stepEl.innerHTML = `
                    <div class="step-header">
                        <i class="fa-solid ${iconClass} step-icon"></i>
                        <span class="step-title">Step ${idx + 1}: ${step.title}</span>
                    </div>
                    <div class="step-body">${escapeHTML(step.content)}</div>
                `;
                traceConsole.appendChild(stepEl);
            });
            
            // Auto scroll console to bottom
            setTimeout(() => {
                traceConsole.scrollTop = traceConsole.scrollHeight;
            }, 100);
        }
    }

    // Helpers
    function escapeHTML(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function formatMarkdown(text) {
        // Simple markdown parsing for bold text (**text**) and paragraph spacing
        let formatted = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
            
        // Convert double newlines to paragraphs
        const paragraphs = formatted.split(/\n\n+/);
        return paragraphs.map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
    }
});
