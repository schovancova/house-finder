# scraper/Scraper.py
import requests
import json
from model.Estate import Estate


class Scraper:
    def __init__(self):
        # if you don't provide this, sreality will give you prices with *slight* offset sometime. pain to debug.
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36",
        }

    def scrape_all_pages(self, start_url):
        """Scrape all pages starting from the initial URL."""
        result = []
        offset = 0
        limit = 100
        max_iter = 500

        while True:
            current_url = f"{start_url}&limit={limit}&offset={offset}"
            print(f"Scraping page: {current_url}")

            response = requests.get(current_url, headers=self.headers)
            data = json.loads(response.content)
            estates = data['results']
            if not estates:
                break
            else:
                for estate in estates:
                    result.append(Estate(estate))
                offset += limit
            if data['pagination']['limit'] + data['pagination']['offset'] >= data['pagination']['total']:
                break
            max_iter -= 1
            if max_iter < 0:
                break

        return result
