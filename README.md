# Signal — Veille IA et digitalisation

Application personnelle en français pour collecter les actualités officielles, repérer des opportunités et suivre un parcours **Idée → Test → Projet → Déployé**.

## Fonctionnement actuel

L'application fonctionne uniquement sur le PC de l'utilisateur. Le service Render a été supprimé le 28 septembre 2026 et la collecte GitHub Actions vers Neon a été arrêtée. GitHub reste une sauvegarde du code. L'ancienne base Neon est conservée comme sauvegarde et n'est pas utilisée par le lancement local.

## Utilisation locale

Python 3.11+ suffit : double-cliquer sur le raccourci **Signal — Veille IA** du Bureau, ou sur `Lancer.cmd`. Le lanceur démarre le serveur et ouvre l’application dans une fenêtre Edge dédiée. Il n’affiche plus de fenêtre noire. Quand cette fenêtre est fermée, le serveur local, le modèle IA et Foundry Local sont arrêtés afin de libérer la mémoire. Les données restent dans `veille.sqlite3`. Ce fichier est exclu de Git.

Configuration minimale conseillée : Windows 10 ou 11, 16 Go de RAM, environ 5 Go d'espace disque avec le modèle IA local et un navigateur récent. Aucun GPU dédié, serveur externe ou abonnement payant n'est nécessaire. Internet sert à installer le modèle puis à récupérer et traduire les nouvelles actualités.

## Fonctions

- Assistant IA entièrement local avec Microsoft Foundry Local et Phi-4 Mini, adapté à 16 Go de RAM : explication des articles, questions sur les pistes et recherche dans les extraits enregistrés.
- Trois pistes quotidiennes préparées : deux applications et une création, issues de 60 fiches pédagogiques. Rotation sans répétition pendant 20 jours puis reprise ; historique conservé sur 30 jours.
- « Comprendre / poser une question » permet d’interroger directement l’IA locale. La copie manuelle de la question reste disponible comme solution de secours.
- 26 sources couvrant les principaux acteurs IA : OpenAI, Microsoft, Google/DeepMind, Anthropic, Meta, AWS, NVIDIA, Mistral, DeepSeek, Alibaba/Qwen, Hugging Face, IBM, Cohere, xAI, Perplexity, Adobe, Stability AI, Runway, ElevenLabs, Midjourney, Apple et Salesforce. Flux officiels et relais Google Actualités limités aux domaines officiels ; couverture non exhaustive, sans API payante.
- Lecture de 12 entrées récentes par source et conservation des publications qui fournissent un extrait fiable, avec historique et dédoublonnage par URL ou titre.
- Titres et extraits traduits en français et conservés en base ; originaux préservés.
- Chaque actualité contient un extrait réellement récupéré sur la publication officielle, traduit en français, puis une fiche de lecture : informations à retenir, intérêt possible, vérifications et lien direct. Les résultats sans extrait fiable ne sont plus conservés.
- Synthèse déterministe des trois articles les mieux classés, dates et liens vers les sources.
- Catégories, pertinence par mots-clés et pistes d’usage présentées comme des hypothèses.
- Recherche et filtre par acteur/source, favoris, lecture, idées, tests, projets, notes et progression.
- Aucune API payante n’est activée. Les questions, notes et extraits traités par l’assistant local restent sur le PC.
- Interface adaptée aux mobiles, thèmes clair et sombre.

## Services externes et limites

La traduction utilise un point d’accès Google sans clé et sans garantie de disponibilité. Seuls les titres et extraits publics sont transmis ; jamais les notes personnelles. Les traductions manquantes sont signalées en français et réessayées lors de la prochaine collecte.

L’assistant utilise par défaut `phi-4-mini-instruct-openvino-gpu` via Microsoft Foundry Local. Pour une question, il reçoit les extraits locaux les plus pertinents et les notes/projets enregistrés. Il ne consulte pas les pages complètes et ne fait pas de recherche web générale. Les scores des articles restent calculés par mots-clés afin de ne pas faire travailler le modèle pendant toute la collecte.

Lorsque le PC disposera de 32 Go de RAM, un modèle local 7B ou plus pourra remplacer Phi-4 Mini. Phi-4 Mini reste le réglage adapté à 16 Go sur ce PC.

En local, la collecte se lance au démarrage si elle est nécessaire. Le PC doit être allumé et connecté à Internet. L'application et les données déjà enregistrées restent consultables sans connexion.

La coordination des collectes utilise dans Neon un bail d'une heure. La connexion est libérée pendant les téléchargements et traductions, ce qui évite qu'un long traitement soit interrompu par le pooler PostgreSQL.

## Vérifications

```text
pip install -r requirements.txt
python -m unittest test_server test_web test_postgres
node --check public/app.js
```

Les tests PostgreSQL utilisent une base locale jetable via `TEST_POSTGRES_URL` et sont ignorés sans elle. Le flux de vérification GitHub crée automatiquement un PostgreSQL 18. Ne jamais utiliser une base de production pour les tests.

Évolutions non incluses : catalogue d’outils, formations, bibliothèque de prompts, alertes externes, compétences et authentification multi-utilisateur.
