# Signal — Veille IA et digitalisation

Application personnelle en français pour collecter les actualités officielles, repérer des opportunités et suivre un parcours **Idée → Test → Projet → Déployé**.

## Fonctionnement actuel

L'application web fonctionne sur Render et utilise PostgreSQL sur Neon. Le navigateur affiche l'interface ; aucun serveur, modèle IA, Ollama ou Foundry Local n'est lancé sur le poste de l'utilisateur.

## Fonctions

- Trois pistes quotidiennes préparées : deux applications et une création, issues de 60 fiches pédagogiques. Rotation sans répétition pendant 20 jours puis reprise ; historique conservé sur 30 jours.
- « Comprendre / poser une question » prépare un texte clair à copier dans ChatGPT ou dans un outil approuvé par l’entreprise.
- Page de connexion intégrée (identifiant et mot de passe, session signée « Rester connecté 30 jours », déconnexion). Identifiants lus dans `APP_USERNAME` et `APP_PASSWORD` (12 caractères minimum) ; sans `APP_PASSWORD` en production, l'application reste verrouillée. `SECRET_KEY` est facultative.
- 33 sources en trois familles :
  - **Outils IA** : OpenAI, Microsoft 365, Copilot Studio, Power Platform, Power BI, Fabric, Google/Gemini, DeepMind, Anthropic, Mistral, Meta, AWS, NVIDIA, DeepSeek, Qwen, Hugging Face, IBM, Cohere, xAI, Perplexity, Adobe, Salesforce ;
  - **Industrie** : Siemens (IA industrielle), ABB (process et papier), L'Usine Digitale ;
  - **Papeterie** : Valmet, ANDRITZ, Voith Paper, Papnews, Pulp & Paper Canada, et deux recherches de presse « IA et papeterie » (anglais et français).
  Flux officiels, ou relais Google Actualités limités au domaine officiel ou à une recherche ciblée ; couverture non exhaustive, sans API payante.
- Pertinence métier (`relevance.py`) : thèmes Papeterie et process, Industrie et maintenance, Copilot et bureautique, Données et décisionnel, Automatisation et agents ; outils cités (ChatGPT, Copilot, Claude, Gemini, Power BI…) ; badge « Nouveauté » pour les annonces de fonctionnalités ; pages d'auteur, de recrutement ou d'événement écartées.
- Lecture de 12 entrées récentes par source et conservation des publications qui fournissent un extrait fiable, avec historique et dédoublonnage par URL ou titre.
- Titres et extraits traduits en français et conservés en base ; originaux préservés.
- Chaque actualité contient un extrait réellement récupéré sur la publication officielle, traduit en français, puis une fiche de lecture : informations à retenir, intérêt possible, vérifications et lien direct. Les résultats sans extrait fiable ne sont plus conservés.
- Synthèse déterministe des trois articles les mieux classés, dates et liens vers les sources.
- Catégories, pertinence par mots-clés et pistes d’usage présentées comme des hypothèses.
- Recherche et filtre par acteur/source, favoris, lecture, idées, tests, projets, notes et progression.
- Aucune API payante n’est activée par défaut.
- Interface adaptée aux mobiles, thèmes clair et sombre.

## Services externes et limites

La traduction utilise un point d’accès Google sans clé et sans garantie de disponibilité. Seuls les titres et extraits publics sont transmis ; jamais les notes personnelles. Les traductions manquantes sont signalées en français et réessayées lors de la prochaine collecte.

La collecte et les traitements s'exécutent sur l'hébergement Render. Le poste de l'utilisateur n'a besoin que d'un navigateur.

La coordination des collectes utilise dans Neon un bail d'une heure. La connexion est libérée pendant les téléchargements et traductions, ce qui évite qu'un long traitement soit interrompu par le pooler PostgreSQL.

## Vérifications

```text
pip install -r requirements.txt
python -m unittest test_server test_web test_postgres
node --check public/app.js
```

Les tests PostgreSQL utilisent une base locale jetable via `TEST_POSTGRES_URL` et sont ignorés sans elle. Le flux de vérification GitHub crée automatiquement un PostgreSQL 18. Ne jamais utiliser une base de production pour les tests.

Évolutions non incluses : catalogue d’outils, formations, bibliothèque de prompts, alertes externes, compétences et authentification multi-utilisateur.
