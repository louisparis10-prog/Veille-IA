# Signal — Veille IA et digitalisation

Application personnelle en français pour collecter les actualités officielles, repérer des opportunités et suivre un parcours **Idée → Test → Projet → Déployé**.

## Architecture en ligne

- **GitHub** : dépôt public autorisé par le propriétaire, tests et collecte quotidienne planifiée. Les données et secrets sont exclus du dépôt.
- **Render** : serveur Flask/Gunicorn protégé par identifiant et mot de passe ; configuration `render.yaml`.
- **Neon PostgreSQL** : articles, traductions, favoris, notes, projets et progression.

Application déployée : https://signal-veille-ia.onrender.com. Dépôt : https://github.com/louisparis10-prog/Veille-IA. Les données sont conservées dans le projet Neon « Veille IA », en région Ohio. Voir [DEPLOIEMENT.md](DEPLOIEMENT.md).

## Utilisation locale

Python 3.11+ suffit pour la version SQLite : double-cliquer sur `Lancer.cmd` ou lancer `python server.py`, puis ouvrir http://127.0.0.1:8765. Les données restent dans `veille.sqlite3`. Ce fichier est exclu de Git. Pour tester Flask et PostgreSQL, installer `requirements.txt`.

## Fonctions

- Quatre flux officiels : OpenAI, Microsoft 365, Power BI et Microsoft Fabric.
- Collecte des 25 dernières entrées de chaque flux, historique et dédoublonnage par URL ou titre.
- Titres et extraits traduits en français et conservés en base ; originaux préservés.
- Synthèse déterministe des trois articles les mieux classés, dates et liens vers les sources.
- Catégories, pertinence par mots-clés et pistes d’usage présentées comme des hypothèses.
- Recherche, favoris, lecture, idées, tests, projets, notes et progression.
- Analyse et assistant IA facultatifs via `OPENAI_API_KEY`, conservée côté serveur.
- Interface adaptée aux mobiles, thèmes clair et sombre.

## Services externes et limites

La traduction utilise un point d’accès Google sans clé et sans garantie de disponibilité. Seuls les titres et extraits publics sont transmis ; jamais les notes personnelles. Les traductions manquantes sont signalées en français et réessayées lors de la prochaine collecte.

L’IA configurée analyse les extraits des nouveaux articles. Pour une question, elle reçoit les extraits sélectionnés et les notes/projets. Modèle configurable par `OPENAI_MODEL` (défaut : `gpt-4.1-mini`). Des frais API peuvent s’appliquer. Sans clé, les scores reposent explicitement sur des mots-clés. L’assistant ne consulte pas les pages complètes et ne fait pas de recherche web générale.

La collecte GitHub Actions est programmée à 05 h 17 UTC et reste indépendante du PC et de la mise en veille Render. Elle nécessite le secret `DATABASE_URL` dans GitHub. GitHub peut retarder cet horaire. En local, garder le serveur lancé ; rattrapage au démarrage.

## Vérifications

```text
pip install -r requirements.txt
python -m unittest test_server test_web test_postgres
node --check public/app.js
```

Les tests PostgreSQL utilisent une base locale jetable via `TEST_POSTGRES_URL` et sont ignorés sans elle. Le flux de vérification GitHub crée automatiquement un PostgreSQL 18. Ne jamais utiliser une base de production pour les tests.

Évolutions non incluses : catalogue d’outils, formations, bibliothèque de prompts, alertes externes, compétences et authentification multi-utilisateur. La version hébergée reste un espace personnel.
