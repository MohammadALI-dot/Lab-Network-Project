import requests
from common import polite_get

s = requests.Session()
r = polite_get(s, "https://example.com", method="bs4", delay=1)
print("status:", r.status_code, "| bytes:", len(r.content))
