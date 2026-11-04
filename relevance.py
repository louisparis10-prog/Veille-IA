"""Pertinence métier sans IA payante : outils cités, nouveautés et lien avec l'industrie papetière.

Les textes analysés combinent l'original (souvent en anglais) et sa traduction française,
afin que les centres d'intérêt saisis en français trouvent aussi leurs correspondances.
"""
import re

def _pattern(terms):
    parts=[]
    for term in terms:
        escaped=re.escape(term.lower()).replace(r'\ ',r'\s+')
        # Les termes se terminant par « * » sont des racines (manufactur* → manufacturing, manufacturer…).
        parts.append(r'\b'+escaped[:-2]+r'\w*' if term.endswith('*') else r'\b'+escaped+r'\b')
    return re.compile('|'.join(parts),re.IGNORECASE)

# (catégorie, poids, mots-clés). L'ordre sert d'arbitrage en cas d'égalité.
THEMES=[
    ('Papeterie et process',32,['paper mill*','papermaking','paper machine*','pulp','pulp and paper','tissue paper','paperboard','containerboard','corrugated','cellulose','wood fib*','papier*','papeterie*','papetier*','pâte à papier','machine à papier','carton*','cellulose','fibres de bois','bobine*','sécherie','Valmet','ANDRITZ','Voith','Metsä','Stora Enso','UPM','Smurfit','Sappi','Mondi']),
    ('Industrie et maintenance',24,['manufactur*','industrial','industry 4.0','factory','factories','shop floor','plant floor','production line*','predictive maintenance','maintenance','downtime','OEE','quality control','quality inspection','defect detection','digital twin*','IIoT','industrial IoT','sensor*','SCADA','manufacturing execution system*','PLC','process control','supply chain','energy efficiency','operators','industrie*','usine*','maintenance prédictive','contrôle qualité','jumeau* numérique*','capteur*','atelier*','ligne* de production','rebut*','opérateur*','Siemens','ABB','Rockwell','AVEVA','Schneider Electric','Honeywell']),
    ('Copilot et bureautique',20,['Copilot','Microsoft 365','Microsoft Teams','Outlook','Excel','PowerPoint','SharePoint','OneDrive','Microsoft Word','Copilot Chat','Copilot Notebooks','bureautique']),
    ('Données et décisionnel',16,['Power BI','Microsoft Fabric','Fabric','dashboard*','analytics','data warehouse','lakehouse','semantic model*','tableau* de bord','décisionnel','données de production']),
    ('Automatisation et agents',16,['Power Automate','Copilot Studio','Power Apps','Power Platform','agent*','agentic','workflow*','automation','automate*','RPA','n8n','automatisation','agentique']),
]
THEME_PATTERNS=[(name,weight,_pattern(words)) for name,weight,words in THEMES]

# Outils et produits IA reconnus, affichés comme étiquettes « Outils cités ».
TOOLS=['ChatGPT','ChatGPT Enterprise','GPT-5','GPT-4o','Codex','Sora','OpenAI o3','Microsoft 365 Copilot','Copilot Studio','Copilot Chat','GitHub Copilot','Copilot','Power BI','Microsoft Fabric','Power Automate','Power Apps','Azure AI Foundry','Azure OpenAI','Dataverse','Claude','Claude Code','Gemini','NotebookLM','Google AI Studio','Vertex AI','Le Chat','Mistral','Llama','DeepSeek','Qwen','Grok','Perplexity','Agentforce','Amazon Bedrock','Amazon Q','SageMaker','Omniverse','Hugging Face','Firefly','watsonx','Industrial Copilot','Cohere','n8n','Valmet DNA','AVEVA']
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
    'Papeterie et process':'Piste papeterie : voir si cette approche peut aider sur une machine à papier (casses, qualité de feuille, humidité, consommation de vapeur et d’énergie). Commencer par l’historique d’une seule ligne et valider avec l’équipe process.',
    'Industrie et maintenance':'Piste atelier : tester sur un équipement critique (historique de pannes, rapports d’intervention, consignes) et mesurer le temps de diagnostic gagné ou les arrêts évités.',
    'Copilot et bureautique':'Piste au quotidien : essayer sur une tâche récurrente (compte rendu de réunion, rapport hebdomadaire, synthèse d’e-mails, mise en forme Excel) et mesurer le temps gagné sur deux semaines.',
    'Données et décisionnel':'Piste données : appliquer à un tableau de bord existant (production, qualité, énergie, rebuts) et comparer les résultats avec la source avant de les diffuser.',
    'Automatisation et agents':'Piste automatisation : choisir un flux simple et répétitif (demande d’achat, relevé de compteurs, alerte qualité) et garder une validation humaine avant toute action.',
    'IA et innovation':'À suivre : nouveauté IA générale. Noter l’outil et attendre un cas d’usage concret pour l’usine avant de tester.',
}

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

def assess(title,text,interests):
    """Retourne catégorie, score 0-100, outils cités, nouveauté et justification."""
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
    score=22+sum(h[2] for h in hits[:2])+min(24,8*len(matches))+min(12,4*len(tools))+(12 if new_feature else 0)
    if LOW_VALUE.search(title or ''): score-=25
    if OFF_TOPIC.search(full): score-=30
    score=max(5,min(98,round(score)))
    themes=', '.join(h[1] for h in hits[:2]) or 'aucun thème métier'
    reason='Correspondances : '+(', '.join(matches) or 'aucune')+' · Thèmes : '+themes+(' · Nouvelle fonctionnalité annoncée' if new_feature else '')+'. Score indicatif calculé par mots-clés, sans IA.'
    opportunity=OPPORTUNITIES[category]+((' Outils concernés : '+', '.join(tools)+'.') if tools else '')
    return dict(category=category,score=score,services=matches,tools=tools,new_feature=new_feature,opportunity=opportunity,reason=reason,mode='Mots-clés')
