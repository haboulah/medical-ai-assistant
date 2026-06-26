# Déploiement sur Render

Ce guide explique comment déployer l'Assistant de Pré-Diagnostic Médical sur Render.

## Prérequis

1. Compte Render (https://render.com)
2. Clé API Groq (https://console.groq.com)
3. Dépôt GitHub/GitLab du projet

## Méthode 1 : Déploiement via Blueprint (recommandé)

### 1. Pousser le projet sur GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/votre-compte/medical-ai-assistant.git
git push -u origin main
```

### 2. Déployer sur Render

1. Connectez-vous à Render
2. Cliquez sur **New → Blueprint**
3. Connectez votre dépôt GitHub
4. Render détecte automatiquement `render.yaml`
5. Configurez les variables d'environnement :
   - `GROQ_API_KEY` : Votre clé API Groq
6. Cliquez sur **Apply**

## Méthode 2 : Déploiement Web Service manuel

### 1. Créer un Web Service

1. Connectez-vous à Render
2. Cliquez sur **New → Web Service**
3. Connectez votre dépôt GitHub

### 2. Configuration

- **Name** : `medical-ai-assistant`
- **Environment** : `Python`
- **Region** : `Frankfurt (EU)` (recommandé)
- **Branch** : `main`
- **Build Command** : `pip install -r requirements.txt`
- **Start Command** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Plan** : Free

### 3. Variables d'environnement

Ajouter dans Render Dashboard :

| Variable | Valeur |
|----------|--------|
| `GROQ_API_KEY` | Votre clé API Groq |
| `APP_NAME` | `Medical AI Assistant` |
| `APP_VERSION` | `1.0.0` |
| `LOG_LEVEL` | `INFO` |
| `PYTHON_VERSION` | `3.12.2` |

### 4. Health Check

Chemin : `/health`

## Vérification

Une fois déployé :

- **URL** : `https://medical-ai-assistant.onrender.com`
- **Dashboard** : `https://medical-ai-assistant.onrender.com/dashboard`
- **Swagger** : `https://medical-ai-assistant.onrender.com/docs`
- **Health** : `https://medical-ai-assistant.onrender.com/health`

## Limitations du plan Free

- 750 heures/mois (un service en continu = 720h)
- 100 GB de bande passante
- Mise en veille après 15 minutes d'inactivité
- Nécessite un réveil (10-30 secondes)

## Mise à jour

```bash
git add .
git commit -m "Nouvelle fonctionnalité"
git push
```

Render déploie automatiquement.

## Dépannage

**Erreur : Application non disponible**
```bash
# Vérifier les logs Render Dashboard
# Vérifier que le port $PORT est utilisé
```

**Erreur : GROQ_API_KEY manquante**
```bash
# Ajouter la variable d'environnement dans Render Dashboard
```

**Base de données SQLite sur Render**
- Les données sont stockées dans le disque éphémère
- Perte de données au redémarrage
- Pour la production, utiliser PostgreSQL (Render propose PostgreSQL gratuit)
