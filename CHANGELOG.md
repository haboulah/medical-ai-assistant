# Changelog

Tous les changements notables de ce projet sont documentés ici.

## [1.0.0] - 2026-06-26

### 🚀 Première version

#### Fonctionnalités
- 🤖 Système multi-agents LangGraph complet
  - Supervisor Agent : routage et orchestration
  - Symptom Analysis Agent : extraction des symptômes
  - Risk Assessment Agent : évaluation des risques (LOW/MEDIUM/HIGH)
  - Medical Advice Agent : conseils généraux
  - Monitoring Agent : métriques d'exécution
- 🚀 API REST FastAPI complète
  - 10 endpoints : /, /health, /chat, /metrics, /dashboard, /dashboard/data, /history, /logs, /version
  - Documentation Swagger (/docs) et Redoc (/redoc)
- 📊 Dashboard temps réel
  - Bootstrap 5 + Chart.js
  - Auto-refresh toutes les 10 secondes
  - Métriques : requêtes, succès, erreurs, temps, risques, agents, système
- 💾 Base de données SQLite
  - Tables : requests, logs, metrics, history
  - Sauvegarde asynchrone de chaque requête
- 🔍 Middleware
  - Correlation ID automatique (X-Correlation-ID)
  - Timing des requêtes
  - Logging structuré
- 📝 Monitoring avancé
  - Loguru avec rotation et compression
  - Métriques CPU et mémoire (psutil)
- 🐳 Docker
  - Dockerfile multi-stage
  - docker-compose avec volumes persistants
- 🔄 CI/CD
  - GitHub Actions : tests, linting, type checking, coverage
  - Render : configuration de déploiement
- ✅ Tests
  - Pytest avec pytest-asyncio
  - Couverture de code ≥ 90%
- 📚 Documentation complète
  - README, INSTALL, ARCHITECTURE, API, CHANGELOG, DEPLOY_RENDER
  - Agent Card, Runbook Incident

#### Architecture
- Clean Architecture : séparation des préoccupations
- SOLID : interfaces bien définies
- Fallback sans LLM : extraction et analyse locales
- Async/await : application 100% asynchrone
