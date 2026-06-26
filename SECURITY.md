# Securite

## Signaler une vulnerabilite

La securite est une priorite pour ce projet, en particulier parce qu'il traite des donnees de sante.

Si vous decouvrez une vulnerabilite de securite, merci de la signaler de maniere responsable :

1. **Ne pas creer d'Issue publique** pour les vulnerabilites
2. Envoyer un email prive a l'adresse indiquee dans le profil GitHub du mainteneur
3. Decrire clairement le probleme et les etapes pour le reproduire

## Perimetre

Les points d'attention couverts par cette politique :

- Exposition de donnees patients
- Injection de code ou de promts LLM
- Fuite de la cle API Groq
- Acces non autorise aux endpoints
- Securite de la base de donnees SQLite

## Bonnes pratiques

- Ne jamais commit de fichier `.env` contenant des cles reelles
- Utiliser des tokens d'acces pour les deploiements
- Activer l'authentification par `API_KEY` en production
- Limiter les logs contenant des donnees personnelles
