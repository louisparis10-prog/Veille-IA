"""Pertinence métier sans IA payante : outils cités, nouveautés et lien avec l'industrie papetière.

Les textes analysés combinent l'original (souvent en anglais) et sa traduction française,
afin que les centres d'intérêt saisis en français trouvent aussi leurs correspondances.
"""
import re

def _pattern(terms):
    parts=[]
    for term in terms:
        # « * » marque une racine (manufactur* → manufacturing, jumeau* numérique* → jumeaux numériques).
        escaped=re.escape(term.lower()).replace(r'\ ',r'\s+').replace(r'\*',r'\w*')
        parts.append(r'\b'+escaped+('' if term.endswith('*') else r'\b'))
    return re.compile('|'.join(parts),re.IGNORECASE)

# (catégorie, poids, mots-clés). L'ordre sert d'arbitrage en cas d'égalité.
THEMES=[
    ('Création (vidéo, image, audio)',28,['video generat*','text-to-video','image-to-video','AI video*','video model*','image generat*','text-to-image','AI image*','image model*','AI music','music generat*','voice clon*','text-to-speech','AI avatar*','Sora','Veo','Runway','Gen-4*','Kling','Luma','Dream Machine','Pika','Midjourney','FLUX.1','Black Forest Labs','Firefly','Imagen','Nano Banana','ElevenLabs','Suno','Udio','HeyGen','Synthesia','Google Flow','Canva','génér* de vidéo*','générat* vidéo','vidéo* IA','générat* d’images','génér* d’images','image* IA','musique IA','voix de synthèse','montage vidéo']),
    ('Assistants et modèles IA',22,['ChatGPT','Claude','Gemini','Le Chat','Grok','Perplexity','Llama','DeepSeek','Qwen','NotebookLM','GPT-*','large language model*','LLM*','reasoning model*','frontier model*','open-weight*','open weight*','model release','new model','modèle* de langage','modèle* d’IA','nouveau modèle','assistant* IA','chatbot*']),
    ('Papeterie et process',32,['paper mill*','papermaking','paper machine*','pulp','pulp and paper','tissue paper','paperboard','containerboard','corrugated','cellulose','wood fib*','papier*','papeterie*','papetier*','pâte à papier','machine à papier','carton*','cellulose','fibres de bois','bobine*','sécherie','Valmet','ANDRITZ','Voith','Metsä','Stora Enso','UPM','Smurfit','Sappi','Mondi']),
    ('Industrie et maintenance',24,['manufactur*','industrial','industry 4.0','factory','factories','shop floor','plant floor','production line*','predictive maintenance','maintenance','downtime','OEE','quality control','quality inspection','defect detection','digital twin*','IIoT','industrial IoT','sensor*','SCADA','manufacturing execution system*','PLC','process control','supply chain','energy efficiency','operators','industrie*','usine*','maintenance prédictive','contrôle qualité','jumeau* numérique*','capteur*','atelier*','ligne* de production','rebut*','opérateur*','Siemens','ABB','Rockwell','AVEVA','Schneider Electric','Honeywell']),
    ('Copilot et bureautique',20,['Copilot','Microsoft 365','Microsoft Teams','Outlook','Excel','PowerPoint','SharePoint','OneDrive','Microsoft Word','Copilot Chat','Copilot Notebooks','bureautique']),
    ('Données et décisionnel',16,['Power BI','Microsoft Fabric','Fabric','dashboard*','analytics','data warehouse','lakehouse','semantic model*','tableau* de bord','décisionnel','données de production']),
    ('Automatisation et agents',16,['Power Automate','Copilot Studio','Power Apps','Power Platform','agent*','agentic','workflow*','automation','automate*','RPA','n8n','automatisation','agentique']),
]
THEME_PATTERNS=[(name,weight,_pattern(words)) for name,weight,words in THEMES]

# Outils et produits IA reconnus, affichés comme étiquettes « Outils cités ».
TOOLS=['ChatGPT Agent','ChatGPT Atlas','ChatGPT Enterprise','ChatGPT','GPT-5','GPT-4o','Codex','Sora','Veo','Imagen','Nano Banana','Google Flow','Runway','Kling','Luma','Midjourney','ElevenLabs','Suno','HeyGen','Synthesia','Canva','OpenAI o3','Microsoft 365 Copilot','Copilot Studio','Copilot Chat','GitHub Copilot','Copilot','Power BI','Microsoft Fabric','Power Automate','Power Apps','Azure AI Foundry','Azure OpenAI','Dataverse','Claude','Claude Code','Gemini','NotebookLM','Google AI Studio','Vertex AI','Le Chat','Mistral','Llama','DeepSeek','Qwen','Grok','Perplexity','Agentforce','Amazon Bedrock','Amazon Q','SageMaker','Omniverse','Hugging Face','Firefly','watsonx','Industrial Copilot','Cohere','n8n','Valmet DNA','AVEVA']
TOOL_PATTERNS=[(tool,_pattern([tool])) for tool in TOOLS]

