# DEPRECATED: This standalone script is kept for backward compatibility only.
# The collection logic has been migrated to the FastAPI backend under
# `backend/scrapers/`. To collect papers into the database, run:
#     cd backend && python3 scrapers/run.py --max 100
# This file still works to refresh the legacy papers.json seed file.
import requests
import json
import time
import xml.etree.ElementTree as ET
import sys

DIFFUSION_KEYWORDS = [
    'diffusion', 'denoising', 'DDPM', 'score-based', 'generative model',
    'diffusion model', 'diffusion probabilistic', 'latent diffusion',
    'stable diffusion', 'text-to-image', 'image generation', 'generative'
]

ARXIV_BASE_URL = 'https://export.arxiv.org/api/query'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_arxiv_papers(search_query, max_results=100):
    papers = []
    start = 0
    batch_size = min(50, max_results)
    
    while start < max_results:
        params = {
            'search_query': search_query,
            'start': start,
            'max_results': batch_size,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        try:
            response = requests.get(ARXIV_BASE_URL, params=params, headers=HEADERS)
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
            
            entries = root.findall('atom:entry', ns)
            
            if not entries:
                break
            
            for entry in entries:
                title = entry.find('atom:title', ns).text.strip()
                summary = entry.find('atom:summary', ns).text.strip() if entry.find('atom:summary', ns) is not None else ''
                
                authors = []
                author_elements = entry.findall('atom:author', ns)
                for author in author_elements:
                    name = author.find('atom:name', ns).text.strip()
                    authors.append(name)
                
                pdf_url = None
                abs_url = None
                links = entry.findall('atom:link', ns)
                for link in links:
                    if link.get('title') == 'pdf' or (link.get('href') and link.get('href').endswith('.pdf')):
                        pdf_url = link.get('href')
                    elif link.get('rel') == 'alternate' or (link.get('href') and '/abs/' in link.get('href')):
                        abs_url = link.get('href')
                
                arxiv_id = entry.find('atom:id', ns).text.strip().split('/')[-1]
                if not pdf_url:
                    pdf_url = f'https://arxiv.org/pdf/{arxiv_id}.pdf'
                if not abs_url:
                    abs_url = f'https://arxiv.org/abs/{arxiv_id}'
                
                tags = []
                full_text = (title + ' ' + summary).lower()
                for keyword in DIFFUSION_KEYWORDS:
                    if keyword.lower() in full_text:
                        tags.append(keyword)
                
                if tags:
                    papers.append({
                        'title': title,
                        'authors': authors,
                        'conference': 'arXiv',
                        'pdf_url': pdf_url,
                        'abs_url': abs_url,
                        'abstract': summary,
                        'tags': tags
                    })
            
            print(f"Fetched {len(entries)} papers, total found: {len(papers)}")
            
            start += batch_size
            
            if len(entries) < batch_size:
                break
            
            time.sleep(2)
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 30))
                print(f"Rate limited. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                continue
            else:
                print(f"HTTP Error: {e}")
                break
        except Exception as e:
            print(f"Error fetching papers: {e}")
            break
    
    return papers

def load_existing_papers(filename='papers.json'):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_to_json(papers, filename='papers.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(papers)} papers to {filename}")

def check_if_needs_update(existing_papers, min_papers=30):
    if len(existing_papers) < min_papers:
        print(f"⚠️  Current papers ({len(existing_papers)}) < minimum ({min_papers}), need update")
        return True
    
    print(f"✅  Already have {len(existing_papers)} papers, may not need update")
    return False

if __name__ == '__main__':
    force_update = '--force' in sys.argv
    existing_papers = load_existing_papers()
    
    if force_update or check_if_needs_update(existing_papers):
        print("\nFetching diffusion papers from arXiv...")
        
        search_queries = [
            'diffusion',
            'diffusion model',
            'denoising diffusion',
            'stable diffusion',
            'latent diffusion',
            'score-based generative'
        ]
        
        seen_titles = {p['title'] for p in existing_papers}
        all_papers = existing_papers.copy()
        
        for query in search_queries:
            print(f"\nSearching for: {query}")
            papers = fetch_arxiv_papers(query, max_results=50)
            
            new_count = 0
            for paper in papers:
                if paper['title'] not in seen_titles:
                    seen_titles.add(paper['title'])
                    all_papers.append(paper)
                    new_count += 1
            
            print(f"Found {new_count} new papers, total unique papers: {len(all_papers)}")
            
            if len(all_papers) >= 100:
                break
        
        save_to_json(all_papers)
    else:
        print("\nNo update needed. To force update, run with --force")
