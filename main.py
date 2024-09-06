#!/usr/bin/env python3
"""Main script"""
import json
import os

import requests
from dotenv import load_dotenv
from notifiers import get_notifier


def send_slack(hook, subject, message, url):
    slack = get_notifier("slack")
    slack.notify(message=f"{subject} {message} {url}", webhook_url=hook)


def scrape_all_pages(start_url):
    result = []
    page = 1
    while True:
        print(f"Scraping page: {start_url}&page={page}")
        response = requests.get(start_url + f"&page={page}")
        if response.status_code == 200:
            data = json.loads(response.content)
            estates = data['_embedded']['estates']
            if not estates:
                break
            else:
                for estate in estates:
                    result.append({
                        'id': estate['hash_id'],
                        'price': estate['price'],
                        'location': estate['locality'],
                        'is_auction': estate['is_auction'],
                        'labels': estate['labelsAll'][0],
                        'name': estate['name'],
                        'link': f"https://www.sreality.cz/detail/prodej/dum/rodinny/{estate['seo']['locality']}/{estate['hash_id']}",
                        'images': [img['href'] for img in estate['_links']['images']],
                    })
                page += 1

        else:
            print("failed")
            exit(0)
    return result


def save_houses(cache_file, links, new_hook, update_hook):
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            visited_links = json.load(file)
            if not isinstance(visited_links, dict):
                visited_links = {}
    else:
        visited_links = {}

    for house in links:
        house_id = str(house['id'])
        body = f"""\n
        * *Price*: {house['price']:,} Kc
        * *Location*: {house['location']}
        * *Photo*: {house['images'][0]}
        """
        if house_id not in visited_links:
            visited_links[house_id] = house
            send_slack(new_hook, house['name'], body, house['link'])
        else:
            if house['price'] != visited_links[house_id]['price']:
                send_slack(update_hook, "House price update", f"From {visited_links[house_id]['price']:,} to {house['price']:,}", house['link'])

    with open(cache_file, 'w') as file:
        json.dump(visited_links, file, indent=4)


if __name__ == "__main__":
    load_dotenv()
    urls = [
        "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=2&category_sub_cb=37%7C39&category_type_cb=1&distance=10&locality_district_id=72%7C73&locality_region_id=14&per_page=60&region=Rajhrad&region_entity_id=5820&region_entity_type=municipality", # rajhrad
        "https://www.sreality.cz/api/cs/v2/estates?category_main_cb=2&category_sub_cb=37%7C39&category_type_cb=1&distance=10&locality_district_id=73%7C72&locality_region_id=14&per_page=60&region=%C5%A0lapanice&region_entity_id=5838&region_entity_type=municipality" # slapanice
    ]
    filtered_urls = [
        # more than 100m2 house area, more than 300m2 land, good status filters
        "https://www.sreality.cz/api/cs/v2/estates?building_condition=1%7C4%7C5%7C6&category_main_cb=2&category_sub_cb=37%7C39&category_type_cb=1&czk_price_summary_order2=0%7C15000000&distance=10&estate_area=300%7C10000000000&locality_district_id=72%7C73&locality_region_id=14&per_page=60&region=Rajhrad&region_entity_id=5820&region_entity_type=municipality&usable_area=100%7C10000000000",  # rajhrad
        "https://www.sreality.cz/api/cs/v2/estates?building_condition=1%7C4%7C5%7C6&category_main_cb=2&category_sub_cb=37%7C39&category_type_cb=1&czk_price_summary_order2=0%7C15000000&distance=10&estate_area=300%7C10000000000&locality_district_id=73%7C72&locality_region_id=14&per_page=60&region=%C5%A0lapanice&region_entity_id=5838&region_entity_type=municipality&usable_area=100%7C10000000000"  # slapanice
    ]
    for base_url in urls:
        houses = scrape_all_pages(base_url)
        save_houses("visited_houses.json", houses, os.getenv('SLACK_WEBHOOK_NEW'), os.getenv('SLACK_WEBHOOK_UPDATE'))

    for filtered_url in filtered_urls:
        houses = scrape_all_pages(filtered_url)
        save_houses("visited_houses_filtered.json", houses, os.getenv('SLACK_WEBHOOK_FILTERED'), os.getenv('SLACK_WEBHOOK_FILTERED_UPDATE'))
