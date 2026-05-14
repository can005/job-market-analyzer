import json
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from ingestion.config import HN_API_BASE_URL, HN_JOBS_FILENAME, HN_RAW_DATA_PATH


def search_hn(query:str, 
              tags:str='story,author_whoishiring',
              hits_per_page:int=10,
              from_up_to_days:int=180) -> dict:
    threshold = int((datetime.now() - timedelta(days=from_up_to_days)).timestamp())
    url = f"{HN_API_BASE_URL}search_by_date"
    params = {
        "query": query,
        "tags": tags,
        "hitsPerPage": str(hits_per_page),
        "numericFilters": f"created_at_i>{threshold}"
    }

    response = requests.get(url, params=params)
    return response.json()

def fetch_thread(post_id:str) -> dict:
     url = f"{HN_API_BASE_URL}items/{post_id}"
     response = requests.get(url)
     return response.json()

def clean_html(text:str) -> str:
  return BeautifulSoup(text, "html.parser").get_text(separator=" ")

def main() -> None:
    results = search_hn("Ask HN: Who is Hiring")
    thread_ids = [hit['objectID'] for hit in results['hits']]
    jobs = []
    for thread_id in thread_ids:
        jobs_thread = fetch_thread(thread_id)
        children = jobs_thread['children']
        time.sleep(0.5)
        for child in children:
            if child.get('text'):
                jobs.append({
                    'id': child['id'],
                    'text': clean_html(child['text']),
                    'author': child['author'],
                    'created_at': child['created_at'],
                })

    print(len(jobs))
    with open(HN_RAW_DATA_PATH + HN_JOBS_FILENAME, "w") as f:
        json.dump(jobs,f)
    
    
if __name__ == '__main__':
    main()