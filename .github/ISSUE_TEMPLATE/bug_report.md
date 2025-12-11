---
name: Bug Report
about: Create a report to help us improve TravelNet Portal
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
A clear and concise description of what actually happened.

## Screenshots
If applicable, add screenshots to help explain your problem.

## Environment Information
- **Raspberry Pi Model**: [e.g. Pi 4B 4GB]
- **OS Version**: [e.g. Raspberry Pi OS Bullseye]
- **TravelNet Portal Version**: [e.g. v2.0.0]
- **WiFi Adapters**: [e.g. Built-in + USB AC600]
- **Browser**: [e.g. Chrome 96, Safari 15]

## Network Configuration
- **AP Interface**: [e.g. wlan0]
- **Client Interface**: [e.g. wlan1]
- **Ethernet**: [Yes/No]

## Log Output
Please include relevant log output:

```
# TravelNet Portal logs
sudo journalctl -u travelnet --since "1 hour ago"

# System logs (if relevant)
sudo journalctl --since "1 hour ago" | grep -i error
```

## Additional Context
Add any other context about the problem here.

## Troubleshooting Attempted
- [ ] Restarted TravelNet service
- [ ] Rebooted Raspberry Pi
- [ ] Checked network interfaces
- [ ] Reviewed logs
- [ ] Tried different browser
- [ ] Other: ___________