import requests
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

load_dotenv()
europeanaapikey = os.getenv('EUROPEANAAPIKEY')

def get_europeana_info(api_url):
    try:
        parsed_url = urlparse(api_url)
        path_segments = parsed_url.path.split("/")
        collection_id, record_id = path_segments[-2], path_segments[-1]
        europeana_api_url = f"https://api.europeana.eu/record/v2/{collection_id}/{record_id}.json?profile=minimal&wskey={europeanaapikey}"
        response = requests.get(europeana_api_url)
        response.raise_for_status()

        try:
            json_data = response.json()
        except ValueError as ve:
            print(f"Invalid JSON in Europeana API response: {ve}")
            print(f"Response content: {response.content}")
            return None

        edm_data_provider = list(find_values_by_key(json_data, "edmDataProvider"))
        def_value = None

        if edm_data_provider:
            def_value = list(find_values_by_key(edm_data_provider[0], "def"))

        return def_value[0] if def_value else None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Europeana API URL: {e}")
        return None


def get_organization_name(api_url):
    try:
        if isinstance(api_url, list):
            api_url = api_url[0]  # Assuming you are interested in the first URL if it's a list

        org_id = urlparse(api_url).path.split("/")[-1]
        
        organization_api_url = f"https://api.europeana.eu/entity/organization/base/{org_id}.json"
        response = requests.get(organization_api_url)
        response.raise_for_status()
        json_data = response.json()

        pref_label_values = list(find_values_by_key(json_data, "prefLabel"))

        if pref_label_values:
            pref_label = pref_label_values[0]
            if isinstance(pref_label, dict) and "en" in pref_label:
                en_value = pref_label["en"]
                return en_value
            #print(f"No 'en' key found in 'prefLabel' for {org_id}")
            firstpreflabel = next(iter((pref_label.items())))
            return firstpreflabel[1]
        else:
            print(f"No 'prefLabel' found for {org_id}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Organization API URL: {e}")
        return None

def find_values_by_key(data, key):
    if isinstance(data, list):
        for item in data:
            for result in find_values_by_key(item, key):
                yield result
    elif isinstance(data, dict):
        for k, v in data.items():
            if k == key:
                yield v
            elif isinstance(v, (dict, list)):
                for result in find_values_by_key(v, key):
                    yield result

def retrieve_gallery_info(gallery_id):
    try:
        user_sets_url = f"https://api.europeana.eu/set/{gallery_id}?wskey={europeanaapikey}"
        response = requests.get(user_sets_url)
        response.raise_for_status()
        json_data = response.json()

        first_url = json_data.get("first")
        last_url = json_data.get("last")

        return first_url, last_url

    except requests.exceptions.RequestException as e:
        print(f"Error fetching User Sets API URL: {e}")
        return None, None

def retrieve_items(api_url):
    items = []

    while api_url:
        try:
            response = requests.get(api_url)
            response.raise_for_status()
            json_data = response.json()

            items.extend(json_data.get("items", []))

            api_url = json_data.get("next")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching items from API URL: {e}")
            break

    return items

if __name__ == "__main__":
    gallery_id = input("Enter the gallery ID: ")

    first_url, last_url = retrieve_gallery_info(gallery_id)

    if first_url and last_url:
        current_url = f"{first_url}&wskey={europeanaapikey}"
        items = retrieve_items(current_url)

        for item in items:
            provider_url = get_europeana_info(item)
            organization_name = get_organization_name(provider_url)
            #print(f"Organization name for {item}: {organization_name}")
            print(organization_name)

    else:
        print("Failed to retrieve gallery information.")
