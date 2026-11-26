# Worker verifies lease before executing stateful operation
ETCDCTL_API=3 etcdctl lock --ttl=30 /swarm/leader/db_migration \
  node dist/worker_migration.js --schema=v2.4
