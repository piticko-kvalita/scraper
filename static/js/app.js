// AI Training Materials Scraper - Frontend JavaScript

// Load statistics on page load and setup event listeners
document.addEventListener('DOMContentLoaded', () => {
    loadStatistics();
    loadContent();
    checkAIStatus();
    checkAutoGatherStatus();
    
    // Allow Enter key to submit URL
    document.getElementById('url-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            scrapeUrl();
        }
    });
    
    // Allow Enter key for AI suggestions
    const aiTopicInput = document.getElementById('ai-topic-input');
    if (aiTopicInput) {
        aiTopicInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                suggestAIUrls();
            }
        });
    }
});

// Load and display statistics
async function loadStatistics() {
    try {
        const response = await fetch('/api/statistics');
        const data = await response.json();
        
        document.getElementById('total-items').textContent = data.total_items || 0;
        document.getElementById('total-words').textContent = (data.total_words || 0).toLocaleString();
        document.getElementById('content-types').textContent = Object.keys(data.content_types || {}).length;
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Load and display content
async function loadContent() {
    const contentList = document.getElementById('content-list');
    contentList.innerHTML = '<div class="loading">Loading content...</div>';
    
    try {
        const response = await fetch('/api/content');
        const data = await response.json();
        
        if (data.content && data.content.length > 0) {
            displayContent(data.content);
        } else {
            contentList.innerHTML = `
                <div class="empty-state">
                    <h3>No content yet</h3>
                    <p>Start by scraping some URLs above</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading content:', error);
        showStatus('Error loading content', 'error');
        contentList.innerHTML = '<div class="empty-state">Error loading content</div>';
    }
}

// Display content items
function displayContent(content) {
    const contentList = document.getElementById('content-list');
    
    contentList.innerHTML = content.map(item => `
        <div class="content-item" onclick="viewContent(${item.id})">
            <h3>${escapeHtml(item.title || 'Untitled')}</h3>
            <div class="content-meta">
                <span class="badge ${item.content_type}">${item.content_type || 'general'}</span>
                <span>${item.word_count || 0} words</span>
                <span>${formatDate(item.scraped_at)}</span>
            </div>
            <div class="content-preview">
                ${escapeHtml(item.content || 'No preview available').substring(0, 200)}...
            </div>
            <div class="content-actions" onclick="event.stopPropagation();">
                <button class="btn btn-secondary" onclick="viewContent(${item.id})">View</button>
                <button class="btn btn-danger" onclick="deleteContent(${item.id})">Delete</button>
            </div>
        </div>
    `).join('');
}

// Scrape a single URL
async function scrapeUrl() {
    const urlInput = document.getElementById('url-input');
    const url = urlInput.value.trim();
    
    if (!url) {
        showStatus('Please enter a URL', 'error');
        return;
    }
    
    showStatus('Scraping...', 'info');
    
    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus(data.message, 'success');
            urlInput.value = '';
            loadStatistics();
            loadContent();
        } else {
            showStatus(data.message, 'error');
        }
    } catch (error) {
        console.error('Error scraping URL:', error);
        showStatus('Error scraping URL', 'error');
    }
}

// Scrape default sources
async function scrapeDefaults() {
    const defaultUrls = [
        'https://en.wikipedia.org/wiki/Artificial_intelligence',
        'https://en.wikipedia.org/wiki/Machine_learning',
        'https://en.wikipedia.org/wiki/Deep_learning'
    ];
    
    showStatus('Scraping default sources... This may take a moment.', 'info');
    
    try {
        const response = await fetch('/api/scrape-multiple', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ urls: defaultUrls }),
        });
        
        const data = await response.json();
        const successCount = data.results.filter(r => r.success).length;
        
        showStatus(`Scraped ${successCount} of ${defaultUrls.length} URLs`, 'success');
        loadStatistics();
        loadContent();
    } catch (error) {
        console.error('Error scraping defaults:', error);
        showStatus('Error scraping default sources', 'error');
    }
}

// Show bulk input
function showBulkInput() {
    const bulkInput = document.getElementById('bulk-input');
    bulkInput.style.display = bulkInput.style.display === 'none' ? 'block' : 'none';
}

// Scrape multiple URLs from bulk input
async function scrapeBulk() {
    const bulkUrls = document.getElementById('bulk-urls').value;
    const urls = bulkUrls.split('\n').map(u => u.trim()).filter(u => u);
    
    if (urls.length === 0) {
        showStatus('Please enter at least one URL', 'error');
        return;
    }
    
    showStatus(`Scraping ${urls.length} URLs... This may take a moment.`, 'info');
    
    try {
        const response = await fetch('/api/scrape-multiple', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ urls }),
        });
        
        const data = await response.json();
        const successCount = data.results.filter(r => r.success).length;
        
        showStatus(`Successfully scraped ${successCount} of ${urls.length} URLs`, 'success');
        document.getElementById('bulk-urls').value = '';
        loadStatistics();
        loadContent();
    } catch (error) {
        console.error('Error scraping bulk URLs:', error);
        showStatus('Error scraping URLs', 'error');
    }
}

// View content details
async function viewContent(id) {
    try {
        const response = await fetch(`/api/content/${id}`);
        const data = await response.json();
        
        if (data.content) {
            const content = data.content;
            document.getElementById('modal-title').textContent = content.title || 'Untitled';
            document.getElementById('modal-type').textContent = content.content_type || 'general';
            document.getElementById('modal-type').className = `badge ${content.content_type}`;
            document.getElementById('modal-words').textContent = `${content.word_count || 0} words`;
            document.getElementById('modal-date').textContent = formatDate(content.scraped_at);
            document.getElementById('modal-url-link').href = content.url;
            document.getElementById('modal-url-link').textContent = content.url;
            document.getElementById('modal-content').textContent = content.content || 'No content available';
            
            document.getElementById('detail-modal').style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading content details:', error);
        showStatus('Error loading content details', 'error');
    }
}

// Close modal
function closeModal() {
    document.getElementById('detail-modal').style.display = 'none';
}

// Close modal on outside click
window.onclick = function(event) {
    const modal = document.getElementById('detail-modal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

// Delete content
async function deleteContent(id) {
    if (!confirm('Are you sure you want to delete this content?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/content/${id}`, {
            method: 'DELETE',
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus('Content deleted', 'success');
            loadStatistics();
            loadContent();
        } else {
            showStatus('Error deleting content', 'error');
        }
    } catch (error) {
        console.error('Error deleting content:', error);
        showStatus('Error deleting content', 'error');
    }
}

// Refresh content
function refreshContent() {
    loadStatistics();
    loadContent();
    showStatus('Content refreshed', 'success');
}

// Export data
function exportData() {
    window.location.href = '/api/export';
    showStatus('Exporting data...', 'success');
}

// Show status message
function showStatus(message, type) {
    const statusDiv = document.getElementById('scrape-status');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
    statusDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 5000);
}

// Utility: Format date
function formatDate(dateString) {
    if (!dateString) return 'Unknown date';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Check AI status
async function checkAIStatus() {
    try {
        const response = await fetch('/api/ai/status');
        const data = await response.json();
        
        if (data.configured && data.enabled) {
            document.getElementById('ai-status-card').style.display = 'block';
            // Show AI features button
            const quickActions = document.querySelector('.quick-actions');
            if (!document.getElementById('ai-features-btn')) {
                const btn = document.createElement('button');
                btn.id = 'ai-features-btn';
                btn.className = 'btn btn-success';
                btn.textContent = '✨ AI Features';
                btn.onclick = showAIFeatures;
                quickActions.appendChild(btn);
            }
        }
    } catch (error) {
        console.error('Error checking AI status:', error);
    }
}

// Show AI features panel
function showAIFeatures() {
    const panel = document.getElementById('ai-features-panel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

// Show auto-gather panel
function showAutoGather() {
    const panel = document.getElementById('auto-gather-panel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}

// Check auto-gather status
async function checkAutoGatherStatus() {
    try {
        const response = await fetch('/api/auto-gather/status');
        const data = await response.json();
        
        if (data.is_running) {
            document.getElementById('auto-status-text').textContent = '▶️ Running';
            document.getElementById('auto-status-text').className = 'status-badge success';
            document.getElementById('start-auto-btn').disabled = true;
            document.getElementById('stop-auto-btn').disabled = false;
        } else {
            document.getElementById('auto-status-text').textContent = '⏸️ Stopped';
            document.getElementById('auto-status-text').className = 'status-badge';
            document.getElementById('start-auto-btn').disabled = false;
            document.getElementById('stop-auto-btn').disabled = true;
        }
        
        document.getElementById('auto-sources-count').textContent = `${data.sources_count} sources`;
    } catch (error) {
        console.error('Error checking auto-gather status:', error);
    }
}

// Start auto-gathering
async function startAutoGather() {
    try {
        const response = await fetch('/api/auto-gather/start', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showAutoStatus(data.message, 'success');
            checkAutoGatherStatus();
        } else {
            showAutoStatus(data.message, 'error');
        }
    } catch (error) {
        console.error('Error starting auto-gather:', error);
        showAutoStatus('Error starting auto-gather', 'error');
    }
}

// Stop auto-gathering
async function stopAutoGather() {
    try {
        const response = await fetch('/api/auto-gather/stop', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showAutoStatus(data.message, 'success');
            checkAutoGatherStatus();
        } else {
            showAutoStatus(data.message, 'error');
        }
    } catch (error) {
        console.error('Error stopping auto-gather:', error);
        showAutoStatus('Error stopping auto-gather', 'error');
    }
}

// Manually trigger auto-gathering
async function scrapeNow() {
    showAutoStatus('Scraping...', 'info');
    
    try {
        const response = await fetch('/api/auto-gather/scrape-now', { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            showAutoStatus(`Scraped ${data.scraped} items (${data.filtered} filtered)`, 'success');
            loadStatistics();
            loadContent();
        } else {
            showAutoStatus('Error scraping', 'error');
        }
    } catch (error) {
        console.error('Error in manual scrape:', error);
        showAutoStatus('Error scraping', 'error');
    }
}

// Show auto-gather status message
function showAutoStatus(message, type) {
    const statusDiv = document.getElementById('auto-status-message');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
    statusDiv.style.display = 'block';
    
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 5000);
}

// AI-powered URL suggestions
async function suggestAIUrls() {
    const topic = document.getElementById('ai-topic-input').value.trim();
    
    if (!topic) {
        showStatus('Please enter a topic', 'error');
        return;
    }
    
    const suggestionsDiv = document.getElementById('ai-suggestions');
    suggestionsDiv.innerHTML = '<div class="loading">AI is finding relevant URLs...</div>';
    
    try {
        const response = await fetch('/api/ai/suggest-urls', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ topic, count: 10 }),
        });
        
        const data = await response.json();
        
        if (data.success && data.urls && data.urls.length > 0) {
            let html = '<h4>Suggested URLs:</h4><div class="ai-url-list">';
            data.urls.forEach(url => {
                html += `
                    <div class="ai-url-item">
                        <span>${url}</span>
                        <button class="btn btn-secondary" onclick="scrapeAIUrl('${url}')">Scrape</button>
                    </div>
                `;
            });
            html += '</div>';
            suggestionsDiv.innerHTML = html;
        } else {
            suggestionsDiv.innerHTML = '<p class="help-text">No URLs found. ' + (data.message || '') + '</p>';
        }
    } catch (error) {
        console.error('Error suggesting URLs:', error);
        suggestionsDiv.innerHTML = '<p class="help-text" style="color: red;">Error: ' + error.message + '</p>';
    }
}

// Scrape a URL from AI suggestions
async function scrapeAIUrl(url) {
    showStatus(`Scraping ${url}...`, 'info');
    
    try {
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url }),
        });
        
        const data = await response.json();
        
        if (data.success) {
            showStatus(data.message, 'success');
            loadStatistics();
            loadContent();
        } else {
            showStatus(data.message, 'error');
        }
    } catch (error) {
        console.error('Error scraping URL:', error);
        showStatus('Error scraping URL', 'error');
    }
}
