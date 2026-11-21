# Web scraping efficiency and network behavior: BS4 vs API vs Selenium

A lab project that collects the same football player statistics from one website in **three different ways** (BeautifulSoup, JSON/API files, Selenium), **measures** each way on the network (time, bandwidth, requests, latency, connections), tests a **firewall** and **multithreading**, and then trains a small **machine-learning model** that suggests a player's position (GK, DF, MF, FW) from his statistics.

* **Target site:** FotMob, La Liga 2026/2027 (26 statistics, about 490 players)
* **Tested on:** Ubuntu 24.04 under WSL2 (Windows), Python 3.12
* **Author / course:** `MhamadAli - Mhamad Farhat - Mehde Ayoub` / `Lab Network Programming`

---

## 1. Results at a glance

Average of 3 runs per method (all three collect identical data: 491 players, 26 statistics):

| Method | Data on the wire | Time | Avg latency | TCP connections |
|---|---|---|---|---|
| API (JSON files) | 375 KB | 57.6 s | 151 ms | 2 |
| BeautifulSoup (HTML pages) | 2,739 KB | 67.3 s | 330 ms | 2 |
| Selenium (headless Chrome) | 80,449 KB (about 79 MB) | 165.4 s | 3,350 ms | 149 |

The API used about 7 times less bandwidth than BS4 and about 214 times less than Selenium. The times include a deliberate 2-second pause after every request.

Position classifier (Logistic Regression, 29 per-90-minute features, 337 players): about **80% accuracy** (0.795 ± 0.048 in repeated cross-validation), perfect for goalkeepers, weakest for midfielders.

These numbers are a snapshot taken in November 2026. The site changes while the season is played, so a new run gives different numbers.

---

## 2. Read this first: responsible use

FotMob's Terms of Use prohibit scraping and bulk retrieval of its data without its written consent. This project was done for **learning only**, with the approval of the course instructor. That approval is not a consent from FotMob.

If you run this project, you take the same responsibility:

* Use it for learning only. Do not publish or sell the data.
* Do not run the scrapers again and again. One run is about 26 requests.
* Keep the pauses and the shared speed limit in the code. Do not remove them.
* Respect `robots.txt` (the code checks it before every request; the `/api/` path of fotmob.com is never used).
* If the site answers HTTP 403 or 429, **stop** and wait. Do not try to get around a block.

---

## 3. What you need

| Part of the project | What it needs |
|---|---|
| Scrapers, data cleaning, machine learning | Linux, macOS or Windows with Python 3.10+ (tested only on Ubuntu 24.04 with Python 3.12), internet |
| Selenium scraper | Google Chrome (the driver is downloaded automatically) |
| **Network measurement and firewall test** | **Linux only** (Ubuntu or WSL2 on Windows): `tcpdump`, `ss`, `iftop`, `nload`, `ufw`, `tshark`, and `sudo` rights |

Windows users: install WSL2 with Ubuntu first (section 5, step 1). macOS users: everything except the network measurement and the firewall test should work, but it was not tested.

---

## 4. Repository structure

```
.
├── scrapers/
│   ├── common.py                 shared helper: robots.txt check, 2 s pause, request log
│   ├── bs4_scraper.py            scraper 1: BeautifulSoup (HTML pages)
│   ├── api_scraper.py            scraper 2: JSON files (the "API" method)
│   ├── selenium_scraper.py       scraper 3: headless Chrome
│   ├── threaded.py               multithreaded BS4 / API with a shared speed limit
│   ├── clean_data.py             data cleaning -> data/clean_data.csv
│   ├── compare_data.py           checks that the three datasets are identical
│   ├── analyze_metrics.py        builds the metrics table and charts from the measurements
│   ├── plot_log.py               log-scale comparison chart
│   ├── selenium_browser_requests.py   counts the requests of one browser page load
│   ├── firewall_test.py          one request per method (used by the firewall test)
│   ├── make_eda_notebook.py      creates notebooks/ml_analysis.ipynb (EDA part)
│   ├── add_ml_cells.py           adds the machine-learning cells to that notebook
│   ├── make_network_notebook.py  creates notebooks/network_analysis.ipynb
│   ├── predict_position.py       the position suggestion program
│   ├── show_ml_outputs.py        prints the text outputs of the ML notebook (for screenshots)
│   └── check_*.py, explore_*.py, inspect*.py, test_*.py
│                                 small exploration/test scripts used to choose the site and
│                                 to understand its data (evidence for the report)
├── network/
│   ├── run_measure.sh            runs one scraper while tcpdump and ss record the network
│   ├── firewall_test.sh          ufw deny / reject test for the three methods
│   ├── metrics.csv, metrics_summary.csv, comparison*.png    measurement results
│   ├── threading_results.csv, firewall_results.csv          threading and firewall results
│   ├── request_log.csv           log of every request made by the scrapers
│   ├── measure/                  per-run outputs (open connections, scraper output, times.csv)
│   ├── pcap/                     packet captures (NOT in the repository: too large, created by you)
│   └── screenshots/              screenshots used by the network notebook
├── data/                         bs4_data.csv, api_data.csv, selenium_data.csv, clean_data.csv ...
├── models/position_model.joblib  the trained position classifier
├── notebooks/                    ml_analysis.ipynb, network_analysis.ipynb
├── report/figures/               charts saved by the notebooks
├── requirements.txt              Python libraries
└── README.md
```

