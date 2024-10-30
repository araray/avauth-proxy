# avauth_proxy/__init__.py

from flask import Flask
from authlib.integrations.flask_client import OAuth
from .config import Config
from .utils import load_oauth_providers

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

oauth = OAuth(app)
oauth_providers = load_oauth_providers(oauth)

from . import routes
