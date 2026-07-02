/**
 * FinTech Sales Intelligence Dashboard Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- Elements ---
    const form = document.getElementById('analysis-form');
    const startBtn = document.getElementById('start-btn');
    const exchangeInput = document.getElementById('exchange-name');
    const countryInput = document.getElementById('country');
    
    const progressContainer = document.getElementById('progress-container');
    const currentExchangeName = document.getElementById('current-exchange-name');
    const jobStatusBadge = document.getElementById('job-status');
    const progressFill = document.getElementById('progress-fill');
    const stepsContainer = document.getElementById('steps-container');
    
    const errorBox = document.getElementById('error-box');
    const errorMessage = document.getElementById('error-message');
    
    const resultsContainer = document.getElementById('results-container');
    
    let currentWs = null;

    // --- Pipeline Steps Definition ---
    const PIPELINE_STEPS = [
        { id: 1, key: 'discovering_exchange', label: 'Discovering Exchange' },
        { id: 2, key: 'finding_member_list', label: 'Finding Members List' },
        { id: 3, key: 'extracting_brokers', label: 'Extracting Brokers' },
        { id: 4, key: 'discovering_websites', label: 'Discovering Websites' },
        { id: 5, key: 'crawling_websites', label: 'Crawling Websites' },
        { id: 6, key: 'detecting_technology', label: 'Detecting Technology' },
        { id: 7, key: 'discovering_executives', label: 'Discovering Executives' },
        { id: 8, key: 'resolving_profiles', label: 'Resolving Profiles' },
        { id: 9, key: 'analyzing_opportunities', label: 'Analyzing Opportunities' },
        { id: 10, key: 'scoring_leads', label: 'Scoring Leads' },
        { id: 11, key: 'generating_insights', label: 'Generating Insights' },
        { id: 12, key: 'generating_emails', label: 'Generating Emails' },
    ];

    // --- Initialize UI ---
    function initStepsUI() {
        stepsContainer.innerHTML = '';
        PIPELINE_STEPS.forEach(step => {
            const el = document.createElement('div');
            el.className = 'step-item';
            el.id = `step-${step.id}`;
            el.innerHTML = `
                <div class="step-icon">${step.id}</div>
                <span>${step.label}</span>
            `;
            stepsContainer.appendChild(el);
        });
    }

    // --- Form Submission ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const exchangeName = exchangeInput.value.trim();
        const country = countryInput.value.trim();
        
        if (!exchangeName) return;

        // Reset UI
        errorBox.style.display = 'none';
        resultsContainer.style.display = 'none';
        initStepsUI();
        progressFill.style.width = '0%';
        currentExchangeName.textContent = exchangeName;
        progressContainer.style.display = 'block';
        
        startBtn.disabled = true;
        startBtn.textContent = 'Starting...';

        try {
            // 1. Start Job via API
            const response = await fetch('/api/v1/analysis', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    exchange_name: exchangeName,
                    country: country || null
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to start analysis');
            }

            // 2. Connect WebSocket for live progress
            connectWebSocket(data.job_id);

        } catch (err) {
            showError(err.message);
            startBtn.disabled = false;
            startBtn.textContent = 'Start Analysis';
        }
    });

    // --- WebSocket Logic ---
    function connectWebSocket(jobId) {
        if (currentWs) {
            currentWs.close();
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/progress/${jobId}`;
        
        currentWs = new WebSocket(wsUrl);

        currentWs.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            if (data.status === 'error' || data.error) {
                showError(data.error || data.message);
                currentWs.close();
                return;
            }

            updateProgressUI(data);

            if (data.status === 'completed' || data.status === 'failed') {
                currentWs.close();
                startBtn.disabled = false;
                startBtn.textContent = 'Start Analysis';
                
                if (data.status === 'completed') {
                    fetchResults(jobId);
                }
            }
        };

        currentWs.onerror = (error) => {
            console.error('WebSocket Error:', error);
            showError('Lost connection to server.');
            startBtn.disabled = false;
            startBtn.textContent = 'Start Analysis';
        };
    }

    // --- Update UI ---
    function updateProgressUI(data) {
        // Update Badge
        jobStatusBadge.textContent = data.status.replace(/_/g, ' ').toUpperCase();
        
        if (data.status === 'completed') {
            jobStatusBadge.style.color = 'var(--accent-emerald)';
            jobStatusBadge.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';
            jobStatusBadge.style.borderColor = 'rgba(16, 185, 129, 0.2)';
            progressFill.style.width = '100%';
        } else if (data.status === 'failed') {
            jobStatusBadge.style.color = 'var(--accent-rose)';
            jobStatusBadge.style.backgroundColor = 'rgba(244, 63, 94, 0.1)';
            jobStatusBadge.style.borderColor = 'rgba(244, 63, 94, 0.2)';
        } else {
            jobStatusBadge.style.color = 'var(--accent-primary)';
            jobStatusBadge.style.backgroundColor = 'rgba(14, 165, 233, 0.1)';
            jobStatusBadge.style.borderColor = 'rgba(14, 165, 233, 0.2)';
            jobStatusBadge.classList.add('pulse');
            
            // Calculate width (step_number is 1-based, total is 13)
            const percent = Math.min(100, Math.max(5, (data.step_number / (data.total_steps - 1)) * 100));
            progressFill.style.width = `${percent}%`;
        }

        if (data.status === 'completed' || data.status === 'failed') {
            jobStatusBadge.classList.remove('pulse');
        }

        // Update Steps Grid
        let currentIdx = PIPELINE_STEPS.findIndex(s => s.key === data.status);
        if (data.status === 'completed') currentIdx = PIPELINE_STEPS.length;
        
        PIPELINE_STEPS.forEach((step, index) => {
            const el = document.getElementById(`step-${step.id}`);
            if (!el) return;
            
            el.className = 'step-item'; // Reset
            
            if (index < currentIdx) {
                el.classList.add('completed');
                el.querySelector('.step-icon').textContent = '✓';
            } else if (index === currentIdx) {
                el.classList.add('active');
                el.classList.add('pulse');
                el.querySelector('.step-icon').textContent = '↻';
            } else {
                el.querySelector('.step-icon').textContent = step.id;
            }
        });
    }

    function showError(msg) {
        errorBox.style.display = 'block';
        errorMessage.textContent = msg;
        jobStatusBadge.textContent = 'ERROR';
        jobStatusBadge.style.color = 'var(--accent-rose)';
        jobStatusBadge.classList.remove('pulse');
    }

    // --- Fetch Results ---
    async function fetchResults(jobId) {
        try {
            const response = await fetch(`/api/v1/analysis/${jobId}/results`);
            const data = await response.json();
            
            if (response.ok && data.report_data) {
                renderResults(data.report_data);
            }
        } catch (err) {
            console.error('Failed to fetch results', err);
        }
    }

    function renderResults(report) {
        // This is a placeholder for where we'd render the actual data table.
        // The backend `report_data` structure would dictate this.
        
        document.getElementById('stat-hot').textContent = report.hot_leads || 0;
        document.getElementById('stat-warm').textContent = report.warm_leads || 0;
        document.getElementById('stat-opps').textContent = report.total_opportunities || 0;
        document.getElementById('stat-execs').textContent = report.total_executives || 0;
        
        resultsContainer.style.display = 'block';
        
        // Scroll to results
        setTimeout(() => {
            resultsContainer.scrollIntoView({ behavior: 'smooth' });
        }, 500);
    }
    
    // Initial Setup
    initStepsUI();
});