NEW_FEATURE=_pattern(['introducing','introduces','launch*','now available','generally available','general availability','new feature*','announcing','rolling out','available today','in preview','public preview','what’s new',"what's new",'released','new release','présente','lance*','désormais disponible','nouvelle* fonctionnalité*','nouveauté*','déploie'])
# Contenus peu utiles au quotidien : recrutement, événements, finance, marketing.
LOW_VALUE=_pattern(['webinar','conference','summit','podcast','hiring','residency','fellowship','internship','funding round','raises','Series A','Series B','earnings','quarterly results','sponsored','gala','award*','convention','registration opens'])
# Bruit fréquent des recherches papeterie : reconversions de sites en centres de données.
OFF_TOPIC=_pattern(['data center','data centre','datacenter','centre de données','centre de calcul*','supercalculateur','explosion','killed','research papers'])

NOISE_TITLE=re.compile(r'(,\s*(author|auteur)\b)|(\b(author|auteur)\s*[-–|])'
                       r'|\b(careers?|carrières?|job openings?|we.re hiring|start your career|privacy policy|cookie policy|terms of use|home page)\b'
                       r'|\((f/m/d|m/f/d|m/w/d|h/f|f/h)\)'
                       r'|^(home|accueil|news|blog|newsroom|products? and services.*)\s*([-–|]|$)',re.IGNORECASE)
NOISE_URL=re.compile(r'/(author|authors|auteur|tag|tags|category|categories|careers?|jobs?|search|people)(/|$|\?)',re.IGNORECASE)

OPPORTUNITIES={
    'Création (vidéo, image, audio)':'À essayer pour créer : tester sur un contenu interne (vidéo de consigne sécurité, tutoriel machine, visuel d’affichage atelier) avec des images non confidentielles. Vérifier les droits d’usage commercial avant toute diffusion.',
    'Assistants et modèles IA':'À connaître : repérer ce qui change dans votre usage quotidien (rédaction, analyse de fichiers Excel ou PDF, recherche). Tester la nouveauté sur une vraie tâche de la semaine et comparer avec votre outil habituel.',
    'Papeterie et process':'Piste papeterie : voir si cette approche peut aider sur une machine à papier (casses, qualité de feuille, humidité, consommation de vapeur et d’énergie). Commencer par l’historique d’une seule ligne et valider avec l’équipe process.',
    'Industrie et maintenance':'Piste atelier : tester sur un équipement critique (historique de pannes, rapports d’intervention, consignes) et mesurer le temps de diagnostic gagné ou les arrêts évités.',
    'Copilot et bureautique':'Piste au quotidien : essayer sur une tâche récurrente (compte rendu de réunion, rapport hebdomadaire, synthèse d’e-mails, mise en forme Excel) et mesurer le temps gagné sur deux semaines.',
    'Données et décisionnel':'Piste données : appliquer à un tableau de bord existant (production, qualité, énergie, rebuts) et comparer les résultats avec la source avant de les diffuser.',
    'Automatisation et agents':'Piste automatisation : choisir un flux simple et répétitif (demande d’achat, relevé de compteurs, alerte qualité) et garder une validation humaine avant toute action.',
    'IA et innovation':'À suivre : nouveauté IA générale. Noter l’outil et attendre un cas d’usage concret pour l’usine avant de tester.',
}

# « Incontournable » : lancement d'un agent, d'un modèle ou d'une fonction chez un acteur majeur.
MAJOR=_pattern(['ChatGPT','OpenAI','GPT-*','Sora','Codex','Claude','Anthropic','Gemini','NotebookLM','Veo','Google AI','Copilot','Mistral','Le Chat','Grok','xAI','Perplexity','Llama','Meta AI','DeepSeek','Qwen','Midjourney','Runway','Kling','ElevenLabs','Firefly','Luma'])
LAUNCH=_pattern(['introducing','introduces','launch*','unveil*','announc*','now available','available now','rolls out','rolling out','releas*','debut*','ships','arrives','is here','gets','adds','brings','new','lance*','dévoile*','présente','annonce*','déploie','arrive*','débarque*','nouveau*','nouvelle*','disponible'])
WHAT=_pattern(['agent*','model*','feature*','mode','app','apps','tool*','assistant*','browser','API','voice','video*','image*','research','memory','canvas','tasks','skills','connector*','integration*','plugin*','modèle*','fonctionnalit*','outil*','application*','navigateur','vidéo*','version'])
MAJOR_SOURCES={'OpenAI','Anthropic / Claude','Google IA et Gemini','Google Gemini','Google DeepMind','Google Labs','Microsoft 365','Microsoft Copilot Studio','Mistral AI','Meta IA','xAI / Grok','Perplexity','DeepSeek','Alibaba / Qwen','Runway','Midjourney','ElevenLabs','Luma AI'}

