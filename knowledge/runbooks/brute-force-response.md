# Brute Force Response Runbook

## Purpose

Respond to credential stuffing and password spray attacks against identity providers.

## Steps

1. Confirm failed authentication spikes across identity providers (Windows 4625, Entra ID, VPN).
2. Extract source IPs and correlate with threat intelligence.
3. Check for successful logins from the same sources within the attack window.
4. Contain: block malicious IPs at the perimeter, force password resets, invalidate sessions.
5. Document IOCs and update detection rules / lockout policies.

## Related MITRE

- T1110 Brute Force
- T1078 Valid Accounts
