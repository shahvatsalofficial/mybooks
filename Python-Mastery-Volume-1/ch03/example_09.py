# ANTI-PATTERN: Eagerly copying dictionaries
effective_config = {**default_config, **env_config, **cli_flags}
