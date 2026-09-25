"""Sélection quotidienne sans API payante, à partir de fiches pédagogiques."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import server

CONTEXTS=[
    ('les changements de format','un changement de référence produit','les heures de début et fin et les difficultés rencontrées'),
    ('les défauts d’emballage','un carton abîmé ou une étiquette mal placée','le type de défaut, le produit et une photo autorisée'),
    ('les arrêts courts','une machine arrêtée quelques minutes','l’heure, la durée et la cause indiquée par l’opérateur'),
    ('les demandes de maintenance','une fuite ou un bruit inhabituel','la machine, le symptôme et la date du signalement'),
    ('les consommations de matière','un écart entre matière utilisée et quantité produite','la quantité entrée, les pièces bonnes et les rebuts'),
    ('les contrôles qualité','une mesure hors de la plage attendue','la mesure, la valeur attendue et le lot'),
    ('les stocks de pièces','une pièce de rechange introuvable','la référence, la quantité et l’emplacement'),
    ('les actions d’amélioration','une action décidée en réunion qui reste sans suivi','l’action, le responsable et la date prévue'),
    ('les réglages de démarrage','plusieurs essais avant de sortir un produit conforme','les réglages essayés et les résultats observés'),
    ('les consommations d’énergie','une machine qui consomme beaucoup à l’arrêt','les relevés d’énergie et les périodes de marche'),
]

def pool():
    output=[]
    for n,(subject,example,fields) in enumerate(CONTEXTS):
        common={'source':'','effort':'Prototype · 1 à 3 jours','group':'industrie'}
        variants=[
            ('Carnet numérique pour '+subject,'Remplacer les papiers dispersés par une liste facile à retrouver.',f'Créer un formulaire avec {fields}. Saisir cinq exemples fictifs. Filtrer la liste par date.','Un collègue retrouve un cas précis en moins d’une minute.','Un tableur suffit pour le premier essai ; une petite application web peut ensuite remplacer le fichier.'),
            ('Tableau de bord pour '+subject,'Voir ce qui revient le plus souvent et choisir quoi améliorer en premier.',f'Rassembler dix exemples avec {fields}. Compter les cas par catégorie dans un tableur. Afficher les trois catégories les plus fréquentes.','Les totaux correspondent au fichier et l’équipe identifie un sujet prioritaire.','Un tableur et un graphique ; le classement vient de calculs vérifiables.'),
            ('Rappel de suivi pour '+subject,'Éviter qu’un problème signalé reste oublié.',f'Créer une liste de cinq cas avec {fields}. Ajouter un responsable et une date de suivi. Afficher en rouge les cas en retard.','Chaque cas possède une prochaine action et les retards apparaissent correctement.','Un tableau de suivi avec des règles de couleur ; commencer sans notifications.'),
            ('Base de solutions pour '+subject,'Retrouver ce qui a déjà été essayé au lieu de repartir de zéro.',f'Décrire cinq cas avec {fields}. Ajouter la solution validée et son résultat. Tester une recherche par mot avec un collègue.','Un collègue retrouve la solution d’un cas connu et sa limite d’utilisation.','Un document partagé ou un moteur de recherche ; seules les solutions validées sont proposées.'),
        ]
        for v,(title,benefit,trial,success,tools) in enumerate(variants):
            output.append(dict(common,id=f'free-app-{n}-{v}',title=title,benefit=benefit+' Exemple : '+example+'.',trial=trial,success=success,tools=tools))
        for v,(medium,action) in enumerate([('Une vidéo explicative','un scénario de vidéo de 45 secondes, composé de trois plans'),('Un quiz pédagogique','cinq questions à choix multiple avec les réponses expliquées')]):
            output.append(dict(id=f'free-create-{n}-{v}',group='creation',title=medium+' sur '+subject,benefit=f'Aider un collègue à comprendre {example}, avec des mots simples.',effort='Premier essai · 30 à 60 minutes',trial=f'Prendre un exemple fictif. Demander à ChatGPT {action}. Faire relire le résultat par un collègue avant de le mettre en forme.',success='Le collègue sait expliquer le problème et la première action à faire.',tools='ChatGPT dans votre compte habituel, selon ses limites disponibles ; aucun achat nécessaire pour préparer le texte. Pour une vidéo finale, filmer un exemple autorisé avec votre téléphone.',source=''))
    return output

def read_daily():
    with server.conn() as c:
        row=c.execute("SELECT value FROM settings WHERE key='daily_ideas'").fetchone()
    return json.loads(row['value']) if row else {'date':None,'ideas':[],'status':'La sélection gratuite du jour sera préparée à la prochaine collecte.'}

def generate_daily():
    previous=read_daily()
    today=datetime.now(ZoneInfo('Europe/Paris')).date().isoformat()
    if previous.get('date')==today: return {'status':'already_generated','date':today}
    seen=set(previous.get('seen',[])); selected=[]; all_ideas=pool()
    # Parcourir les thèmes avant de revenir à une autre variante du même thème.
    all_ideas.sort(key=lambda i:(int(i['id'].split('-')[-1]),int(i['id'].split('-')[-2])))
    for group,count in [('industrie',2),('creation',1)]:
        group_pool=[i for i in all_ideas if i['group']==group]
        available=[i for i in group_pool if i['id'] not in seen]
        if len(available)<count:
            seen.difference_update(i['id'] for i in group_pool)
            available=group_pool
        for i in available[:count]:
            selected.append(dict(i,date=today)); seen.add(i['id'])
    archive=(previous.get('archive',[])+previous['ideas'])[-90:]
    value={'date':today,'ideas':selected,'archive':archive,'seen':sorted(seen),'status':'3 pistes du jour, sélectionnées sans IA payante dans 60 fiches préparées. Rotation sans répétition pendant 20 jours, puis reprise du catalogue.'}
    with server.conn() as c:
        c.execute("INSERT INTO settings(key,value) VALUES('daily_ideas',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(json.dumps(value,ensure_ascii=False),))
    return {'status':'generated','count':3,'date':today}

def explain(body):
    raise server.AIUnavailable('Mode sans frais API : préparez votre question et copiez-la dans ChatGPT pour une réponse personnalisée.')
