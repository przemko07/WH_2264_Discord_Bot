import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GOOD = TOKEN != None and len(str(TOKEN)) > 0

if (GOOD):
    print(f"FOUND TOKEN: \"{TOKEN}\"")
else:
    print(f"NOT FOUND TOKEN: \"{TOKEN}\"")