# Restrict access to IMDS link-local IP strictly to root and Azure DaemonSet UID
iptables -A OUTPUT -d 169.254.169.254/32 -m owner ! --uid-owner 0 -j DROP
