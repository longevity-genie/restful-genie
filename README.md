# biotables

Experimental repository that helps with paper reviews

# Python part

## Setting up python backend and library
```commandline
micromamba create -f environment.yaml
micromamba activate biotables
```

# Google script part

The google script part is managed by clasp at scripts folder.
It provides the following functions to the spreadsheets:
```
GPT(textValue, model_name='gpt-3.5-turbo', temperature=0.0, resplit = true,  host='http://agingkills.eu:8000'. api = "/papers", limit=1)
SEMANTIC_SEARCH(textValue, collection_name='bge_base_en_v1.5_aging_5', host='http://agingkills.eu:8000'. api = "/papers", limit=1, with_vectors=false, with_payload=true, resplit = true)
GPT_3_5(textValue, temperature=0.0)
GPT_4(textValue, temperature=0.0)
```

## Setting up google script part
```bash
pip install -e .
```

Install nodejs to deal with google script

```bash
wget -qO- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
nvm install node
npm install -g @google/clasp
clasp login
clasp pull
```

To push changes use:
```bash
clasp push --force
```

By default, the project is published from genielongevity@gmail.com
Latest deployment id is AKfycbyLOpK2I7cWD67yKov_JffufrGPXkCYgaKPgkF6_RFZEVVysc3ZX6AOetePFDqkxtZ8