"""Fail-closed LAN access checks, including reverse proxy address chains."""

from ipaddress import ip_address, ip_network


LOCAL_NETWORKS = tuple(ip_network(value) for value in (
    "127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
    "::1/128", "fc00::/7",
))


def is_local_request(remote_addr, headers) -> bool:
    # Never replace the socket peer with a client-controlled header. Every hop
    # must be local, so adding a forged private address cannot bypass this gate.
    addresses = [remote_addr]
    for name in ("X-Forwarded-For", "X-Real-IP"):
        if name in headers:
            addresses.extend(headers[name].split(","))
    # The bundled Traefik uses X-Forwarded-For. Reject unsupported forwarding
    # formats instead of silently ignoring a possible public client address.
    if "Forwarded" in headers:
        return False
    for value in addresses:
        try:
            address = ip_address(str(value or "").strip())
        except ValueError:
            return False
        if address.version == 6 and address.ipv4_mapped:
            address = address.ipv4_mapped
        if not any(address in network for network in LOCAL_NETWORKS):
            return False
    return True
