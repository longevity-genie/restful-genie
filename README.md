# biotables

Experimental repository that helps with paper reviews



# Setting up python backend and library
```commandline
micromamba create -f environment.yaml
micromamba activate biotables
```

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