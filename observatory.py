"""Observatoire des principales IA, calculé automatiquement à partir des articles collectés.

Aucune donnée n'est saisie à la main : activité, dernières annonces et modèles cités
sont recalculés à chaque affichage, donc mis à jour à chaque collecte.
"""
import re
from datetime import datetime, timedelta, timezone

def _rx(pattern): return re.compile(pattern,re.IGNORECASE)

ASSISTANTS=[
    dict(id='chatgpt',name='ChatGPT',company='OpenAI',color='#10a37f',site='https://chatgpt.com',news='https://openai.com/news/',
         match=_rx(r'\b(openai|chatgpt|gpt-\d|sora|codex)\b'),
         models=_rx(r'\b(GPT-\d+(?:\.\d+)?(?:[- ](?:mini|nano|pro|turbo|codex))?|o\d(?:-(?:mini|pro))?|Sora(?: \d+)?|Codex|ChatGPT (?:Agent|Atlas|Pulse))\b')),
    dict(id='claude',name='Claude',company='Anthropic',color='#d97757',site='https://claude.ai',news='https://www.anthropic.com/news',
         match=_rx(r'\b(anthropic|claude)\b'),
         models=_rx(r'\b(Claude (?:Opus|Sonnet|Haiku)(?: \d+(?:\.\d+)?)?|Claude \d+(?:\.\d+)? (?:Opus|Sonnet|Haiku)|Claude Code|Claude Duet)\b')),
    dict(id='gemini',name='Gemini',company='Google',color='#4285f4',site='https://gemini.google.com',news='https://blog.google/products/gemini/',
         match=_rx(r'\b(gemini|deepmind|notebooklm|veo|imagen|nano banana)\b'),
         models=_rx(r'\b(Gemini \d+(?:\.\d+)?(?: (?:Pro|Flash(?:-Lite)?|Ultra|Nano|Deep Think|Carbon))?|Veo \d+(?:\.\d+)?|Imagen \d+|Nano Banana(?: Pro)?|NotebookLM)\b')),
    dict(id='copilot',name='Copilot',company='Microsoft',color='#0078d4',site='https://copilot.microsoft.com',news='https://www.microsoft.com/en-us/microsoft-365/blog/',
         match=_rx(r'\bcopilot\b'),
         models=_rx(r'\b(Microsoft 365 Copilot|Copilot Studio|GitHub Copilot|Copilot Chat|Copilot Notebooks|Copilot Vision|Copilot Pages|Copilot Cowork|Copilot Researcher|Copilot Analyst)\b')),
    dict(id='mistral',name='Le Chat',company='Mistral AI',color='#fa520f',site='https://chat.mistral.ai',news='https://mistral.ai/news/',
         match=_rx(r'\b(mistral|le chat)\b'),
         models=_rx(r'\b(Mistral (?:Large|Medium|Small)(?: \d+(?:\.\d+)?)?|Magistral(?: (?:Medium|Small))?|Codestral|Devstral|Pixtral|Voxtral)\b')),
    dict(id='grok',name='Grok',company='xAI',color='#6b7280',site='https://grok.com',news='https://x.ai/news',
         match=_rx(r'\b(xai|grok)\b'),
         models=_rx(r'\b(Grok \d+(?:\.\d+)?(?: (?:Heavy|mini|Fast))?|Grok Imagine)\b')),
    dict(id='meta',name='Meta AI',company='Meta',color='#0866ff',site='https://www.meta.ai',news='https://ai.meta.com/blog/',
         match=_rx(r'\b(meta ai|llama)\b'),
         models=_rx(r'\b(Llama \d+(?:\.\d+)?(?: (?:Scout|Maverick|Behemoth))?)\b')),
    dict(id='deepseek',name='DeepSeek',company='DeepSeek',color='#4d6bfe',site='https://chat.deepseek.com',news='https://deepseek.com/en/news/',
         match=_rx(r'\bdeepseek\b'),
         models=_rx(r'\b(DeepSeek[- ](?:V|R)\d+(?:\.\d+)?(?:-\w+)?)\b')),
    dict(id='qwen',name='Qwen',company='Alibaba',color='#615ced',site='https://chat.qwen.ai',news='https://qwen.ai/',
         match=_rx(r'\bqwen'),
         models=_rx(r'\b(Qwen ?\d+(?:\.\d+)?(?:-(?:Max|Plus|Coder|VL|Omni))?)\b')),
    dict(id='perplexity',name='Perplexity',company='Perplexity',color='#20808d',site='https://www.perplexity.ai',news='https://www.perplexity.ai/hub/blog',
         match=_rx(r'\bperplexity\b'),
         models=_rx(r'\b(Comet|Sonar(?: Pro| Reasoning)?|Perplexity (?:Pro|Max|Labs))\b')),
]

def mentions(text):
    return [a['id'] for a in ASSISTANTS if a['match'].search(text or '')]

def _date(value):
    try:
        d=datetime.fromisoformat(value)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except Exception: return None

def build(articles,now=None):
    now=now or datetime.now(timezone.utc)
    month=now-timedelta(days=30)
    result=[]
    for config in ASSISTANTS:
        related=[a for a in articles if config['id'] in a.get('assistants',[])]
        recent=[a for a in related if (_date(a.get('published') or '') or now-timedelta(days=999))>=month]
        models={}
        for a in related:  # du plus récent au plus ancien
            text=(a.get('original_title') or '')+' '+(a.get('details') or '')
            for found in config['models'].findall(text):
                name=found if isinstance(found,str) else found[0]
                key=name.lower().strip()
                if key not in models: models[key]={'name':name.strip(),'last':a.get('published'),'count':0}
                models[key]['count']+=1
        ranked=sorted(models.values(),key=lambda m:((m['last'] or ''),m['count']),reverse=True)[:5]
        latest=sorted(related[:12],key=lambda a:(not a.get('must_read'),))[:4]
        count=len(recent)
        status='Très actif' if count>=6 else 'Actif' if count>=2 else 'Calme'
        result.append(dict(id=config['id'],name=config['name'],company=config['company'],color=config['color'],site=config['site'],news=config['news'],
                           count30=count,total=len(related),status=status,last=related[0].get('published') if related else None,
                           must_read=sum(1 for a in recent if a.get('must_read')),
                           models=[{'name':m['name'],'last':m['last']} for m in ranked],
                           latest=[{'id':a['id'],'title':a['title'],'url':a['url'],'published':a.get('published'),'source':a.get('source'),'must_read':bool(a.get('must_read'))} for a in latest]))
    result.sort(key=lambda r:(-r['count30'],-r['total']))
    return result
