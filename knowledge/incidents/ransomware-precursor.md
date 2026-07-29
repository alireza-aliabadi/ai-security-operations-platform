# Incident: Ransomware Precursor Hunt

## Summary

Detection of suspicious service creation and shadow copy deletion on a file server, treated as ransomware precursor activity.

## Actions Taken

1. Isolated the file server VLAN segment
2. Captured volatile memory and disk image
3. Hunted for similar process trees across the estate
4. Restored from known-good backup after clean rebuild

## Lessons

Earlier EDR alerting on `vssadmin` abuse would have reduced dwell time.
