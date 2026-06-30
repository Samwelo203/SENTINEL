# SENTINEL-KE — GitHub-only edition (100% free, no card required)

Same system, rebuilt to run entirely on GitHub:

- **GitHub Actions** (free, scheduled) replaces Cloud Scheduler + Cloud Run Job — runs
  the pipeline daily at 06:00 EAT.
- **The repo itself** (`docs/data/*.json`) replaces BigQuery + Firestore — the pipeline
  commits updated risk scores back to the repo every day.
- **GitHub Pages** replaces the Cloud Run dashboard — a static site that reads those
  JSON files directly, no server needed.

Same caveats as before: NDVI/WASH/mobility/health-capacity are placeholder values
(see `pipeline/data_sources.py`), and the model trains on synthetic labels until you
plug in real historical outbreak data (see `model/train.py`).

## Step-by-step deployment

### 1. Create the GitHub repo
- Go to **https://github.com** and sign in (or create a free account)
- Click **+ → New repository** (top right)
- Name it `sentinel-ke`, set it to **Public** (required for free unlimited Actions
  minutes — private repos get limited free minutes too, but public is simplest),
  leave "Add a README" unchecked, click **Create repository**

### 2. Push this folder to the repo
On your computer, open a terminal inside the unzipped `sentinel-ke-github` folder:
```bash
git init
git add .
git commit -m "Initial SENTINEL-KE setup"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/sentinel-ke.git
git push -u origin main
```
(Replace `YOUR-USERNAME` with your actual GitHub username — you'll see the exact
URL on the empty repo page after step 1.)

No `git` installed? Instead: on the repo page, click **uploading an existing file**,
drag the entire folder contents in, and commit. (Slower for big folders, but needs
no software at all.)

### 3. Turn on GitHub Pages
- In your repo, click **Settings → Pages** (left sidebar)
- Under "Build and deployment", set **Source** to **Deploy from a branch**
- Set **Branch** to `main` and folder to **`/docs`**, click **Save**
- GitHub gives you a URL like `https://YOUR-USERNAME.github.io/sentinel-ke/` —
  this is your dashboard, live in about a minute

### 4. Run the pipeline for the first time
- Click the **Actions** tab in your repo
- You'll see "SENTINEL-KE Daily Pipeline" listed — click it
- Click **Run workflow** (top right) → **Run workflow** again to confirm
- Watch it run (takes 1–3 minutes); it will train the model, fetch data, and
  commit `docs/data/latest.json` + `docs/data/history.json` back to your repo
- Once it finishes, refresh your dashboard URL from step 3 — you'll see real data

### 5. After that, it's automatic
The workflow runs every day at 06:00 EAT on its own — nothing more to do. Check the
**Actions** tab anytime to see run history or trigger it manually.

## Repository layout
```
sentinel-ke-github/
├── .github/workflows/daily.yml   # the scheduled job definition
├── pipeline/                       # fetch data -> features -> predict -> write JSON
├── model/                            # train.py (synthetic labels, see warning) + predict.py
└── docs/                                # GitHub Pages site
    ├── index.html                          # the dashboard
    └── data/latest.json, history.json        # written by the pipeline daily
```

## Improving this later
- **Real outbreak data**: edit `model/train.py` to load real DHIS2-sourced labels
  instead of `generate_synthetic_training_data()`.
- **Real WASH/mobility/health-capacity data**: edit the `fetch_*` stub functions in
  `pipeline/data_sources.py` — each is isolated so swapping one doesn't touch the rest.
- **NDVI**: get a free NASA Earthdata token at https://urs.earthdata.nasa.gov/ and
  add it as a GitHub Actions secret (`Settings → Secrets and variables → Actions`),
  then wire it into `fetch_ndvi`.
