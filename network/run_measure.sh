#!/bin/bash
# usage: ./network/run_measure.sh <bs4|api|selenium> <run_number>
METHOD=$1; RUN=$2
cd "$(dirname "$0")/.."
source venv/bin/activate
mkdir -p network/pcap network/measure
PCAP=network/pcap/${METHOD}_run${RUN}.pcap
CONN=network/measure/${METHOD}_run${RUN}_conn.csv
OUT=network/measure/${METHOD}_run${RUN}.txt
LOG=network/request_log.csv
TIMES=network/measure/times.csv
rm -f "$CONN"
[ -f "$TIMES" ] || echo "method,run,seconds,log_from,log_to" > "$TIMES"

sudo -v || exit 1
sudo tcpdump -i any -n -Z "$USER" "port 80 or port 443" -w "$PCAP" >/dev/null 2>&1 &
sleep 3
( while true; do
    echo "$(date +%s),$(ss -tn state established '( dport = :443 or dport = :80 )' | tail -n +2 | wc -l)" >> "$CONN"
    sleep 1
  done ) &
SAMPLER=$!

if [ -f "$LOG" ]; then FROM=$(( $(wc -l < "$LOG") - 1 )); else FROM=0; fi
echo ">>> running $METHOD (run $RUN) ..."
START=$(date +%s.%N)
python scrapers/${METHOD}_scraper.py > "$OUT" 2>&1
END=$(date +%s.%N)

kill $SAMPLER 2>/dev/null
sleep 2
sudo pkill -INT -x tcpdump
sleep 1
TO=$(( $(wc -l < "$LOG") - 1 ))
SECS=$(awk "BEGIN{print $END-$START}")
echo "$METHOD,$RUN,$SECS,$FROM,$TO" >> "$TIMES"
echo ">>> done: $METHOD run $RUN in $SECS s"
tail -6 "$OUT"
