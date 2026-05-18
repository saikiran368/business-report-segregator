# 📊 Business Report Segregator

Automatically extract tables from PDF files, generate AI-powered summaries using **Amazon Bedrock (Claude)**, and export to a Word document — via a clean web UI.

## ✨ Features
- 📋 Auto-detects all tables in digital PDFs
- 📸 Captures visual snapshots of each table
- 🤖 Claude generates summaries using **real data from the table**
- 📎 Optional reference doc for style-guided summaries
- 📝 Exports clean Word report (summary on top, snapshot below)

---

## ☁️ Deploy on Streamlit Cloud (5 minutes)

### Step 1 — Push to GitHub
```bash
cd ~/Documents/pdf_table_extractor_cloud
git init
git add .
git commit -m "Initial commit"
# Create a repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/business-report-segregator.git
git push -u origin main
```

### Step 2 — Create IAM User for Bedrock
1. Go to **AWS Console → IAM → Users → Create user**
2. Name it `business-report-segregator-bot`
3. Attach this inline policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": "bedrock:InvokeModel",
    "Resource": "*"
  }]
}
```
4. Create **Access Key** → copy Key ID and Secret

### Step 3 — Deploy on Streamlit Cloud
1. Go to **[share.streamlit.io](https://share.streamlit.io)**
2. Click **New app**
3. Connect your GitHub repo
4. Set **Main file path** to `app.py`
5. Click **Advanced settings → Secrets**, paste:
```toml
[aws]
AWS_ACCESS_KEY_ID     = "AKIA..."
AWS_SECRET_ACCESS_KEY = "your-secret"
AWS_DEFAULT_REGION    = "us-east-1"
```
6. Click **Deploy** — your app is live at `https://your-app.streamlit.app`

---

## 🖥️ Run Locally (Amazon Mac)
```bash
cd ~/Documents/pdf_table_extractor_cloud
streamlit run app.py
# Credentials auto-fetched via ada (Conduit)
```

---

## 📁 Project Structure
```
pdf_table_extractor_cloud/
├── app.py                  # Streamlit UI
├── pdf_table_extractor.py  # PDF table extraction + snapshots
├── ref_table_extractor.py  # Reference doc table header extraction
├── header_matcher.py       # Fuzzy header cross-matching
├── summary_engine.py       # Amazon Bedrock (Claude) summaries
├── word_output.py          # Word document builder
├── credentials_helper.py   # AWS auth (Streamlit secrets + ada)
├── requirements.txt
├── .streamlit/
│   ├── config.toml         # Theme + upload size
│   └── secrets.toml.template
└── .gitignore
```
