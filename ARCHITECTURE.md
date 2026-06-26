# Architecture

## Vue d'ensemble

L'**Assistant de Pré-Diagnostic Médical** est construit selon les principes de **Clean Architecture** avec un workflow **Multi-Agents LangGraph**.

## Diagramme de l'Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Client HTTP                           │
│          (curl, navigateur, application)                 │
└────────────────────┬───────────────────────────────────┘
                     │
┌────────────────────▼───────────────────────────────────┐
│              FastAPI Middleware                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │           CorrelationMiddleware                   │  │
│  │  • Génération X-Correlation-ID                   │  │
│  │  • Mesure du temps d'exécution                   │  │
│  │  • Logging de toutes les requêtes                │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────┘
                     │
┌────────────────────▼───────────────────────────────────┐
│                    API Layer                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Routes (/chat, /health, /metrics, /dashboard)    │  │
│  │  Schémas Pydantic (validation)                    │  │
│  │  Gestion des erreurs                              │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────┘
                     │
┌────────────────────▼───────────────────────────────────┐
│                Service Layer                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │        MedicalAIService                           │  │
│  │  • Orchestration du workflow LangGraph            │  │
│  │  • Gestion des appels agents                      │  │
│  │  • Sauvegarde en base de données                  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────┬───────────────────────────────────┘
                     │
┌────────────────────▼───────────────────────────────────┐
│              LangGraph Workflow                         │
│                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │Supervisor│───▶│Symptom       │───▶│Risk          │ │
│  │Agent     │    │Analysis Agent│    │Assessment    │ │
│  └──────────┘    └──────────────┘    │Agent         │ │
│                                      └──────┬───────┘ │
│  ┌──────────┐    ┌──────────────┐          │          │
│  │Monitoring│◀───│Medical       │◀─────────┘          │
│  │Agent     │    │Advice Agent  │                      │
│  └──────────┘    └──────────────┘                     │
└────────────────────┬───────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          ▼                      ▼
┌──────────────────┐  ┌──────────────────┐
│   Base de        │  │   Monitoring     │
│   Données SQLite │  │   (Loguru)       │
│   • requests     │  │   • Logs console │
│   • metrics      │  │   • Fichiers     │
│   • logs         │  │   • Rotation     │
│   • history      │  │   • Compression  │
└──────────────────┘  └──────────────────┘
```

## Flux de Données

1. **Requête entrante** → Middleware ajoute X-Correlation-ID
2. **Supervisor** → Valide l'entrée, route vers Symptom Analysis
3. **Symptom Analysis** → Extrait les symptômes du texte
4. **Risk Assessment** → Évalue le niveau de risque (LOW/MEDIUM/HIGH)
5. **Medical Advice** → Génère des conseils généraux
6. **Monitoring** → Enregistre les métriques d'exécution
7. **Réponse** → Compilation et retour au client
8. **Base de données** → Sauvegarde asynchrone

## Structure des Couches

### 1. Agents (`app/agents/`)
- `BaseAgent` : Classe abstraite avec création LLM et timing
- `SupervisorAgent` : Routage et orchestration
- `SymptomAnalysisAgent` : Extraction des symptômes (LLM + fallback)
- `RiskAssessmentAgent` : Évaluation des risques
- `MedicalAdviceAgent` : Conseils généraux
- `MonitoringAgent` : Métriques d'exécution

### 2. Core (`app/core/`)
- Configuration via variables d'environnement (Pydantic Settings)
- Exceptions personnalisées

### 3. Database (`app/database/`)
- Connection async SQLAlchemy + aiosqlite
- Modèles : Request, Log, Metric, History

### 4. Middleware (`app/middleware/`)
- CorrelationMiddleware : ID unique, timing, logging

### 5. Monitoring (`app/monitoring/`)
- Loguru : Console + fichier avec rotation
- Timer context manager
- Métriques système (CPU, mémoire)

### 6. Services (`app/services/`)
- MedicalAIService : Orchestrateur principal

## Principes de Conception

- **Clean Architecture** : Séparation des préoccupations
- **SOLID** : Interfaces bien définies
- **DRY** : Pas de duplication
- **KISS** : Simplicité
- **Failover** : Fallback sans LLM
- **Async/await** : Toute l'application est asynchrone
