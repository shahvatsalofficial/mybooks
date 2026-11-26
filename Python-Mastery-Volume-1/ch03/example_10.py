from collections import ChainMap

# Zero allocations! Holds pointers to the underlying dicts:
config_view = ChainMap(cli_flags, env_config, default_config)

# Resolves 'timeout_ms' by searching cli_flags, then env_config, then default_config:
timeout = config_view["timeout_ms"]