# Annonces d'entreprise ou de conformité : utiles, mais pas des nouveautés à essayer.
NOT_MUST=_pattern(['certification*','certified','FedRAMP','GovCloud','compliance','SOC 2','ISO 27001','program','programme','partner network','partnership','partenariat','capital','funding','raises','levée de fonds','valuation','valorisation','insurance','assurance','acquire*','acquisition','rachète','lawsuit','procès'])
def must_read(title,text,source=''):
    if LOW_VALUE.search(title or '') or OFF_TOPIC.search(title or '') or NOT_MUST.search(title or ''): return False
    launch=bool(LAUNCH.search(title or ''))
    if source in MAJOR_SOURCES and launch and (WHAT.search(title or '') or NEW_FEATURE.search(title or '')): return True
    return bool(MAJOR.search(title or '')) and launch and bool(WHAT.search(title or '') or WHAT.search((text or '')[:400]))

def is_noise(title,url=''):
    """Pages d'auteur, de recrutement ou de catégorie : aucune information utile."""
    return bool(NOISE_TITLE.search(title or '') or NOISE_URL.search(url or ''))

def clean_title(title,source=''):
    """Retirer le suffixe « - Éditeur » ajouté par Google Actualités ou les blogs."""
    title=(title or '').strip()
    words={w for w in re.findall(r'\w+',(source or '').lower()) if len(w)>=3}
    for _ in range(2):
        match=re.match(r'^(.{15,}?)\s+[-–|]\s+([^-–|]{2,70})$',title)
        if not match: break
        suffix=match.group(2).lower()
        if words & set(re.findall(r'\w+',suffix)) or re.search(r'\b(blog|news|newsroom|\w+\.(com|ai|io|fr|org|net))\b',suffix):
            title=match.group(1).strip()
        else: break
    return title

def tools_in(text):
    found=[]
    for tool,pattern in TOOL_PATTERNS:
        if pattern.search(text) and not any(tool.lower() in f.lower() for f in found):
            found=[f for f in found if f.lower() not in tool.lower()]+[tool]
    return found[:5]

def assess(title,text,interests,source=''):
    """Retourne catégorie, score 0-100, outils cités, nouveauté, incontournable et justification."""
    full=(title or '')+' \n '+(text or '')
    lower=full.lower()
    hits=[]
    for name,weight,pattern in THEME_PATTERNS:
        count=len(pattern.findall(full))
        in_title=bool(pattern.search(title or ''))
        if count: hits.append((weight*(1+min(count,4)/4)+(weight/2 if in_title else 0),name,weight,count))
    hits.sort(key=lambda h:-h[0])
    category=hits[0][1] if hits else 'IA et innovation'
    terms=[x.strip() for x in (interests or '').split(',') if x.strip()]
    matches=[x for x in terms if x.lower() in lower]
    tools=tools_in(full)
    new_feature=bool(NEW_FEATURE.search(title or '')) or len(NEW_FEATURE.findall(full))>=2
    essential=must_read(title,text,source)
    creative=any(h[1].startswith('Création') for h in hits)
    score=22+sum(h[2] for h in hits[:2])+min(24,8*len(matches))+min(12,4*len(tools))+(12 if new_feature else 0)+(28 if essential else 0)
    if LOW_VALUE.search(title or ''): score-=25
    if OFF_TOPIC.search(full): score-=30
    score=max(5,min(98,round(score)))
    themes=', '.join(h[1] for h in hits[:2]) or 'aucun thème métier'
    reason='Correspondances : '+(', '.join(matches) or 'aucune')+' · Thèmes : '+themes+(' · Lancement d’un acteur majeur' if essential else '')+(' · Nouvelle fonctionnalité annoncée' if new_feature else '')+'. Score indicatif calculé par mots-clés, sans IA.'
    opportunity=OPPORTUNITIES[category]+((' Outils concernés : '+', '.join(tools)+'.') if tools else '')
    return dict(category=category,score=score,services=matches,tools=tools,new_feature=new_feature or essential,must_read=essential,creative=creative,opportunity=opportunity,reason=reason,mode='Mots-clés')
