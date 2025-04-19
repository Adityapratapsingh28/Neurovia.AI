document.addEventListener('DOMContentLoaded', function() {
    // Initialize feature dropdowns
    loadFeatureDropdowns();

    // Form submission handler
    document.getElementById('diagnosisForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const submitBtn = this.querySelector('button[type="submit"]');
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
            Processing...
        `;

        try {
            const features = [];
            const selects = document.querySelectorAll('.feature-select');
            
            // Validate and collect feature values
            for (const select of selects) {
                if (select.value === 'custom') {
                    const customInput = document.querySelector(`#${select.id}_custom`);
                    if (!customInput.value) {
                        throw new Error(`Please enter a value for ${select.name}`);
                    }
                    features.push(parseFloat(customInput.value));
                } else if (select.value) {
                    features.push(parseFloat(select.value));
                } else {
                    throw new Error(`Please select a value for ${select.name}`);
                }
            }

            // Submit to backend
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ features })
            });

            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Assessment failed');
            
            // Display results
            displayResults(data);
            
        } catch (error) {
            showError(error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Run Comprehensive Assessment';
        }
    });

    // Chat handler
    document.getElementById('chatForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const input = document.getElementById('questionInput');
        const question = input.value.trim();
        if (!question) return;

        const chatResponse = document.getElementById('chatResponse');
        addChatMessage('user', question);
        input.value = '';
        input.disabled = true;
        
        try {
            const response = await fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            });
            
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Failed to get response');
            
            addChatMessage('assistant', data.response);
            
        } catch (error) {
            addChatMessage('error', error.message);
        } finally {
            input.disabled = false;
            chatResponse.scrollTop = chatResponse.scrollHeight;
        }
    });
});

// Load feature dropdowns with actual values
async function loadFeatureDropdowns() {
    try {
        const response = await fetch('/feature_options');
        if (!response.ok) throw new Error('Failed to load feature options');
        
        const features = await response.json();
        const container = document.getElementById('featureInputs');
        container.innerHTML = '';
        
        // Create dropdown for each feature
        Object.entries(features).forEach(([name, options], index) => {
            const group = document.createElement('div');
            group.className = 'col-md-6 mb-3';
            
            group.innerHTML = `
                <label for="feature_${index}" class="form-label small">
                    ${formatFeatureName(name)}
                </label>
                <select class="form-select feature-select" 
                        id="feature_${index}" 
                        name="${name}" 
                        required>
                    <option value="" disabled selected>Select value</option>
                    ${options.map(val => `
                        <option value="${val}">${val.toFixed(6)}</option>
                    `).join('')}
                    <option value="custom">Custom value...</option>
                </select>
                <input type="number" step="any" 
                       class="form-control mt-2 custom-value" 
                       id="feature_${index}_custom" 
                       style="display: none;"
                       placeholder="Enter custom ${formatFeatureName(name)} value">
            `;
            
            container.appendChild(group);
            
            // Show/hide custom input
            document.getElementById(`feature_${index}`).addEventListener('change', function() {
                const customInput = document.getElementById(`feature_${index}_custom`);
                customInput.style.display = this.value === 'custom' ? 'block' : 'none';
                if (this.value === 'custom') customInput.focus();
            });
        });
        
    } catch (error) {
        console.error('Error loading features:', error);
        showError('Could not load feature options. Using default inputs.');
        createDefaultInputs();
    }
}

// Helper functions
function formatFeatureName(name) {
    return name.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2');
}

function createDefaultInputs() {
    const container = document.getElementById('featureInputs');
    container.innerHTML = '';
    
    for (let i = 0; i < 22; i++) {
        const group = document.createElement('div');
        group.className = 'col-md-6 mb-3';
        group.innerHTML = `
            <label for="feature_${i}" class="form-label small">
                Feature ${i+1}
            </label>
            <input type="number" step="any" 
                   class="form-control" 
                   id="feature_${i}" 
                   required>
        `;
        container.appendChild(group);
    }
}

function displayResults(data) {
    document.getElementById('results').innerHTML = `
        <div class="alert alert-${data.prediction.includes('No') ? 'success' : 'warning'}">
            <h4>${data.prediction}</h4>
            <hr>
            ${data.explanation}
        </div>
        <div class="mt-3">
            <h5>Feature Values</h5>
            <div class="table-responsive">
                <table class="table table-sm">
                    <tbody>
                        ${Object.entries(data.features).map(([name, value]) => `
                            <tr>
                                <td>${formatFeatureName(name)}</td>
                                <td>${parseFloat(value).toFixed(6)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    document.getElementById('medicalReport').innerHTML = data.report;
}

function addChatMessage(role, content) {
    const chatResponse = document.getElementById('chatResponse');
    const message = document.createElement('div');
    message.className = `chat-message ${role}`;
    message.innerHTML = `
        <strong>${role === 'user' ? 'You' : 'Assistant'}:</strong>
        <div>${content}</div>
    `;
    chatResponse.appendChild(message);
    chatResponse.scrollTop = chatResponse.scrollHeight;
}

function showError(message) {
    document.getElementById('results').innerHTML = `
        <div class="alert alert-danger">
            <h5>Error</h5>
            <p>${message}</p>
            <button onclick="window.location.reload()" 
                    class="btn btn-sm btn-outline-danger">
                Try Again
            </button>
        </div>
    `;
}