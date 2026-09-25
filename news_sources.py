"""Sources officielles et relais de leurs publications publiques, sans API payante."""
from urllib.parse import urlencode

def relay(domain):
    return 'https://news.google.com/rss/search?'+urlencode({'q':'site:'+domain,'hl':'en-US','gl':'US','ceid':'US:en'})

# (Nom, page officielle, flux direct facultatif). Le relais reste limité au domaine indiqué.
CATALOG=[
    ('OpenAI','https://openai.com/news/','https://openai.com/news/rss.xml','openai.com'),
    ('Microsoft 365','https://www.microsoft.com/en-us/microsoft-365/blog/','https://www.microsoft.com/en-us/microsoft-365/blog/feed/','microsoft.com'),
    ('Power BI','https://powerbi.microsoft.com/en-us/blog/','https://powerbi.microsoft.com/en-us/blog/feed/','powerbi.microsoft.com'),
    ('Microsoft Fabric','https://blog.fabric.microsoft.com/','https://blog.fabric.microsoft.com/en-us/blog/feed/','blog.fabric.microsoft.com'),
    ('Microsoft IA','https://blogs.microsoft.com/','https://blogs.microsoft.com/feed/','blogs.microsoft.com'),
    ('Google IA et Gemini','https://blog.google/innovation-and-ai/technology/ai/','https://blog.google/innovation-and-ai/technology/ai/rss/','blog.google'),
    ('Google DeepMind','https://deepmind.google/blog/','','deepmind.google'),
    ('Anthropic / Claude','https://www.anthropic.com/news','','anthropic.com'),
    ('Meta IA','https://ai.meta.com/blog/','','ai.meta.com'),
    ('Amazon AWS IA','https://aws.amazon.com/blogs/machine-learning/','https://aws.amazon.com/blogs/machine-learning/feed/','aws.amazon.com/blogs/machine-learning'),
    ('NVIDIA','https://blogs.nvidia.com/','https://blogs.nvidia.com/feed/','blogs.nvidia.com'),
    ('Mistral AI','https://mistral.ai/news/','','mistral.ai/news'),
    ('DeepSeek','https://deepseek.com/en/news/','','deepseek.com'),
    ('Alibaba / Qwen','https://qwen.ai/','','qwen.ai'),
    ('Hugging Face','https://huggingface.co/blog','https://huggingface.co/blog/feed.xml','huggingface.co/blog'),
    ('IBM Research','https://research.ibm.com/blog','','research.ibm.com/blog'),
    ('Cohere','https://cohere.com/blog','','cohere.com/blog'),
    ('xAI / Grok','https://x.ai/news','','x.ai/news'),
    ('Perplexity','https://www.perplexity.ai/hub/blog','','perplexity.ai/hub/blog'),
    ('Adobe / Firefly','https://blog.adobe.com/','','blog.adobe.com'),
    ('Stability AI','https://stability.ai/news','','stability.ai/news'),
    ('Runway','https://runwayml.com/news','','runwayml.com'),
    ('ElevenLabs','https://elevenlabs.io/blog/','','elevenlabs.io/blog'),
    ('Midjourney','https://updates.midjourney.com/','','updates.midjourney.com'),
    ('Apple Machine Learning','https://machinelearning.apple.com/','','machinelearning.apple.com'),
    ('Salesforce IA','https://www.salesforce.com/blog/category/artificial-intelligence/','','salesforce.com/blog')
]
BY_NAME={name:{'official':official,'feed':feed or relay(domain),'relay':not bool(feed),'fallback':relay(domain)} for name,official,feed,domain in CATALOG}
SOURCES=[(name,config['feed']) for name,config in BY_NAME.items()]
