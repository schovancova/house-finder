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
        page = 1

        while True:
            current_url = f"{start_url}&page={page}" if page > 1 else start_url
            print(f"Scraping page: {current_url}")

            response = requests.get(current_url, headers=self.headers)
            if response.status_code == 200:
                data = json.loads(response.content)
                estates = data['_embedded']['estates']
                if not estates:
                    break
                else:
                    for estate in estates:
                        result.append(Estate(estate))
                    page += 1
            else:
                print("Failed to fetch data")
                break

        return result
