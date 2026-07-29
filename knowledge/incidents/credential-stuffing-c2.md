# Incident: Credential Stuffing to C2

## Summary

External brute-force against account `jdoe` succeeded, followed by malware execution and C2 to `185.220.101.45` / `evil.example.com`, then lateral movement to `SRV-APP-12` via RDP.

## Timeline Highlights

1. Password spray against VPN and workstation logons
2. Successful interactive logon on `WS-FINANCE-07`
3. PowerShell payload (`trojan.loader.x64`)
4. Beaconing to C2 infrastructure
5. RDP lateral movement to application server

## Outcome

Hosts isolated, credentials reset, IOCs blocked at perimeter.
