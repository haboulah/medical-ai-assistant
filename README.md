# Medical AI Assistant

**Assistant de Pré-Diagnostic Médical** basé sur une architecture **Multi-Agents LangGraph**.

⚠️ **Avertissement : cette application fournit uniquement une aide informative et ne remplace pas un professionnel de santé.**

---

## 🎯 Objectif

Système multi-agents qui analyse les symptômes décrits par l'utilisateur, évalue le niveau de risque et fournit des conseils généraux. Le système ne remplace jamais un médecin.

## ✨ Fonctionnalités

- 🤖 **Multi-Agents LangGraph** : Supervisor, Symptom Analysis, Risk Assessment, Medical Advice, Monitoring
- 🏗️ **Clean Architecture** : Modulaire, testé, prêt pour la production
- 🚀 **API REST FastAPI** : Endpoints complets avec documentation Swagger/Redoc
- 📊 **Dashboard temps réel** : Bootstrap 5 + Chart.js avec auto-refresh
- 💾 **Base de données SQLite** : Persistance des requêtes, métriques et historique
- 🔍 **Middleware** : Correlation ID, timing, logging structuré
- 📝 **Logging avancé** : Loguru avec rotation et rétention
- 🐳 **Docker** : Conteneurisé et prêt pour le déploiement
- ✅ **Tests complets** : Pytest avec coverage ≥ 90%
- 🔄 **CI/CD** : GitHub Actions + Render

## 🏗️ Architecture

```
Utilisateur → Supervisor Agent → Symptom Analysis Agent
  → Risk Assessment Agent → Medical Advice Agent
  → Monitoring Agent → Réponse Finale
```

## 🛠️ Stack Technique

| Technologie | Version |
|------------|---------|
| Python | 3.12+ |
| FastAPI | 0.115+ |
| LangGraph | 0.3+ |
| Groq (LLM) | llama-3.3-70b-versatile |
| SQLAlchemy | 2.0+ |
| SQLite | - |
| Bootstrap | 5.3 |
| Chart.js | 4.4 |
| Docker | - |

## 🚀 Démarrage Rapide

### Avec Docker

```bash
cp .env.example .env
# Éditer .env avec votre clé GROQ_API_KEY
docker compose up --build
```

### Sans Docker

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## 📚 Documentation

- [Guide d'installation](INSTALL.md)
- [Architecture](ARCHITECTURE.md)
- [API](API.md)
- [Déploiement Render](DEPLOY_RENDER.md)
- [Agent Card](agent_card.md)
- [Runbook Incident](runbook_incident.md)
- [Changelog](CHANGELOG.md)

## 📖 Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Informations API |
| `GET /health` | Health check |
| `POST /chat` | Chat avec les agents |
| `GET /metrics` | Métriques |
| `GET /dashboard` | Dashboard web |
| `GET /dashboard/data` | Données du dashboard (JSON) |
| `GET /history` | Historique des conversations |
| `GET /logs` | Logs applicatifs |
| `GET /version` | Version |
| `/docs` | Swagger UI |
| `/redoc` | Redoc UI |

## 📁 Structure du Projet

```
medical-ai-assistant/
├── app/
│   ├── agents/       # Agents du système multi-agents
│   ├── api/          # Routes FastAPI
│   ├── core/         # Configuration et exceptions
│   ├── database/     # Modèles et connexion SQLite
│   ├── dashboard/    # Template HTML du dashboard
│   ├── graph/        # Workflow LangGraph
│   ├── middleware/   # Middleware FastAPI
│   ├── monitoring/   # Logging et monitoring
│   ├── prompts/      # Templates de prompts
│   ├── schemas/      # Schémas Pydantic
│   ├── services/     # Logique métier
│   └── utils/        # Utilitaires
├── tests/            # Tests pytest
├── docs/             # Documentation
├── logs/             # Fichiers de logs
├── Dockerfile
├── docker-compose.yml
├── render.yaml
└── README.md
```

## 📄 Licence

MIT
