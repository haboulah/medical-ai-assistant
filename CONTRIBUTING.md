# Contribuer a Medical AI Assistant

Merci de votre interet pour contribuer a ce projet. Les contributions sont les bienvenues sous forme de rapports de bugs, suggestions d'amelioration, ou pull requests.

## Guide de contribution

### Signaler un bug

1. Verifiez que le bug n'a pas deja ete signale dans les Issues
2. Ouvrez une nouvelle Issue avec un titre clair et descriptif
3. Incluez les etapes pour reproduire le probleme
4. Indiquez votre environnement (OS, version Python, etc.)

### Proposer une amelioration

1. Ouvrez une Issue pour discuter de l'amelioration
2. Decrivez clairement le besoin et la solution proposee
3. Attendez un retour avant de commencer le developpement

### Pull Request

1. Forkez le depot
2. Creez une branche : `git checkout -b feature/ma-fonctionnalite`
3. Assurez-vous que les tests passent : `pytest tests/`
4. Verifiez le linting : `ruff check app/ tests/`
5. Formatez le code : `black app/ tests/`
6. Commitez avec un message clair
7. Poussez la branche et ouvrez une Pull Request

### Normes de code

- Respectez PEP 8 via Ruff
- Formatez avec Black (line-length 100)
- Ajoutez des tests pour toute nouvelle fonctionnalite
- Documentez les fonctions avec des docstrings
- Utilisez des types (annotations Python)
- Suivez l'architecture existante (DDD, clean architecture)

### Environnement de developpement

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Ajoutez GROQ_API_KEY dans .env
```

## Code de conduite

Ce projet suit un code de conduite strict. Tout comportement irrespectueux ou discriminatoire ne sera pas tolere. Signalez tout incident via les Issues du depot.
