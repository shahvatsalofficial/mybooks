# ANTI-PATTERN: Creating SSLContext per request burns 35ms of CPU time!
ssl_context = ssl.create_default_context()
