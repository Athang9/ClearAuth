# COMPLETE SETUP GUIDE — Windows
## ClearAuth: Prior Authorization AI Pipeline
### Step-by-step. Nothing skipped.

---

## PART 1 — Get Your API Key (15 minutes)

### Step 1: Create an Anthropic account
1. Open your browser and go to: **https://console.anthropic.com**
2. Click "Sign Up"
3. Enter your email and create a password
4. Verify your email when they send you a confirmation

### Step 2: Add a payment method
1. Once logged in, click your profile icon (top right)
2. Click "Billing"
3. Add a credit card
4. Add at least $5 of credits (the demo will cost less than $0.50 total)

### Step 3: Get your API key
1. In the left menu, click "API Keys"
2. Click "Create Key"
3. Name it "clearauth"
4. COPY THE KEY — you won't see it again
5. Paste it into a Notepad file temporarily so you don't lose it

---

## PART 2 — Install Python (10 minutes)

### Step 1: Download Python
1. Go to: **https://www.python.org/downloads/**
2. Click the big yellow "Download Python 3.12.x" button
3. Run the installer

### Step 2: CRITICAL — Check the box at the bottom
When the installer opens, at the bottom there is a checkbox that says:
**"Add Python to PATH"**
CHECK THIS BOX before clicking Install Now.
(If you miss this, Python won't work from the terminal.)

### Step 3: Finish installing
Click "Install Now" and wait for it to finish.
Click "Close" when done.

### Step 4: Verify Python works
1. Press the **Windows key + R**
2. Type `cmd` and press Enter (this opens the Command Prompt)
3. Type this and press Enter:
   ```
   python --version
   ```
4. You should see something like: `Python 3.12.3`
   If you see an error, the PATH checkbox was missed — reinstall Python.

---

## PART 3 — Install Git (5 minutes)

### Step 1: Download Git
1. Go to: **https://git-scm.com/download/win**
2. Click "Click here to download" (64-bit)
3. Run the installer
4. Click "Next" through ALL the options — defaults are fine

### Step 2: Verify Git works
In Command Prompt, type:
```
git --version
```
You should see: `git version 2.x.x`

---

## PART 4 — Set Up the Project (20 minutes)

### Step 1: Create a folder for your project
In Command Prompt, type these commands ONE AT A TIME, pressing Enter after each:
```
cd Desktop
mkdir projects
cd projects
```
(This creates a "projects" folder on your Desktop and goes into it.)

### Step 2: Create the project folder structure
Type each command below, pressing Enter after each:
```
mkdir clearauth
cd clearauth
mkdir src
mkdir data
mkdir data\synthetic_cases
mkdir data\synthetic_pdfs
mkdir data\payer_policies
mkdir outputs
mkdir outputs\appeal_letters
mkdir tests
```

### Step 3: Create a virtual environment
A virtual environment keeps your project's packages separate from everything else.
```
python -m venv venv
```
Wait for it to finish. Then activate it:
```
venv\Scripts\activate
```
You should now see `(venv)` at the start of your command line. This means it's active.

**IMPORTANT:** Every time you open a new Command Prompt window to work on this project,
you need to run these two commands first:
```
cd Desktop\projects\clearauth
venv\Scripts\activate
```

### Step 4: Install the dependencies
```
pip install groq pydantic pypdf reportlab faker python-dotenv pytest
```
This will take 1-2 minutes. You'll see a lot of text scrolling — that's normal.

---

## PART 5 — Copy All the Code Files

Now you need to create each file. The easiest way is:

### Option A: Use VS Code (Recommended)
1. Download VS Code: **https://code.visualstudio.com/**
2. Install it (click Next through everything)
3. Open VS Code
4. Click File → Open Folder → navigate to Desktop\projects\clearauth
5. Create each file by right-clicking in the left panel → New File
6. Copy and paste the code from each section below

### Option B: Use Notepad
1. Open Notepad
2. Copy the code
3. Click File → Save As
4. Navigate to the right folder
5. In "Save as type" — select "All Files (*.*)"
6. Type the filename (e.g., `models.py`)
7. Click Save

---

## PART 6 — Create Your .env File

### Step 1: Create the file
In VS Code (or Notepad), create a new file called `.env` in your clearauth folder.

### Step 2: Add your API key
The file should contain exactly one line:
```
GROQ_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXX
```
Replace `sk-ant-XXXXXXXXXXXXXXXXXXXXXXXX` with the actual key you copied in Part 1.

### Step 3: NEVER share this file
Do NOT upload .env to GitHub. The `.gitignore` file protects it, but be careful.

---

## PART 7 — Run the Project

### Step 1: Generate synthetic test data
Make sure you're in the clearauth folder with venv active, then:
```
python data\generate_synthetic.py
```
You should see:
```
Generating synthetic clinical note PDFs...
  Created: case_001_PT_10042.pdf
  Created: case_002_PT_10073.pdf
  ...
Done! Generated 5 PDFs
```

### Step 2: Run the pipeline on your first case
```
python src\pipeline.py data\synthetic_pdfs\case_001_PT_10042.pdf
```
Watch the output. You'll see it:
1. Read the PDF
2. Send it to Claude
3. Return the PA decision

### Step 3: Try all 5 cases
```
python src\pipeline.py data\synthetic_pdfs\case_002_PT_10073.pdf
python src\pipeline.py data\synthetic_pdfs\case_003_PT_10091.pdf
python src\pipeline.py data\synthetic_pdfs\case_004_PT_10108.pdf
python src\pipeline.py data\synthetic_pdfs\case_005_PT_10127.pdf
```

### Step 4: Generate your metrics report
```
python src\metrics.py
```
This creates `outputs\metrics_report.md` — open it in VS Code to read it.

---

## PART 8 — Upload to GitHub

### Step 1: Create a GitHub account
1. Go to: **https://github.com**
2. Click "Sign Up"
3. Create your account

### Step 2: Create a new repository
1. Click the "+" icon (top right) → "New repository"
2. Name it: `clearauth`
3. Set it to Public
4. DO NOT check "Add a README" (you already have one)
5. Click "Create repository"

### Step 3: Upload your code
GitHub will show you commands. Go back to your Command Prompt and type:
```
git init
git add .
git commit -m "Initial commit: ClearAuth prior authorization pipeline"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/clearauth.git
git push -u origin main
```
Replace YOUR_USERNAME with your actual GitHub username.

GitHub will ask for your username and password.
For password — use a Personal Access Token (not your account password):
1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
2. Generate new token → check "repo" → Generate
3. Copy and paste this as your "password"

### Step 4: Verify
Go to https://github.com/YOUR_USERNAME/clearauth in your browser.
You should see all your files there.

---

## PART 9 — Before Friday

### The night before (Thursday):
1. Open Command Prompt
2. Navigate to your project: `cd Desktop\projects\clearauth`
3. Activate venv: `venv\Scripts\activate`
4. Run the full pipeline on all 5 cases
5. Run `python src\metrics.py` to regenerate the report
6. Open the slides (clearauth_deck.pptx) and run through them once
7. Read your demo_script.md out loud — practice out loud, not in your head

### Day of (Friday):
1. Have Command Prompt open and ready at your project folder
2. Have the slides open on slide 1
3. Have your GitHub repo open in the browser
4. Have the `outputs\appeal_letters` folder open in File Explorer

### The one command to run during demo:
```
python src\pipeline.py data\synthetic_pdfs\case_001_PT_10042.pdf
```
Know this by heart. Type it slowly during the meeting.

---

## TROUBLESHOOTING

### "python is not recognized"
→ Python PATH wasn't set. Reinstall Python and CHECK the "Add to PATH" box.

### "No module named anthropic"
→ Your venv isn't active. Run: `venv\Scripts\activate`

### "GROQ_API_KEY not found"
→ Your .env file is missing or in the wrong folder.
   Make sure it's in Desktop\projects\clearauth (not inside src\)

### "pypdf not found" / "reportlab not found"
→ Run: `pip install pypdf reportlab`

### Pipeline runs but returns weird JSON
→ This is a Claude API prompt issue. Run it again — it usually works on retry.

### GitHub push asks for password and fails
→ Use a Personal Access Token (see Part 8, Step 3), not your account password.

---

*You've got everything you need. Go build it.*
