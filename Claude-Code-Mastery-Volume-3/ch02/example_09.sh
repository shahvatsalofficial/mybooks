# Create pristine read-only base mount
mkdir -p /mnt/repo-base /mnt/scratch /mnt/merged
mount --bind -o ro /opt/enterprise-repo /mnt/repo-base

# Mount RAM-backed writable layer
mount -t tmpfs -o size=4G,noexec,nosuid,nodev tmpfs /mnt/scratch

# Combine via OverlayFS
mount -t overlay overlay -o lowerdir=/mnt/repo-base,upperdir=/mnt/scratch/upper,workdir=/mnt/scratch/work /mnt/merged
