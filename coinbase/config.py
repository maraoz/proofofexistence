__author__ = 'gsibble'

COINBASE_ENDPOINT = 'https://coinbase.com/api/v1'

COINBASE_AUTH_URI = 'https://www.coinbase.com/oauth/authorize'
COINBASE_TOKEN_URI = 'https://www.coinbase.com/oauth/token'


TEMP_CREDENTIALS = '''
{"_module": "oauth2client.client", "token_expiry": "2013-03-24T02:37:50Z", "access_token": "2a02d1fc82b1c42d4ea94d6866b5a232b53a3a50ad4ee899ead9afa6144c2ca3", "token_uri": "https://www.coinbase.com/oauth/token", "invalid": false, "token_response": {"access_token": "2a02d1fc82b1c42d4ea94d6866b5a232b53a3a50ad4ee899ead9afa6144c2ca3", "token_type": "bearer", "expires_in": 7200, "refresh_token": "ffec0153da773468c8cb418d07ced54c13ca8deceae813c9be0b90d25e7c3d71", "scope": "all"}, "client_id": "2df06cb383f4ffffac20e257244708c78a1150d128f37d420f11fdc069a914fc", "id_token": null, "client_secret": "7caedd79052d7e29aa0f2700980247e499ce85381e70e4a44de0c08f25bded8a", "revoke_uri": "https://accounts.google.com/o/oauth2/revoke", "_class": "OAuth2Credentials", "refresh_token": "ffec0153da773468c8cb418d07ced54c13ca8deceae813c9be0b90d25e7c3d71", "user_agent": null}'''