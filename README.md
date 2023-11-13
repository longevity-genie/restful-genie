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
cd scripts
clasp clone "1iIXMPhK9hx5J7RbKQ-AwacjDwtZMN3BgaTXvV99U10HJCthDLVYvSbUQ"
```

To push changes use:
```bash
cd scripts
clasp push
```