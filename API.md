# API Documentation

## Overview

Base URL: `http://localhost:8000`

All responses are in JSON format.

## Endpoints

---

### GET /

Root endpoint with API information.

**Response:**
```json
{
  "name": "Medical AI Assistant",
  "version": "1.0.0",
  "description": "AI Medical Pre-Diagnosis Assistant",
  "docs": "/docs",
  "redoc": "/redoc",
  "dashboard": "/dashboard"
}
```

---

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "ok",
  "llm": "configured",
  "timestamp": "2026-01-01T00:00:00"
}
```

---

### POST /chat

Process a chat message through the multi-agent workflow.

**Request:**
```json
{
  "message": "J'ai de la fièvre, je tousse et je suis fatigué."
}
```

**Response:**
```json
{
  "correlation_id": "uuid",
  "symptoms": {
    "symptoms": ["Fièvre", "Toux", "Fatigue"],
    "raw_text": "J'ai de la fièvre, je tousse et je suis fatigué."
  },
  "risk": {
    "level": "LOW",
    "justification": "Les symptômes sont légers..."
  },
  "medical_advice": {
    "advice": "Reposez-vous et hydratez-vous...",
    "disclaimer": "⚠️ Avertissement..."
  },
  "monitoring": {
    "correlation_id": "uuid",
    "duration_ms": 150.5,
    "agents_executed": ["Supervisor", "SymptomAnalysis", "RiskAssessment", "MedicalAdvice", "Monitoring"],
    "status": "success"
  },
  "disclaimer": "⚠️ Avertissement..."
}
```

---

### GET /metrics

Application metrics.

**Response:**
```json
{
  "total_requests": 42,
  "success_rate": 95.24,
  "avg_duration_ms": 150.5,
  "max_duration_ms": 500.2,
  "min_duration_ms": 8.3,
  "risk_distribution": {"LOW": 30, "MEDIUM": 10, "HIGH": 2},
  "agent_calls": {"Supervisor": 42, "SymptomAnalysis": 42},
  "memory_usage_mb": 91.8,
  "cpu_percent": 21.7
}
```

---

### GET /dashboard

Web dashboard (HTML).

### GET /dashboard/data

Dashboard JSON data for Chart.js.

### GET /history

Recent conversation history.

### GET /logs

Recent application logs.

### GET /version

Version information.

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid input) |
| 422 | Validation Error |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Headers

- `X-Correlation-ID` : Added to every response for request tracing.
