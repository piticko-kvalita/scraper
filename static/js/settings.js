// Settings page JavaScript

// Load settings on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    loadAIStatus();
    
    // Show/hide AI features info based on checkbox
    document.getElementById('ai-enabled').addEventListener('change', (e) => {
        const featuresInfo = document.getElementById('ai-features-info');
        featuresInfo.style.display = e.target.checked ? 'block' : 'none';
    });
});

// Load current settings
async function loadSettings() {
    try {
        const response = await fetch('/api/settings');
        const settings = await response.json();
        
        // Populate form
        if (settings.openrouter_api_key_set) {
            document.getElementById('api-key').placeholder = settings.openrouter_api_key_masked || '••••••••';
        }
        
        document.getElementById('ai-enabled').checked = settings.ai_enabled || false;
        document.getElementById('quality-threshold').value = settings.quality_threshold || 0.3;
        document.getElementById('auto-interval').value = settings.auto_gather_interval || 24;
        
        // Show AI features if enabled
        if (settings.ai_enabled) {
            document.getElementById('ai-features-info').style.display = 'block';
        }
        
        // Update status
        if (settings.openrouter_api_key_set) {
            document.getElementById('api-key-status').textContent = settings.openrouter_api_key_masked;
        }
        
    } catch (error) {
        console.error('Error loading settings:', error);
        showStatus('Error loading settings', 'error');
    }
}

// Load AI status
async function loadAIStatus() {
    try {
        const response = await fetch('/api/ai/status');
        const status = await response.json();
        
        const statusEl = document.getElementById('ai-status');
        if (status.configured && status.enabled) {
            statusEl.textContent = '✅ Configured & Enabled';
            statusEl.className = 'status-badge success';
        } else if (status.configured) {
            statusEl.textContent = '⚠️ Configured but Disabled';
            statusEl.className = 'status-badge warning';
        } else {
            statusEl.textContent = '❌ Not Configured';
            statusEl.className = 'status-badge error';
        }
        
    } catch (error) {
        console.error('Error loading AI status:', error);
    }
}

// Save settings
async function saveSettings() {
    const apiKey = document.getElementById('api-key').value.trim();
    const aiEnabled = document.getElementById('ai-enabled').checked;
    const qualityThreshold = parseFloat(document.getElementById('quality-threshold').value);
    const autoInterval = parseInt(document.getElementById('auto-interval').value);
    
    const settings = {
        ai_enabled: aiEnabled,
        quality_threshold: qualityThreshold,
        auto_gather_interval: autoInterval,
    };
    
    // Only include API key if a new one is provided
    if (apiKey && !apiKey.startsWith('••')) {
        settings.openrouter_api_key = apiKey;
    }
    
    // Validate
    if (aiEnabled && !settings.openrouter_api_key && document.getElementById('api-key').placeholder.startsWith('Enter')) {
        showStatus('Please enter an OpenRouter API key to enable AI features', 'error');
        return;
    }
    
    try {
        showStatus('Saving settings...', 'info');
        
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(settings),
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus('Settings saved successfully! ✅', 'success');
            // Reload settings and status
            setTimeout(() => {
                loadSettings();
                loadAIStatus();
            }, 500);
        } else {
            showStatus(`Error: ${result.message}`, 'error');
        }
        
    } catch (error) {
        console.error('Error saving settings:', error);
        showStatus('Error saving settings', 'error');
    }
}

// Show status message
function showStatus(message, type) {
    const statusDiv = document.getElementById('settings-status');
    statusDiv.textContent = message;
    statusDiv.className = `status-message ${type}`;
    statusDiv.style.display = 'block';
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        statusDiv.style.display = 'none';
    }, 5000);
}
