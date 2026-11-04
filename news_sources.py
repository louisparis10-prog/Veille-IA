"""Sources suivies : éditeurs d'outils IA, industrie et papeterie, sans API payante."""
from urllib.parse import urlencode

def relay(query,lang='en'):
    region={'en':('en-US','US','US:en'),'fr':('fr','FR','FR:fr')}[lang]
    return 'https://news.google.com/rss/search?'+urlencode({'q':query,'hl':region[0],'gl':region[1],'ceid':region[2]})

# (Nom, page officielle, flux direct facultatif, domaine autorisé, requête de relais facultative, langue, famille)
# Sans flux direct, Google Actualités relaie les publications. Le domaine « * » accepte la presse de tout site.
CATALOG=[
    # Outils IA du quotidien
    ('OpenAI','https://openai.com/news/','https://openai.com/news/rss.xml','openai.com','','en','Outils IA'),
    ('Microsoft 365','https://www.microsoft.com/en-us/microsoft-365/blog/','https://www.microsoft.com/en-us/microsoft-365/blog/feed/','microsoft.com','','en','Outils IA'),
    ('Microsoft Copilot Studio','https://www.microsoft.com/en-us/microsoft-copilot/blog/copilot-studio/','https://www.microsoft.com/en-us/microsoft-copilot/blog/copilot-studio/feed/','microsoft.com','','en','Outils IA'),
    ('Microsoft Power Platform','https://www.microsoft.com/en-us/power-platform/blog/','https://www.microsoft.com/en-us/power-platform/blog/feed/','microsoft.com','','en','Outils IA'),
    ('Power BI','https://powerbi.microsoft.com/en-us/blog/','https://powerbi.microsoft.com/en-us/blog/feed/','powerbi.microsoft.com','','en','Outils IA'),
    ('Microsoft Fabric','https://blog.fabric.microsoft.com/','https://blog.fabric.microsoft.com/en-us/blog/feed/','blog.fabric.microsoft.com','','en','Outils IA'),
    ('Microsoft IA','https://blogs.microsoft.com/','https://blogs.microsoft.com/feed/','blogs.microsoft.com','','en','Outils IA'),
    ('Google IA et Gemini','https://blog.google/innovation-and-ai/technology/ai/','https://blog.google/innovation-and-ai/technology/ai/rss/','blog.google','','en','Outils IA'),
    ('Google Gemini','https://blog.google/products/gemini/','https://blog.google/products/gemini/rss/','blog.google','','en','Outils IA'),
    ('Google DeepMind','https://deepmind.google/blog/','','deepmind.google','','en','Outils IA'),
    ('Anthropic / Claude','https://www.anthropic.com/news','','anthropic.com','','en','Outils IA'),
    ('Mistral AI','https://mistral.ai/news/','','mistral.ai/news','','en','Outils IA'),
    ('Meta IA','https://ai.meta.com/blog/','','ai.meta.com','','en','Outils IA'),
    ('Amazon AWS IA','https://aws.amazon.com/blogs/machine-learning/','https://aws.amazon.com/blogs/machine-learning/feed/','aws.amazon.com/blogs/machine-learning','','en','Outils IA'),
    ('NVIDIA','https://blogs.nvidia.com/','https://blogs.nvidia.com/feed/','blogs.nvidia.com','','en','Outils IA'),
    ('DeepSeek','https://deepseek.com/en/news/','','deepseek.com','','en','Outils IA'),
    ('Alibaba / Qwen','https://qwen.ai/','','qwen.ai','','en','Outils IA'),
    ('Hugging Face','https://huggingface.co/blog','https://huggingface.co/blog/feed.xml','huggingface.co/blog','','en','Outils IA'),
    ('IBM Research','https://research.ibm.com/blog','','research.ibm.com/blog','','en','Outils IA'),
    ('Cohere','https://cohere.com/blog','','cohere.com/blog','','en','Outils IA'),
    ('xAI / Grok','https://x.ai/news','','x.ai/news','','en','Outils IA'),
    ('Perplexity','https://www.perplexity.ai/hub/blog','','perplexity.ai/hub/blog','','en','Outils IA'),
    ('Salesforce IA','https://www.salesforce.com/blog/category/artificial-intelligence/','','salesforce.com/blog','','en','Outils IA'),
    # Actualité IA : ne manquer aucun lancement d'agent, de modèle ou de fonctionnalité
    ('The Verge · IA','https://www.theverge.com/ai-artificial-intelligence','https://www.theverge.com/rss/ai-artificial-intelligence/index.xml','theverge.com','','en','Actualité IA'),
    ('TechCrunch · IA','https://techcrunch.com/category/artificial-intelligence/','https://techcrunch.com/category/artificial-intelligence/feed/','techcrunch.com','','en','Actualité IA'),
    ('Agents et assistants · presse','https://news.google.com/','','*','(ChatGPT OR Claude OR Gemini OR Copilot OR Grok OR "Le Chat" OR Perplexity) (agent OR agents OR "new feature" OR launches OR "rolls out" OR "now available" OR "new model") when:7d','en','Actualité IA'),
    ('IA grand public · presse FR','https://news.google.com/','','*','(ChatGPT OR Claude OR Gemini OR Copilot OR Mistral OR "Le Chat") (nouveau OR nouvelle OR lance OR déploie OR disponible OR agent) when:7d','fr','Actualité IA'),
    # Création : vidéo, image, voix et musique
    ('Google Labs','https://blog.google/technology/google-labs/','https://blog.google/technology/google-labs/rss/','blog.google','','en','Création'),
    ('Adobe / Firefly','https://blog.adobe.com/','','blog.adobe.com','site:blog.adobe.com (Firefly OR "generative AI" OR "AI video" OR "AI image")','en','Création'),
    ('Runway','https://runwayml.com/news','','runwayml.com','site:runwayml.com (news OR introducing OR launch OR Gen)','en','Création'),
    ('Midjourney','https://updates.midjourney.com/','','updates.midjourney.com','','en','Création'),
    ('Luma AI','https://lumalabs.ai/news','','lumalabs.ai','site:lumalabs.ai (Ray OR "Dream Machine" OR launch OR introducing OR news)','en','Création'),
    ('ElevenLabs','https://elevenlabs.io/blog/','','elevenlabs.io/blog','','en','Création'),
    ('Stability AI','https://stability.ai/news','','stability.ai/news','','en','Création'),
    ('Kling AI · presse','https://klingai.com/','','*','"Kling AI" (launch OR launches OR model OR new OR released) when:30d','en','Création'),
    ('Création IA · presse','https://news.google.com/','','*','("AI video generator" OR "video generation model" OR "image generation model" OR "AI image generator" OR "AI music generator" OR "text-to-video" OR "AI video model") (launch OR launches OR released OR introduces OR unveils) when:14d','en','Création'),
    # Industrie et automatisation
    ('Siemens IA industrielle','https://www.siemens.com/global/en/company/topic-areas/artificial-intelligence.html','','siemens.com','site:siemens.com ("Industrial Copilot" OR "industrial AI" OR "artificial intelligence") -career -jobs','en','Industrie'),
    ('ABB process et papier','https://new.abb.com/pulp-paper','','new.abb.com','site:new.abb.com (AI OR "artificial intelligence" OR digital OR automation) (pulp OR paper OR "process industries")','en','Industrie'),
    ('L’Usine Digitale','https://www.usine-digitale.fr/','https://www.usine-digitale.fr/rss','usine-digitale.fr','','fr','Industrie'),
    # Papeterie
    ('Valmet','https://www.valmet.com/media/news/','','valmet.com','site:valmet.com (automation OR digital OR AI OR "machine learning" OR paper) -career','en','Papeterie'),
    ('ANDRITZ','https://www.andritz.com/newsroom-en','','andritz.com','site:andritz.com (digital OR automation OR AI OR "Metris") (pulp OR paper OR tissue) -career','en','Papeterie'),
    ('Voith Paper','https://voith.com/corp-en/industry-solutions/papermaking.html','','voith.com','site:voith.com (paper OR papermaking OR tissue) (digital OR automation OR AI OR autonomous) -career','en','Papeterie'),
    ('Papnews','https://www.papnews.com/','https://www.papnews.com/feed/','papnews.com','','en','Papeterie'),
    ('Pulp & Paper Canada','https://www.pulpandpapercanada.com/','https://www.pulpandpapercanada.com/feed/','pulpandpapercanada.com','','en','Papeterie'),
    ('IA et papeterie · presse','https://news.google.com/','','*','("paper mill" OR papermaking OR "pulp and paper" OR "paper machine" OR "tissue mill") (AI OR "artificial intelligence" OR "machine learning" OR "digital twin" OR "predictive maintenance") -"data center" -"data centre" when:180d','en','Papeterie'),
    ('IA et papeterie · presse FR','https://news.google.com/','','*','(papeterie OR "industrie papetière" OR "pâte à papier" OR "machine à papier") ("intelligence artificielle" OR IA OR digitalisation OR "industrie 4.0" OR "maintenance prédictive") -"data center" -"centre de données" -supercalculateur when:180d','fr','Papeterie'),
]
BY_NAME={}
for name,official,feed,domain,query,lang,family in CATALOG:
    fallback=relay(query or 'site:'+domain,lang)
    BY_NAME[name]={'official':official,'feed':feed or fallback,'relay':not bool(feed),'fallback':fallback,
                   'domain':domain.split('/')[0],'family':family,'press':domain=='*' or family not in ('Outils IA','Création')}
FAMILIES=['Outils IA','Actualité IA','Création','Industrie','Papeterie']
SOURCES=[(name,config['feed']) for name,config in BY_NAME.items()]
