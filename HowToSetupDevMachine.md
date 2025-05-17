1. open cmd.exe in RepoRoot (you should 
  1.1. run in cmd `py -3 -m venv .venv`
  1.2. run in cmd `.\.venv\Scripts\activate`
  1.3. run in cmd `python -m pip install --upgrade pip setuptools wheel`
  1.4. run in cmd `python -m pip install -U "discord.py[voice]" python-dotenv`
2. Create `Secret Token` from bot dashboard, copy it into file:
  "$Root$\\src\\.env"
  **The file is gitignored, double check if you are NOT leaking secret token!**
3. 

**Why `python-dotenv`?** It automatically loads the token from `.env`, keeping secrets out of your codebase.
