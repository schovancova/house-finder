#!/usr/bin/env python3
"""Main script"""
import json
import os

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from openai import OpenAI


def scrape_page(soup):
    anchor_tags = soup.find_all('a', {'class': 'c-products__link'}, href=True)
    parcel_links = []
    for tag in anchor_tags:
        href = tag['href']
        full_link = f"https://reality.idnes.cz{href}" if href.startswith('/') else href
        if full_link not in visited_links:
            visited_links.add(full_link)
            parcel_links.append(full_link)
    return parcel_links


def scrape_description(link):
    response = requests.get(link)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        description_tag = soup.find('div', {'class': 'm-auto'})
        if description_tag:
            return ' '.join(description_tag.text.split())
    return ""


def get_next_page_url(soup):
    next_page = soup.find('a', {'class': 'next'})
    if next_page and 'href' in next_page.attrs:
        return f"https://reality.idnes.cz{next_page['href']}" if next_page['href'].startswith('/') else next_page[
            'href']
    return None


def send_slack(message_json):
    # todo
    pass


# Main scraping function with pagination
def send_to_gpt(parcel_links):
    key = api_key
    client = OpenAI(
        organization=org_id,
        api_key=key
    )
    for parcel_link in parcel_links:
        description = scrape_description(parcel_link)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are given a description of a parcel. Understand it and provide a minified JSON "
                               "with NO formatting or special tags on"
                               "output. JSON fields: area, price, width (street width, if given), location,"
                               "distance_from_Brno (in km), electricity, water, sewage_system"},
                {
                    "role": "user",
                    "content": description}
            ],
            model="gpt-4o-mini",
        )
        r = chat_completion.choices[0].message.content
        r = json.loads(r)
        print(r)

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"where is {r.get('location', '')} directionally positioned in relation to Brno? give "
                               f"me only direction name"}
            ],
            model="gpt-4o-mini",
        )
        r2 = chat_completion.choices[0].message.content
        print(r2)
        # todo read config, check if parcel fits with config ...
        send_slack(r)
    pass


def scrape_all_pages(start_url):
    current_url = start_url
    while current_url:
        print(f"Scraping page: {current_url}")
        response = requests.get(current_url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
        else:
            print("failed")
            exit(0)
        parcel_links = scrape_page(soup)
        send_to_gpt(parcel_links)
        current_url = get_next_page_url(soup)


def save_visited_links(links):
    with open(cache_file, 'w') as file:
        json.dump(list(links), file)


if __name__ == "__main__":
    # todo create classes form this from file, looks like a massive mess
    load_dotenv()
    api_key = os.getenv('API_KEY')
    org_id = os.getenv('ORG_ID')
    if not api_key or not org_id:
        raise Exception("Missing ORG_ID or API_KEY. Please add .env file")
    # todo more URLs here centered around places we like using filters
    base_url = "https://reality.idnes.cz/s/prodej/pozemky/rajhrad-okres-brno-venkov/"

    cache_file = "visited_links.json"
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            visited_links = set(json.load(f))
    else:
        visited_links = set()

    scrape_all_pages(base_url)
    save_visited_links(visited_links)
