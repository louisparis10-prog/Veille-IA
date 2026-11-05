"""Configuration lue automatiquement par gunicorn au démarrage sur Render.

Un seul processus (mémoire de l'offre gratuite), mais plusieurs fils : l'interface reste
réactive pendant une collecte, une traduction ou le préchauffage au réveil du service.
"""
import os

workers = int(os.environ.get('WEB_CONCURRENCY', '1'))
threads = 4
timeout = 120
graceful_timeout = 30
