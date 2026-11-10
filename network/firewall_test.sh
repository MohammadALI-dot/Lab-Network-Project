#!/bin/bash
cd "$(dirname "$0")/.."
source venv/bin/activate
sudo -v || exit 1

cleanup() {
  sudo ufw delete reject out 443/tcp >/dev/null 2>&1
  sudo ufw delete deny out 443/tcp >/dev/null 2>&1
  sudo ufw --force disable >/dev/null 2>&1
}
trap cleanup EXIT
cleanup

echo; echo "=== firewall before ==="
sudo ufw status verbose

sudo ufw default allow outgoing
sudo ufw --force enable
sudo ufw deny out 443/tcp
sudo ufw status | grep -q "Status: active" || { echo "UFW could not be enabled in this environment"; exit 1; }
echo; echo "=== rule 'deny out 443' (packets dropped silently) ==="
sudo ufw status verbose
python scrapers/firewall_test.py deny

sudo ufw delete deny out 443/tcp
sudo ufw reject out 443/tcp
echo; echo "=== rule 'reject out 443' (refused at once) ==="
sudo ufw status verbose
python scrapers/firewall_test.py reject

cleanup
echo; echo "=== firewall after cleanup ==="
sudo ufw status
python scrapers/firewall_test.py after

echo; cat network/firewall_results.csv