---

## 5. Setup, step by step

### Step 1. Get a Linux terminal

* **Linux:** open a terminal and go to step 2.
* **Windows:** open PowerShell **as administrator** and run:
  ```powershell
  wsl --install -d Ubuntu-24.04
  ```
  Restart the computer if it asks, open "Ubuntu 24.04" from the Start menu and create a user name and password. Every command below goes into this **Ubuntu** terminal (the prompt looks like `name@computer:~$`), not into PowerShell or Command Prompt.
* **macOS:** use the Terminal, and install Python and Git with Homebrew. Skip the network tools in step 2.

### Step 2. Install the system packages (Ubuntu / WSL)

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip curl net-tools
sudo apt install -y tcpdump iftop nload ufw tshark
```

* `sudo` asks for your password. Nothing appears while you type, which is normal. Type it on its own line and press Enter.
* During the `tshark` install, a window may ask "Should non-superusers be able to capture packets?". Choose **No**.
* The second `apt` line is only needed for the network measurement (section 6, part E to H).

### Step 3. Install Google Chrome (needed for the Selenium scraper)

```bash
cd ~
wget --progress=dot:giga https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
ls -lh google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
google-chrome --version
```

The `.deb` file must be about 100 MB or more. If it is tiny, the download failed: delete it and download again. You do **not** need to install a chromedriver: Selenium downloads the matching one by itself the first time (internet needed).

### Step 4. Download the project

```bash
cd ~
git clone https://github.com/MohammadALI-dot/Lab-Network-Project.git
cd Lab-Network-Project
chmod +x network/*.sh
```

### Step 5. Create the Python environment and install the libraries

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Your prompt now starts with `(venv)`. **You must run `source venv/bin/activate` in every new terminal**, from the project folder. Without it, Python cannot find the libraries.

### Step 6. Check the installation

```bash
python -c "import requests, bs4, selenium, pandas, sklearn, matplotlib, seaborn, joblib, nbformat; print('All good')"
google-chrome --version
which tcpdump ss iftop nload ufw tshark
```

You should see `All good`, a Chrome version, and a path for each of the six tools.

---

## 6. Run the project

Always run the commands from the **project folder** with the environment active:

```bash
cd ~/Lab-Network-Project
source venv/bin/activate
```

### Quick start: try the finished model (no scraping, about 1 minute)

The repository already contains the cleaned data and the trained model:

```bash
python scrapers/predict_position.py tackles_p90=2 interceptions_p90=1.2 clearances_p90=4 passes_p90=45
python scrapers/predict_position.py shots_p90=3.2 goals_p90=0.6 shots_on_target_p90=1.5
python scrapers/predict_position.py saves_p90=3 goals_conceded_p90=1.2
```

Each run prints the suggested position and how sure the model is for each of GK, DF, MF and FW. Run it without arguments to be asked for each statistic. Values are **per 90 minutes** (a total is converted with: statistic ÷ minutes played × 90).

If you see a scikit-learn version warning or an error, rebuild the model by running part C below.

To look at the notebooks without running anything, open `notebooks/ml_analysis.ipynb` on GitHub (it shows the saved results).

### A. Run the three scrapers (each overwrites its CSV file in `data/`)

```bash
python scrapers/bs4_scraper.py          # about 70 seconds  -> data/bs4_data.csv
python scrapers/api_scraper.py          # about 60 seconds  -> data/api_data.csv
python scrapers/selenium_scraper.py     # about 4 minutes   -> data/selenium_data.csv
```

Each prints a summary at the end (players, columns, requests, time). Expect about 490 players and 56 to 57 columns. Do not run these more often than needed (see section 2). Every request is appended to `network/request_log.csv`.

Optional check that the three datasets are identical:

```bash
python scrapers/compare_data.py
```

### B. Clean the data

```bash
python scrapers/clean_data.py           # keeps players with at least 270 minutes
```

This writes `data/clean_data.csv` (about 337 players and 29 features, with the positions GK, DF, MF, FW) and prints the cleaning steps. A different minimum of minutes can be given as an argument, for example `python scrapers/clean_data.py 900`.

### C. Exploratory analysis and machine learning (about 2 minutes)

```bash
python scrapers/make_eda_notebook.py     # creates notebooks/ml_analysis.ipynb (overwrites it)
python scrapers/add_ml_cells.py          # adds the model cells
jupyter nbconvert --to notebook --execute --inplace notebooks/ml_analysis.ipynb
jupyter nbconvert --to html notebooks/ml_analysis.ipynb
```

Open `notebooks/ml_analysis.html` in a browser to read the results. The charts are saved in `report/figures/`, and the trained model is saved to `models/position_model.joblib` (this is the file `predict_position.py` loads). To print the text results of one section in the terminal: `python scrapers/show_ml_outputs.py 7.3`.

### D. Use the position suggestion program

See the quick start above: `python scrapers/predict_position.py`.

### E. Network measurement (Linux only, about 25 minutes)

`run_measure.sh` runs one scraper while `tcpdump` records the packets and `ss` samples the open connections every second. It needs `sudo`; it asks for your password **once**, at the start. Do not use the network for other things in Ubuntu while it runs.

**Find your network interface first.** The script uses `eth0` (the usual name under WSL2):

```bash
ip -br a
```

If your interface has another name (for example `enp3s0` or `wlan0`), edit the script before running it:

```bash
grep -n "tcpdump" network/run_measure.sh
sed -i 's/tcpdump -i eth0/tcpdump -i YOUR_INTERFACE/' network/run_measure.sh
```

(`eth0` is used instead of `-i any`, because on WSL2 a capture on `any` records every packet twice.)

**If you want your own measurement instead of the one in the repository, start fresh.** The results table reads the log and the timing file together, so old and new files must not be mixed:

```bash
mkdir -p network/old
mv network/request_log.csv network/measure network/pcap network/old/ 2>/dev/null
```

**Run each scraper 3 times, one at a time, alternating:**

```bash
for run in 1 2 3; do
  for m in bs4 api selenium; do
    ./network/run_measure.sh $m $run
  done
done
```

Or a single run to test: `./network/run_measure.sh api 1`.

**Build the table and the charts:**

```bash
python scrapers/analyze_metrics.py       # network/metrics.csv, metrics_summary.csv, comparison.png
python scrapers/plot_log.py              # network/comparison_log.png (log scale)
python scrapers/selenium_browser_requests.py   # how many requests Chrome makes for ONE page
```

> **Warning:** `run_measure.sh` stops all running `tcpdump` processes at the end (`pkill tcpdump`). Do not run it on a machine where another capture is running.

**To watch the traffic live**, open a second terminal while a scraper runs in the first one:

```bash
sudo iftop -i eth0 -n          # press q to quit
nload eth0                     # press q to quit
sudo ss -tnp | grep -E "python|chrome"
```

To open the captures in Wireshark, install Wireshark and open the files in `network/pcap/`, then use Statistics > Conversations and Statistics > I/O Graph.

### F. Firewall test (Linux only, about 2 minutes)

The test blocks outgoing HTTPS with `ufw` (first `deny out 443`, then `reject out 443`), runs one request per method under each condition, then removes the rule.

```bash
./network/firewall_test.sh 2>&1 | tee network/firewall_output.txt
cat network/firewall_results.csv
```

Enter your password once at the start. Read this before you run it:

* The script **turns `ufw` on and, at the end, turns it off**. Only run it on a machine where `ufw` was off before (the default on Ubuntu and WSL). If your firewall is on, do not run it.
* While the rule is active, `git push`, `pip` and `apt` do not work. The script removes the rule at the end, even if something fails.
* Check afterwards with `sudo ufw status`. It must say `Status: inactive`.
* Do the whole test within about one hour of a Selenium run (Selenium keeps its driver in a short-lived cache and must not need the network while the rule is active).
* Under WSL, `ufw enable` can fail if the kernel lacks the firewall modules. In that case run the test in an Ubuntu virtual machine.

### G. Multithreading test (about 5 minutes)

All threads share one speed limit: a new request may start only every `interval` seconds.

```bash
# usage: python scrapers/threaded.py <api|bs4> <threads> <interval in seconds>
python scrapers/threaded.py api 4 1.0
for i in 1.0 0.25; do for w in 1 4 8; do python scrapers/threaded.py api $w $i; done; done
for w in 1 4 8; do python scrapers/threaded.py bs4 $w 0.25; done
python scrapers/threaded.py bs4 4 1.0
cat network/threading_results.csv
```

The BS4 runs download about 16 MB each, so do not repeat them without a reason. The `same_data_as_csv` column must say `26/26`. It compares with `data/bs4_data.csv` or `data/api_data.csv`, so run part A first.

### H. Network analysis notebook

```bash
python scrapers/make_network_notebook.py
jupyter nbconvert --to notebook --execute --inplace notebooks/network_analysis.ipynb
jupyter nbconvert --to html notebooks/network_analysis.ipynb
```

It reads the files in `network/` and draws the comparison, the firewall and threading results, and your screenshots (put them in `network/screenshots/`; file names are listed in the last section of the notebook). The "traffic over time" chart needs the `.pcap` files from part E.

---

## 7. How long does everything take?

| Step | Time | Requests to the site |
|---|---|---|
| Quick start (prediction) | 1 minute | 0 |
| A. Three scrapers | about 6 minutes | about 80 |
| B. Cleaning | seconds | 0 |
| C. Notebook with ML | about 2 minutes | 0 |
| E. Full measurement (9 runs) | about 25 minutes | about 240 |
| F. Firewall test | about 2 minutes | 0 (blocked) or a few |
| G. Multithreading | about 5 minutes | about 290 |
| H. Network notebook | about 1 minute | 0 |

---

## 8. Change the season or the league

The target is set in one place, at the top of `scrapers/bs4_scraper.py`:

```python
LEAGUE_ID, SEASON_ID, SLUG = 87, 38843, "laliga"
```

The API, Selenium and threaded scrapers import these values. La Liga is league 87. The season ids seen on the site are 38843 (2026/2027), 27233 (2025/2026) and 23686 (2024/2025). Other leagues have other ids, which you can read from the address of the league's statistics page on the site.

A full season has about 38 matches per player instead of about 12, so use a larger minimum of minutes when cleaning (for example `python scrapers/clean_data.py 900`).

---

## 9. Troubleshooting

| Problem | Cause and fix |
|---|---|
| `error: externally-managed-environment` when installing with pip | The virtual environment is not active. Run `source venv/bin/activate`. Do not use `--break-system-packages`. |
| `ModuleNotFoundError: No module named 'pandas'` (or selenium, bs4 ...) | Same: the prompt must start with `(venv)`. |
| `python: command not found` | Outside the environment only `python3` exists. Activate the environment, or use `python3`. |
| Several pasted commands behave strangely after a `sudo` command | `sudo` asks for the password and takes the next pasted lines as the password. Run `sudo -v` first, type the password, then paste the rest. |
| Selenium: "session not created", Chrome not found | Chrome is not installed (step 3). Check `google-chrome --version`. |
| Selenium: "Unable to obtain driver" | No internet for the driver download, or the firewall rule from part F is still active. Check `sudo ufw status`. |
| `tcpdump: No such device exists` | Wrong interface name: see `ip -br a` and the `sed` command in part E. |
| Packets counted twice | You captured on `any` under WSL2. Use the real interface (`eth0`). |
| HTTP 403 or 429 from the site | The site blocks or limits you. Stop and wait. Do not retry in a loop. |
| `KeyError` or `NoneType` when reading the page data | The site changed its page structure. The scrapers need to be adapted. |
| `No such kernel named python3` (Jupyter) | `python -m ipykernel install --user` |
| scikit-learn warning when loading `position_model.joblib` | The model was saved with another scikit-learn version. Rebuild it with part C. |
| `analyze_metrics.py` shows wrong or missing rows | Old and new measurement files are mixed. Start fresh as described in part E. |
| `ufw enable` fails under WSL | The WSL kernel lacks the firewall modules. Use an Ubuntu virtual machine for part F. |
| `git push` or `pip` fail with a connection error | The firewall test is still active. `sudo ufw status` must say `inactive`. |

---

## 10. Limitations

* One league, one season (about 12 matches per player), 337 players after cleaning and only 23 goalkeepers: the accuracy estimate is uncertain (see the ± value).
* The "API" is a set of JSON data files found through the website, not an official API, and the page structure is not documented. Both can change without notice, which can break the scrapers.
* The run times include the deliberate pauses between requests.
* Three runs per method is a small sample. WSL2 adds a virtual network layer, so native Linux can give different numbers.
* The position labels come from the site's own position codes, mapped to four classes.

---

## 11. Data and credits

All statistics come from FotMob and belong to their owners. The files in `data/` are a small snapshot kept only for this course project. Do not redistribute them.
