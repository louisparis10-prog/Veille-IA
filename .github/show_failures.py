"""Publie les tests en échec comme annotations GitHub, visibles sans ouvrir les journaux."""
import re
import sys

text=open(sys.argv[1],encoding='utf-8',errors='replace').read()
blocks=[b.strip() for b in re.split(r'^={20,}$',text,flags=re.M) if re.match(r'\s*(ERROR|FAIL):',b)]
for block in blocks[:10]:
    title=block.splitlines()[0][:200]
    body=block.split('-'*20,1)[-1].strip()[-3000:]
    print('::error title='+title.replace(':','%3A').replace(',','%2C')+'::'+body.replace('%','%25').replace('\r','').replace('\n','%0A'))
if not blocks: print('::error title=Tests::'+text[-3000:].replace('%','%25').replace('\n','%0A'))
