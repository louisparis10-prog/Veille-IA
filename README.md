# Signal — Veille IA et digitalisation

Application personnelle en français pour collecter les actualités officielles, repérer des opportunités et suivre un parcours **Idée → Test → Projet → Déployé**.

## Fonctionnement actuel

L'application fonctionne uniquement sur le PC de l'utilisateur. Le service Render a été supprimé le 28 septembre 2026 et la collecte GitHub Actions vers Neon a été arrêtée. GitHub reste une sauvegarde du code. L'ancienne base Neon est conservée comme sauvegarde et n'est pas utilisée par le lancement local.

## Utilisation locale

Python 3.11+ suffit : double-cliquer sur `Lancer.cmd`. Le lanceur vérifie Python, démarre le serveur, puis ouvre http://127.0.0.1:8765. Les données restent dans `veille.sqlite3`. Ce fichier est exclu de Git. La fenêtre noire doit rester ouverte pendant l'utilisation.

Configuration minimale conseillée : Windows 10 ou 11, 2 Go de mémoire disponible, 200 Mo d'espace disque et un navigateur récent. Aucun GPU, serveur externe ou abonnement payant n'est nécessaire. Internet sert uniquement à récupérer et traduire les nouvelles actualités.

## Fonctions

- Mode sans frais API : aucun appel OpenAI tant que `ALLOW_PAID_AI` n’est pas explicitement activé. Une clé seule ne déclenche aucune dépense.
- Trois pistes quotidiennes préparées : deux applications et une création, issues de 60 fiches pédagogiques. Rotation sans répétition pendant 20 jours puis reprise ; historique conservé sur 30 jours.
- « Comprendre / poser une question » prépare un message modifiable à copier dans le compte ChatGPT de l’utilisateur. Ce n’est pas une conversation API intégrée ; aucun texte n’est envoyé automatiquement.
- 26 sources couvrant les principaux acteurs IA : OpenAI, Microsoft, Google/DeepMind, Anthropic, Meta, AWS, NVIDIA, Mistral, DeepSeek, Alibaba/Qwen, Hugging Face, IBM, Cohere, xAI, Perplexity, Adobe, Stability AI, Runway, ElevenLabs, Midjourney, Apple et Salesforce. Flux officiels et relais Google Actualités limités aux domaines officiels ; couverture non exhaustive, sans API payante.
- Lecture de 12 entrées récentes par source et conservation des publications qui fournissent un extrait fiable, avec historique et dédoublonnage par URL ou titre.
- Titres et extraits traduits en français et conservés en base ; originaux préservés.
- Chaque actualité contient un extrait réellement récupéré sur la publication officielle, traduit en français, puis une fiche de lecture : informations à retenir, intérêt possible, vérifications et lien direct. Les résultats sans extrait fiable ne sont plus conservés.
- Synthèse déterministe des trois articles les mieux classés, dates et liens vers les sources.
- Catégories, pertinence par mots-clés et pistes d’usage présentées comme des hypothèses.
- Recherche et filtre par acteur/source, favoris, lecture, idées, tests, projets, notes et progression.
- Analyse et assistant IA facultatifs via `OPENAI_API_KEY` et `ALLOW_PAID_AI=true`, désactivés par défaut conformément au souhait de ne rien payer.
- Interface adaptée aux mobiles, thèmes clair et sombre.

## Services externes et limites

La traduction utilise un point d’accès Google sans clé et sans garantie de disponibilité. Seuls les titres et extraits publics sont transmis ; jamais les notes personnelles. Les traductions manquantes sont signalées en français et réessayées lors de la prochaine collecte.

L’IA configurée analyse les extraits des nouveaux articles. Pour une question, elle reçoit les extraits sélectionnés et les notes/projets. Modèle configurable par `OPENAI_MODEL` (défaut : `gpt-4.1-mini`). Des frais API peuvent s’appliquer. Sans clé, les scores reposent explicitement sur des mots-clés. L’assistant ne consulte pas les pages complètes et ne fait pas de recherche web générale.

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
