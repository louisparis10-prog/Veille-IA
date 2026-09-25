# GitHub → Render → Neon PostgreSQL

Le dossier `veille-app` est la racine du dépôt GitHub. Les fichiers SQLite, les secrets et les dépendances locales sont exclus de Git. Le contenu reste en français.

## Installation actuelle

- Application : https://signal-veille-ia.onrender.com
- Dépôt public, autorisé par le propriétaire : https://github.com/louisparis10-prog/Veille-IA
- Render : service `signal-veille-ia`, plan gratuit, région Ohio.
- Neon : projet « Veille IA », base `neondb`, PostgreSQL 18, région Ohio.
- Import initial vérifié : 75 articles, 150 traductions, 4 sources et les paramètres locaux.
- Identifiant d'accès : `louis`. Le mot de passe est défini uniquement dans le secret Render `APP_PASSWORD`.

## 1. Dépôt GitHub

Le code est publié dans `louisparis10-prog/Veille-IA` sur `main`. Le flux de vérification teste SQLite, le serveur web, PostgreSQL 18 et l'import des données avant le déploiement automatique Render.

## 2. Projet Neon

Le projet du propriétaire se trouve en région Ohio avec la base `neondb`. Récupérer la chaîne de connexion dans **Connect**. La connexion mutualisée est compatible avec l'application. Conserver les paramètres TLS de Neon. Ne jamais coller la chaîne dans un message, un fichier suivi ou un journal.

## 3. Service Render

Le service a été créé depuis le dépôt GitHub, avec les mêmes réglages que `render.yaml`. Il utilise le plan gratuit, en région Ohio. Pour recréer une installation, le Blueprint peut aussi être utilisé. Secrets :

| Variable | Valeur |
| --- | --- |
| `DATABASE_URL` | Chaîne de connexion PostgreSQL Neon |
| `APP_USERNAME` | Identifiant personnel (défaut : `louis`) |
| `APP_PASSWORD` | Mot de passe personnel unique, au moins 16 caractères |
| `OPENAI_API_KEY` | Facultative, pour les analyses IA et les questions |

Le navigateur demandera l'identifiant et le mot de passe à l'ouverture. Le service refuse de démarrer en production si la base Neon ou la protection d'accès ne sont pas configurées. Le point `/healthz` est public mais n'affiche aucune donnée utilisateur. Toutes les données et les fichiers de l'interface sont protégés.

Render exécute `python manage.py init` puis Gunicorn. Les fichiers locaux Render ne servent jamais à conserver les données. Le déploiement suit la réussite des vérifications GitHub.

## 4. Reprendre les données locales

Après création des tables, exécuter depuis ce dossier, dans une session où `DATABASE_URL` est définie de manière privée :

```text
python manage.py migrate --source veille.sqlite3
python manage.py check
```

L'import lit la base locale sans la modifier, garde les identifiants, dates, originaux, traductions, notes, favoris et statuts. Les doublons sont ignorés et la séquence des identifiants de projets est réajustée. Le profil de centres d'intérêt local remplace le profil par défaut de la cible. Éviter de refaire cet import après avoir modifié le profil en ligne.

Ne pas transférer la base SQLite dans GitHub. Si les données sont déjà présentes en ligne, l'import conserve les versions en ligne des articles, projets et traductions.

## 5. Collecte quotidienne indépendante du PC

Dans les secrets GitHub Actions du dépôt, ajouter `DATABASE_URL` et, facultativement, `OPENAI_API_KEY`. Lancer une première fois **Actions → Collecte quotidienne → Run workflow**.

Le flux tourne ensuite à 05 h 17 UTC (06 h 17 en hiver et 07 h 17 en été à Paris). GitHub peut retarder les exécutions planifiées : ce n'est pas une garantie horaire stricte. Il collecte et traduit directement dans Neon, même si le service Render est en veille. Un verrou PostgreSQL évite les collectes concurrentes. En cas d'échec de toutes les sources ou de traductions manquantes, le flux signale un échec.

Le plan Render gratuit peut se mettre en veille et ralentir la première ouverture. Un hébergement constamment actif nécessiterait un plan payant ; aucun plan payant n'est créé par cette configuration. Vérifier les quotas des comptes GitHub et Neon avant une utilisation intensive.

## Développement local

```text
pip install -r requirements.txt
python -m unittest test_server test_web
python server.py
```

Sans `DATABASE_URL`, le serveur local conserve SQLite. La version Render utilise `app:app` et PostgreSQL. Ne pas lancer les tests unitaires contre une base de production. Les tests PostgreSQL sont limités à une instance locale jetable via `TEST_POSTGRES_URL` et sont exécutés automatiquement dans GitHub Actions.

Références : [Render et Flask](https://render.com/docs/deploy-flask), [Blueprint Render](https://render.com/docs/blueprint-spec), [Plan gratuit Render](https://render.com/docs/free), [Python avec Neon](https://neon.com/docs/guides/python).
