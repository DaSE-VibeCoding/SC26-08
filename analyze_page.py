import requests
from bs4 import BeautifulSoup

url = 'https://aclanthology.org/events/acl-2024/'
response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
soup = BeautifulSoup(response.text, 'html.parser')

print("All div classes found:")
divs = soup.find_all('div', class_=True)
classes = set()
for div in divs:
    for cls in div.get('class', []):
        classes.add(cls)

for cls in sorted(classes):
    print(f"  {cls}")

print("\nAll h3/h4 tags:")
for tag in soup.find_all(['h3', 'h4']):
    print(f"  <{tag.name}> {tag.get_text()[:50]}")

print("\nLooking for paper links:")
for a in soup.find_all('a', href=True):
    href = a['href']
    if '/papers/' in href or '/pdfs/' in href:
        print(f"  {href} - {a.get_text()[:60]}")
