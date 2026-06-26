# Runbook Incident

## Guide de réponse aux incidents pour le Medical AI Assistant

---

## 1. Détection

### Symptômes d'incident

| Niveau | Symptômes | Action |
|--------|-----------|--------|
| 🔴 Critique | API inaccessible, réponse 5xx, plantage | Incident critique |
| 🟠 Élevé | Temps de réponse > 10s, erreurs LLM fréquentes | Surveillance renforcée |
| 🟡 Moyen | Dashboard lent, base de données lente | Investigation |
| 🟢 Faible | Log warning, métriques anormales | Observation |

### Sources de détection

- Health check (`GET /health`)
- Métriques dashboard (`GET /metrics`)
- Logs application (`GET /logs`)
- Monitoring système (CPU, mémoire)
- Alertes Render Dashboard

### Seuils d'alerte

| Métrique | Seuil | Action |
|----------|-------|--------|
| Taux d'erreur | > 5% | Investigation |
| Temps de réponse | > 5s (moyen) | Optimisation |
| Utilisation mémoire | > 80% | Restart |
| CPU | > 90% pendant 5min | Scale up |
| Base de données | Erreur de connexion | Restart DB |

---

## 2. Containment

### Actions immédiates

```bash
# 1. Vérifier l'état de l'API
curl http://localhost:8000/health

# 2. Vérifier les métriques
curl http://localhost:8000/metrics

# 3. Vérifier les logs récents
curl http://localhost:8000/logs?limit=50

# 4. Vérifier les processus
ps aux | grep uvicorn
docker ps  # si Docker
```

### Isolation

1. **Si API uniquement** : Redémarrer le service
2. **Si base de données** : Vérifier l'intégrité
3. **Si LLM** : Basculer en mode fallback (pas de clé API)

### Communication

- Notifier l'équipe
- Documenter l'incident
- Garder les logs

---

## 3. Remédiation

### Problèmes courants

#### 1. API ne répond pas

```bash
# Redémarrer le service
systemctl restart medical-ai-assistant
# ou Docker
docker compose restart

# Vérifier les logs
docker compose logs --tail=50
```

#### 2. Erreur LLM (Groq)

```bash
# Vérifier la clé API
echo $GROQ_API_KEY
# Vérifier que le modèle est disponible
# https://console.groq.com
```

#### 3. Base de données corrompue

```bash
# Sauvegarder et recréer
cp data/medical_ai.db data/medical_ai.db.bak
rm data/medical_ai.db
# Redémarrer (la base sera recréée)
docker compose restart
```

#### 4. Erreur de déploiement Render

1. Vérifier les logs Render Dashboard
2. Vérifier les variables d'environnement
3. Redéployer depuis GitHub

### Procédure de redémarrage

```bash
# Docker
docker compose down
docker compose up --build -d

# Local
pkill -f "uvicorn"
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
```

---

## 4. Rétablissement

### Vérifications post-incident

```bash
# 1. Health check
curl http://localhost:8000/health
# Attendu : {"status": "healthy"}

# 2. Test fonctionnel
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test"}'
# Attendu : réponse JSON valide

# 3. Dashboard
curl http://localhost:8000/dashboard
# Attendu : page HTML

# 4. Métriques
curl http://localhost:8000/metrics
# Attendu : métriques à jour
```

### Critères de retour à la normale

- ✅ Health check ok
- ✅ Chat fonctionnel
- ✅ Dashboard accessible
- ✅ Métriques normales
- ✅ Taux d'erreur < 5%
- ✅ Temps de réponse < 2s

---

## 5. Post Mortem

### Template

```markdown
# Post Mortem - [Date]

## Résumé
- **Incident** : [Titre]
- **Durée** : [Début] → [Fin]
- **Impact** : [Description]
- **Sévérité** : [Critique/Élevé/Moyen/Faible]

## Chronologie
| Heure | Événement |
|-------|-----------|
| HH:MM | Détection |
| HH:MM | Containment |
| HH:MM | Remédiation |
| HH:MM | Rétablissement |

## Cause racine
[Description détaillée]

## Actions correctives
- [ ] [Action 1]
- [ ] [Action 2]

## Leçons apprises
1. [Leçon 1]
2. [Leçon 2]

## Annexes
- Logs : [lien]
- Métriques : [lien]
```

### Exemple

```markdown
# Post Mortem - 2026-06-26

## Résumé
- **Incident** : API down après déploiement
- **Durée** : 14:30 → 14:45 (15 minutes)
- **Impact** : 100% des requêtes en échec
- **Sévérité** : Critique

## Cause racine
Variable GROQ_API_KEY manquante après redéploiement.

## Actions correctives
- [x] Ajouter vérification pré-déploiement des variables d'env
- [x] Ajouter health check

## Leçons apprises
1. Toujours vérifier les variables d'environnement
2. Les health checks doivent être redondants
```

---

## Checklist de Résolution

- [ ] Incident détecté et confirmé
- [ ] Impact évalué
- [ ] Containment effectué
- [ ] Cause racine identifiée
- [ ] Correctif appliqué
- [ ] Tests de vérification passés
- [ ] Retour à la normale confirmé
- [ ] Post mortem rédigé
- [ ] Actions correctives planifiées
