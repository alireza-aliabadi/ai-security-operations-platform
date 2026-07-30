# C2 Containment SOP

## Scope

Standard operating procedure for command-and-control beaconing containment.

## Procedure

1. Block destination IPs and domains at the perimeter firewall and DNS sinkhole.
2. Capture memory from the beaconing host before isolation when safe.
3. Check for scheduled tasks, services, and WMI persistence.
4. Hunt for related hashes and process trees across EDR.
5. Watch for known indicators such as `185.220.101.45` and `evil.example.com`.

## Escalation

Escalate to incident commander for confirmed C2 with data staging evidence.
