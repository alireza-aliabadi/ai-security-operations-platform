# Lateral Movement Playbook

## Purpose

Contain and eradicate RDP/SMB lateral movement after initial compromise.

## Steps

1. Identify source and destination hosts from authentication and network logs.
2. Disable the compromised account and review privileged group membership.
3. Isolate affected hosts from the network.
4. Review domain controller auth logs for additional targets.
5. Rotate privileged credentials and hunt for persistence (services, scheduled tasks).

## Related MITRE

- T1021.001 Remote Desktop Protocol
- T1021.002 SMB/Windows Admin Shares
