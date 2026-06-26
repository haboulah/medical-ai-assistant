# Dashboard HTML template.
"""Bootstrap 5 dashboard with Chart.js for real-time monitoring."""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Medical AI Assistant - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
    <style>
        :root { --primary: #0d6efd; --success: #198754; --warning: #ffc107; --danger: #dc3545; }
        body { background: #f8f9fa; font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; }
        .navbar-brand { font-weight: 700; font-size: 1.3rem; }
        .stat-card { border: none; border-radius: 12px; transition: transform 0.2s; }
        .stat-card:hover { transform: translateY(-3px); }
        .stat-card .card-body { padding: 1.2rem; }
        .stat-value { font-size: 2rem; font-weight: 700; line-height: 1.2; }
        .stat-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.8; }
        .chart-container { position: relative; height: 250px; }
        .table-container { max-height: 400px; overflow-y: auto; }
        .badge-risk-LOW { background-color: var(--success); }
        .badge-risk-MEDIUM { background-color: var(--warning); color: #000; }
        .badge-risk-HIGH { background-color: var(--danger); }
        .badge-status-success { background-color: var(--success); }
        .badge-status-error { background-color: var(--danger); }
        .refresh-indicator { font-size: 0.75rem; opacity: 0.6; }
        .card-header { font-weight: 600; background: transparent; border-bottom: 2px solid #e9ecef; }
        @media (max-width: 768px) { .stat-value { font-size: 1.5rem; } }
        .status-dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
        .status-dot.ok { background-color: var(--success); }
        .status-dot.error { background-color: var(--danger); }
        .status-dot.warn { background-color: var(--warning); }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark bg-dark shadow-sm mb-4">
        <div class="container-fluid px-4">
            <span class="navbar-brand">
                <i class="bi bi-heart-pulse-fill text-danger me-2"></i>
                Medical AI Assistant
            </span>
            <div class="d-flex align-items-center gap-3">
                <span class="refresh-indicator text-light" id="lastUpdate"></span>
                <button class="btn btn-outline-light btn-sm" onclick="refreshDashboard()">
                    <i class="bi bi-arrow-clockwise"></i> Actualiser
                </button>
            </div>
        </div>
    </nav>

    <div class="container-fluid px-4">
        <!-- Status Row -->
        <div class="row mb-4">
            <div class="col-md-3 mb-3">
                <div class="card stat-card bg-primary text-white h-100">
                    <div class="card-body">
                        <div class="stat-value" id="totalRequests">0</div>
                        <div class="stat-label">Requetes Totales</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card stat-card bg-success text-white h-100">
                    <div class="card-body">
                        <div class="stat-value" id="successRate">100%</div>
                        <div class="stat-label">Taux de Succes</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card stat-card bg-warning text-dark h-100">
                    <div class="card-body">
                        <div class="stat-value" id="avgDuration">0ms</div>
                        <div class="stat-label">Temps Moyen</div>
                    </div>
                </div>
            </div>
            <div class="col-md-3 mb-3">
                <div class="card stat-card bg-danger text-white h-100">
                    <div class="card-body">
                        <div class="stat-value" id="errorCount">0</div>
                        <div class="stat-label">Erreurs</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="row mb-4">
            <div class="col-md-6 mb-4">
                <div class="card stat-card shadow-sm h-100">
                    <div class="card-header">
                        <i class="bi bi-pie-chart-fill me-2 text-primary"></i>Repartition des Risques
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="riskChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6 mb-4">
                <div class="card stat-card shadow-sm h-100">
                    <div class="card-header">
                        <i class="bi bi-bar-chart-fill me-2 text-primary"></i>Appels par Agent
                    </div>
                    <div class="card-body">
                        <div class="chart-container">
                            <canvas id="agentChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Metrics & System Row -->
        <div class="row mb-4">
            <div class="col-md-6 mb-4">
                <div class="card stat-card shadow-sm h-100">
                    <div class="card-header">
                        <i class="bi bi-clock-history me-2 text-primary"></i>Temps d'Execution
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-4">
                                <div class="stat-value text-success" id="minDuration">0ms</div>
                                <div class="stat-label text-muted">Minimum</div>
                            </div>
                            <div class="col-4">
                                <div class="stat-value text-warning" id="avgDuration2">0ms</div>
                                <div class="stat-label text-muted">Moyen</div>
                            </div>
                            <div class="col-4">
                                <div class="stat-value text-danger" id="maxDuration">0ms</div>
                                <div class="stat-label text-muted">Maximum</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6 mb-4">
                <div class="card stat-card shadow-sm h-100">
                    <div class="card-header">
                        <i class="bi bi-cpu me-2 text-primary"></i>Systeme
                    </div>
                    <div class="card-body">
                        <div class="row text-center">
                            <div class="col-4">
                                <div class="stat-value text-info" id="memUsage">0 MB</div>
                                <div class="stat-label text-muted">Memoire</div>
                            </div>
                            <div class="col-4">
                                <div class="stat-value text-info" id="cpuUsage">0%</div>
                                <div class="stat-label text-muted">CPU</div>
                            </div>
                            <div class="col-4">
                                <div class="stat-value text-info" id="apiStatus">
                                    <span class="status-dot ok" id="apiStatusDot"></span>OK
                                </div>
                                <div class="stat-label text-muted">API</div>
                            </div>
                        </div>
                        <hr>
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">Version:</small>
                                <span class="badge bg-secondary" id="appVersion">1.0.0</span>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">LLM:</small>
                                <span class="badge bg-warning text-dark" id="llmStatus">Non configure</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Requests -->
        <div class="card stat-card shadow-sm mb-4">
            <div class="card-header">
                <i class="bi bi-list-ul me-2 text-primary"></i>Requetes Recentes
                <span class="badge bg-secondary ms-2" id="requestCount">0</span>
            </div>
            <div class="card-body table-container">
                <table class="table table-hover mb-0">
                    <thead>
                        <tr>
                            <th>Correlation ID</th>
                            <th>Message</th>
                            <th>Statut</th>
                            <th>Risque</th>
                            <th>Temps</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody id="requestsTable"></tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        let riskChartInstance = null;
        let agentChartInstance = null;
        let refreshInterval = null;

        // Colors
        const COLORS = {
            low: '#198754',
            medium: '#ffc107',
            high: '#dc3545',
            agents: ['#0d6efd', '#6f42c1', '#fd7e14', '#20c997', '#e83e8c']
        };

        async function refreshDashboard() {
            try {
                document.getElementById('lastUpdate').textContent =
                    'Derniere mise a jour: ' + new Date().toLocaleTimeString('fr-FR');

                const response = await fetch('/dashboard/data');
                if (!response.ok) throw new Error('HTTP ' + response.status);
                const data = await response.json();
                applyDashboardData(data);
            } catch (err) {
                console.error('Dashboard refresh error:', err);
                const apiDot = document.getElementById('apiStatusDot');
                if (apiDot) apiDot.className = 'status-dot error';
            }
        }

        function applyDashboardData(data) {
            try { document.getElementById('totalRequests').textContent = data.total_requests; } catch(e) {}
            try { document.getElementById('successRate').textContent = data.success_rate + '%'; } catch(e) {}
            try { document.getElementById('avgDuration').textContent = data.avg_duration_ms + 'ms'; } catch(e) {}
            try { document.getElementById('avgDuration2').textContent = data.avg_duration_ms + 'ms'; } catch(e) {}
            try { document.getElementById('errorCount').textContent = data.error_count; } catch(e) {}
            try { document.getElementById('minDuration').textContent = data.min_duration_ms + 'ms'; } catch(e) {}
            try { document.getElementById('maxDuration').textContent = data.max_duration_ms + 'ms'; } catch(e) {}
            try { document.getElementById('memUsage').textContent = data.memory_usage_mb.toFixed(1) + ' MB'; } catch(e) {}
            try { document.getElementById('cpuUsage').textContent = data.cpu_percent + '%'; } catch(e) {}
            try { document.getElementById('appVersion').textContent = data.version; } catch(e) {}
            try { document.getElementById('requestCount').textContent = (data.recent_requests || []).length; } catch(e) {}

            // LLM status
            try {
                const llmBadge = document.getElementById('llmStatus');
                if (data.llm_configured) {
                    llmBadge.className = 'badge bg-success';
                    llmBadge.textContent = 'Groq OK';
                } else {
                    llmBadge.className = 'badge bg-warning text-dark';
                    llmBadge.textContent = 'Non configure';
                }
            } catch(e) {}

            // API status
            try {
                const apiDot = document.getElementById('apiStatusDot');
                if (apiDot) apiDot.className = 'status-dot ok';
            } catch(e) {}

            // Charts (safe: try/catch per chart)
            try { updateRiskChart(data.risk_distribution || {}); } catch(e) { console.warn('Risk chart:', e); }
            try { updateAgentChart(data.agent_calls || {}); } catch(e) { console.warn('Agent chart:', e); }
            try { updateRequestsTable(data.recent_requests || []); } catch(e) { console.warn('Table:', e); }
        }

        function updateRiskChart(riskDist) {
            const el = document.getElementById('riskChart');
            if (!el) return;
            const ctx = el.getContext('2d');
            const labels = Object.keys(riskDist);
            const values = Object.values(riskDist);
            const colors = labels.map(l => {
                switch(l) {
                    case 'LOW': return COLORS.low;
                    case 'MEDIUM': return COLORS.medium;
                    case 'HIGH': return COLORS.high;
                    default: return '#6c757d';
                }
            });
            if (riskChartInstance) riskChartInstance.destroy();
            riskChartInstance = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels.length ? labels : ['Aucune donnee'],
                    datasets: [{
                        data: labels.length ? values : [1],
                        backgroundColor: labels.length ? colors : ['#e9ecef'],
                        borderWidth: 2,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: 'bottom' } }
                }
            });
        }

        function updateAgentChart(agentCalls) {
            const el = document.getElementById('agentChart');
            if (!el) return;
            const ctx = el.getContext('2d');
            const labels = Object.keys(agentCalls);
            const values = Object.values(agentCalls);
            const colors = labels.map((_, i) => COLORS.agents[i % COLORS.agents.length]);
            if (agentChartInstance) agentChartInstance.destroy();
            agentChartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels.length ? labels : ['Aucune donnee'],
                    datasets: [{
                        label: "Nombre d'appels",
                        data: labels.length ? values : [0],
                        backgroundColor: labels.length ? colors : ['#e9ecef'],
                        borderRadius: 6,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
                    plugins: { legend: { display: false } }
                }
            });
        }

        function updateRequestsTable(requests) {
            const tbody = document.getElementById('requestsTable');
            if (!tbody) return;
            if (!requests || requests.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-4">Aucune requete</td></tr>';
                return;
            }
            tbody.innerHTML = requests.map(function(r) {
                var id = (r.correlation_id && r.correlation_id.substring(0, 8)) || '---';
                var msg = (r.user_input && r.user_input.substring(0, 60)) || '';
                var status = r.status || '';
                var risk = r.risk_level || 'LOW';
                var dur = r.duration_ms ? r.duration_ms.toFixed(1) + 'ms' : '---';
                var date = formatDateTime(r.created_at);
                return '<tr><td><code>' + escapeHtml(id) + '...</code></td><td>' + escapeHtml(msg) + '</td><td><span class="badge badge-status-' + status + '">' + status + '</span></td><td><span class="badge badge-risk-' + risk + '">' + risk + '</span></td><td>' + dur + '</td><td><small>' + date + '</small></td></tr>';
            }).join('');
        }

        function escapeHtml(text) {
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function formatDateTime(isoStr) {
            if (!isoStr) return '---';
            try {
                var d = new Date(isoStr);
                return d.toLocaleString('fr-FR', {
                    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'
                });
            } catch(e) { return isoStr; }
        }

        // Auto-refresh every 10 seconds
        document.addEventListener('DOMContentLoaded', function() {
            refreshDashboard();
            refreshInterval = setInterval(refreshDashboard, 10000);
        });
    </script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""
