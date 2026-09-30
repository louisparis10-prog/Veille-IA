# Signal — Veille IA et digitalisation

Application personnelle en français pour collecter les actualités officielles, repérer des opportunités et suivre un parcours **Idée → Test → Projet → Déployé**.

## Fonctionnement actuel

L'application web fonctionne sur Render et utilise PostgreSQL sur Neon. Le navigateur affiche l'interface ; aucun serveur, modèle IA, Ollama ou Foundry Local n'est lancé sur le poste de l'utilisateur.

## Fonctions

- Trois pistes quotidiennes préparées : deux applications et une création, issues de 60 fiches pédagogiques. Rotation sans répétition pendant 20 jours puis reprise ; historique conservé sur 30 jours.
- « Comprendre / poser une question » prépare un texte clair à copier dans ChatGPT ou dans un outil approuvé par l’entreprise.
- 26 sources couvrant les principaux acteurs IA : OpenAI, Microsoft, Google/DeepMind, Anthropic, Meta, AWS, NVIDIA, Mistral, DeepSeek, Alibaba/Qwen, Hugging Face, IBM, Cohere, xAI, Perplexity, Adobe, Stability AI, Runway, ElevenLabs, Midjourney, Apple et Salesforce. Flux officiels et relais Google Actualités limités aux domaines officiels ; couverture non exhaustive, sans API payante.
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
