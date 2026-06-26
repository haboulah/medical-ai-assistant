---
title: Medical Ai Assistant
emoji: 🔥
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 10000
---

# Medical AI Assistant

**Assistant de Pré-Diagnostic Médical** basé sur une architecture **Multi-Agents LangGraph**.

**Avertissement : cette application fournit uniquement une aide informative et ne remplace pas un professionnel de sante.**

---

## Objectif

Systeme multi-agents qui analyse les symptomes decrits par l'utilisateur, evalue le niveau de risque et fournit des conseils generaux. Le systeme ne remplace jamais un medecin.

## Fonctionnalites

- **Multi-Agents LangGraph** : Supervisor, Symptom Analysis, Risk Assessment, Medical Advice, Monitoring
- **Clean Architecture** : Modulaire, teste, pret pour la production
- **API REST FastAPI** : Endpoints complets avec documentation Swagger/Redoc
- **Dashboard temps reel** : Bootstrap 5 + Chart.js avec auto-refresh et valeurs injectees cote serveur
- **Interface Chat** : Design type messagerie clinique, bulles, resultats medicaux structures
- **Base de donnees SQLite** : Persistance des requetes, metriques et historique
- **Middleware** : Correlation ID, timing, logging structure
- **Logging avance** : Loguru avec rotation et retention
- **Docker** : Conteneurise et pret pour le deploiement
- **Tests complets** : Pytest avec 195 tests et couverture >= 88%
- **CI/CD** : GitHub Actions + Render

## Architecture

```
Utilisateur -> Supervisor Agent -> Symptom Analysis Agent
  -> Risk Assessment Agent -> Medical Advice Agent
  -> Monitoring Agent -> Reponse Finale
```

## Stack Technique

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

## Demarrage Rapide

### Avec Docker

```bash
cp .env.example .env
# Editer .env avec votre cle GROQ_API_KEY
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

## Documentation

- [Guide d'installation](INSTALL.md)
- [Architecture](ARCHITECTURE.md)
- [API](API.md)
- [Deploiement Render](DEPLOY_RENDER.md)
- [Agent Card](agent_card.md)
- [Runbook Incident](runbook_incident.md)
- [Changelog](CHANGELOG.md)

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Informations API |
| `GET /health` | Health check |
| `POST /chat` | Chat avec les agents |
| `GET /chat-ui` | Interface chat web |
| `GET /metrics` | Metriques |
| `GET /dashboard` | Dashboard web |
| `GET /dashboard/data` | Donnees du dashboard (JSON) |
| `GET /history` | Historique des conversations |
| `GET /logs` | Logs applicatifs |
| `GET /version` | Version |
| `/docs` | Swagger UI |
| `/redoc` | Redoc UI |

## Structure du Projet

```
medical-ai-assistant/
+-- app/
|   +-- agents/       # Agents du systeme multi-agents
|   +-- api/          # Routes FastAPI
|   +-- core/         # Configuration et exceptions
|   +-- database/     # Modeles et connexion SQLite
|   +-- dashboard/    # Template HTML du dashboard
|   +-- graph/        # Workflow LangGraph
|   +-- middleware/   # Middleware FastAPI
|   +-- monitoring/   # Logging et monitoring
|   +-- prompts/      # Templates de prompts
|   +-- schemas/      # Schemas Pydantic
|   +-- services/     # Logique metier
|   +-- utils/        # Utilitaires
+-- tests/            # Tests pytest
+-- docs/             # Documentation
+-- logs/             # Fichiers de logs
+-- Dockerfile
+-- docker-compose.yml
+-- render.yaml
+-- README.md
```

## Licence

MIT
---
title: Medical Ai Assistant
emoji: 🔥
colorFrom: indigo
colorTo: purple
sdk: docker
pinned: false
license: mit
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference
>>>>>>> da5a4be5e8e95e6569951a56900f3deafdafbfff
