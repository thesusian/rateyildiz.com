import json
import requests
from bs4 import BeautifulSoup
import time
import sys
import os


def scrape_professor_info(network_user_id):
    url = f"https://avesis.yildiz.edu.tr/nr/{network_user_id}"
    print(f"Attempting to scrape: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    profile_div = soup.find('div', class_='ol-user-profile')
    if not profile_div:
        print(f"Could not find profile div for user ID: {network_user_id}")
        return None

    name_element = profile_div.find('h1', class_='title')
    name = name_element.get_text().strip() if name_element else None

    image_element = profile_div.find('img')
    image_id = image_element['src'].split('/')[-1] if image_element else None

    corporate_info_element = soup.find('span', class_='corporateInformation')
    if corporate_info_element:
        corporate_info = corporate_info_element.get_text().strip()
        departments = [dept.strip() for dept in corporate_info.split(',')]
    else:
        departments = []

    # Extract username from the primary menu
    primary_menu = soup.find('ul', id='primary-menu')
    username = None
    if primary_menu:
        first_menu_item = primary_menu.find('li')
        if first_menu_item:
            anchor = first_menu_item.find('a')
            if anchor and 'href' in anchor.attrs:
                username = anchor['href'].strip('/')

    print(f"Scraped: {name}")
    return {
        'name': name,
        'image_id': image_id,
        'departments': departments,
        'username': username
    }

def load_existing_data():
    if os.path.exists('professors_info.json'):
        with open('professors_info.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    return []

def save_data(data, filename='professors_info.json'):
    with open(filename, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

def main():
    try:
        with open('professors_raw.json', 'r') as file:
            professors_raw = json.load(file)
    except FileNotFoundError:
        print("Error: 'professors_raw.json' file not found.")
        return
    except json.JSONDecodeError:
        print("Error: 'professors_raw.json' is not a valid JSON file.")
        return

    print(f"Loaded {len(professors_raw)} professors from the input file.")

    professors_info = load_existing_data()
    existing_ids = set(prof['user_id'] for prof in professors_info)

    new_professors_info = []
    for i, professor in enumerate(professors_raw, 1):
        network_user_id = professor.get('NetworkUserId')
        faculty_id = professor.get('FacultyId')

        if not network_user_id:
            print(f"Warning: NetworkUserId not found for professor at index {i-1}")
            continue

        if network_user_id in existing_ids:
            print(f"Skipping professor {i}/{len(professors_raw)} (already processed)")
            continue

        print(f"Processing professor {i}/{len(professors_raw)}")
        professor_data = scrape_professor_info(network_user_id)
        if professor_data:
            professor_data['user_id'] = network_user_id
            professor_data['faculty_id'] = faculty_id
            new_professors_info.append(professor_data)

        if len(new_professors_info) % 10 == 0:
            professors_info.extend(new_professors_info)
            save_data(professors_info)
            print(f"Saved data for {len(new_professors_info)} new professors")
            new_professors_info = []

        time.sleep(1)

    if new_professors_info:
        professors_info.extend(new_professors_info)
        save_data(professors_info)
        print(f"Saved data for the remaining {len(new_professors_info)} new professors")

    print(f"Professor information has been scraped and saved to 'professors_info.json'. Total: {len(professors_info)}")

if __name__ == "__main__":
    main()
