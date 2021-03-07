# Issuer URL. For production, this is https://shibboleth.illinois.edu.
from decouple import config

ISSUER_URL = config("ISSUER_URL")
SCOPES = config("SCOPES")  # Other OIDC scopes can be added as needed.

# SESSION
SESSION_SECRET = config("SESSION_SECRET")

# SHIBBOLETH
CLIENT_ID = config("CLIENT_ID")
CLIENT_SECRET = config("CLIENT_SECRET")
REDIRECT_URIS = [config("REDIRECT_URIS")]
