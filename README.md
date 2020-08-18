# NGM API lambda backend


## install serverless framework
```bash
npm install --save-dev serverless-wsgi serverless-python-requirements
```

## deploy
```bash
sls deploy
```

## add python dependencies
```bash
pip freeze > requirements.txt
```

## local development
```bash
virtualenv .venv --python=python3
source ~/.venv/bin/activate
pip install -r requirements.txt
FLASK_ENV=development flask run
```
