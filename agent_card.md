# Agent Card

## Informations Générales

| Champ | Valeur |
|-------|--------|
| **Nom** | Medical AI Assistant |
| **Version** | 1.0.0 |
| **Type** | Multi-Agent System (LangGraph) |
| **Langage** | Python 3.12 |
| **Framework** | FastAPI |
| **LLM** | Groq (llama-3.3-70b-versatile) |

## Objectif

Assistant de pré-diagnostic médical basé sur une architecture multi-agents. Il analyse les symptômes décrits par l'utilisateur, évalue le niveau de risque et fournit des conseils généraux. Le système **ne remplace jamais un médecin**.

## Architecture des Agents

### 1. Supervisor Agent
- **Rôle** : Ordonnanceur du workflow
- **Responsabilités** :
  - Routage des requêtes vers les agents appropriés
  - Gestion du workflow LangGraph
  - Contrôle d'exécution et gestion d'erreurs
- **Entrée** : Texte libre de l'utilisateur
- **Sortie** : Décision de routage vers le prochain agent

### 2. Symptom Analysis Agent
- **Rôle** : Analyse des symptômes
- **Responsabilités** :
  - Extraction des symptômes du texte utilisateur
  - Retour sous forme de liste structurée
- **Entrée** : Texte libre (description des symptômes)
- **Sortie** : Liste de symptômes détectés + texte original
- **Fallback** : Extraction par mots-clés si LLM indisponible

### 3. Risk Assessment Agent
- **Rôle** : Évaluation des risques
- **Responsabilités** :
  - Analyse de la sévérité des symptômes
  - Attribution d'un niveau de risque
- **Entrée** : Liste des symptômes
- **Sortie** : Niveau (LOW/MEDIUM/HIGH) + justification
- **Critères** :
  - LOW : Symptômes légers (rhume, fatigue)
  - MEDIUM : Symptômes nécessitant une consultation
  - HIGH : Symptômes urgents

### 4. Medical Advice Agent
- **Rôle** : Conseils médicaux généraux
- **Responsabilités** :
  - Fournir des conseils adaptés au niveau de risque
  - Ne jamais poser de diagnostic
  - Rappeler le disclaimer médical
- **Entrée** : Symptômes + niveau de risque
- **Sortie** : Conseils généraux + disclaimer

### 5. Monitoring Agent
- **Rôle** : Métriques d'exécution
- **Responsabilités** :
  - Enregistrement du Correlation ID
  - Timing de chaque agent
  - Comptage des tokens
  - Statut succès/erreur
- **Entrée** : État final du workflow
- **Sortie** : Rapport de monitoring JSON

## Workflow

```
START → Supervisor → SymptomAnalysis → RiskAssessment → MedicalAdvice → Monitoring → END
```

## Entrées et Sorties

### Entrées
- **Format** : Texte libre (JSON via API REST)
- **Exemple** : `{"message": "J'ai de la fièvre et je tousse"}`
- **Contrainte** : 1-5000 caractères

### Sorties
- **Format** : JSON structuré
- **Champs** : symptoms, risk, medical_advice, monitoring
- **Toujours inclus** : Disclaimer médical

## Limites

1. **Pas de diagnostic médical** : Le système ne remplace pas un médecin
2. **Analyse textuelle uniquement** : Pas d'analyse d'images ou de documents
3. **Dépendance LLM** : Qualité dépendante du modèle Groq
4. **Fallback limité** : L'extraction par mots-clés est basique
5. **Stockage local** : Base de données SQLite (non adaptée à la production à grande échelle)
6. **Monolingue** : Optimisé pour le français

## Risques

1. **Faux négatifs** : Le système peut sous-estimer la gravité des symptômes
2. **Faux positifs** : Le système peut surestimer le niveau de risque
3. **Mauvaise interprétation** : L'utilisateur peut mal décrire ses symptômes
4. **Dépendance excessive** : L'utilisateur pourrait ignorer les signes graves
5. **Confidentialité** : Les données transitent par l'API Groq

## Sécurité

1. **API Key** : Authentification via Groq API Key stockée en variable d'environnement
2. **Validation** : Entrées validées par Pydantic
3. **CORS** : Middleware configurable
4. **Logging** : Logs avec rotation et rétention limitée
5. **Correlation ID** : Traçabilité de chaque requête

## Monitoring

- Loguru (console + fichier avec rotation)
- Métriques système (CPU, mémoire via psutil)
- Timing de chaque agent
- Métriques par requête stockées en base SQLite
- Dashboard temps réel (Chart.js)

## Outils et Dépendances

| Outil | Usage |
|-------|-------|
| FastAPI | Framework API REST |
| LangGraph | Orchestration multi-agents |
| Groq | LLM pour l'analyse |
| SQLAlchemy | ORM base de données |
| Loguru | Logging |
| psutil | Métriques système |
| Pytest | Tests |
| Ruff/Black/MyPy | Qualité de code |
| Docker | Conteneurisation |
| Render | Déploiement cloud |
