# Guide d'Installation

## Prérequis

- Python 3.12+
- Clé API Groq (gratuite : https://console.groq.com)
- Docker (optionnel)

## Installation Locale

### 1. Cloner le projet

```bash
git clone <votre-repo>
cd medical-ai-assistant
```

### 2. Configuration des variables d'environnement

```bash
cp .env.example .env
```

Éditer `.env` :

```env
GROQ_API_KEY=votre_clé_api_groq
APP_NAME=Medical AI Assistant
APP_VERSION=1.0.0
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
```

### 3. Environnement virtuel

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

### 4. Installation des dépendances

```bash
pip install -r requirements.txt
```

### 5. Lancer l'application

```bash
uvicorn app.main:app --reload
```

### 6. Accès

- Application : http://localhost:8000
- Dashboard : http://localhost:8000/dashboard
- Swagger : http://localhost:8000/docs
- Redoc : http://localhost:8000/redoc

## Installation avec Docker

### 1. Configuration

```bash
cp .env.example .env
# Éditer .env avec votre clé GROQ_API_KEY
```

### 2. Build et lancement

```bash
docker compose up --build
```

### 3. Arrêt

```bash
docker compose down
```

## Installation pour le développement

```bash
# Installer les dépendances de développement
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov httpx ruff black mypy

# Exécuter les tests
pytest tests/ -v --cov=app

# Vérifier le formatage
black --check app/ tests/

# Linting
ruff check app/ tests/

# Type checking
mypy app/
```

## Résolution de problèmes

### Erreur : GROQ_API_KEY non configurée
Le système fonctionne avec une extraction de symptômes par fallback, mais l'analyse LLM ne sera pas disponible.

### Erreur : Port déjà utilisé
```bash
# Changer le port dans .env
APP_PORT=8001
```

### Erreur : Base de données verrouillée
```bash
# Supprimer la base de données et redémarrer
rm -f data/medical_ai.db
uvicorn app.main:app --reload
```
