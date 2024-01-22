import requests
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()
europeanaapikey = os.getenv('EUROPEANAAPIKEY')
contentfulkey = os.getenv("CONTENTFULAPIKEY")

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

def get_id_values(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        json_data = response.json()

        id_values = list(find_values_by_key(json_data, "id"))

        return id_values

    except requests.exceptions.RequestException as e:
        print(f"Error fetching API URL: {e}")
        return []

def get_url_values(api_url):
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        json_data = response.json()

        url_values = list(find_values_by_key(json_data, "url"))

        return url_values

    except requests.exceptions.RequestException as e:
        print(f"Error fetching API URL: {e}")
        return []

def get_europeana_info(api_url):
    try:
        parsed_url = urlparse(api_url)
        path_segments = parsed_url.path.split("/")
        collection_id, record_id = path_segments[-2], path_segments[-1]

        europeana_api_url = f"https://api.europeana.eu/record/v2/{collection_id}/{record_id}.json?profile=minimal&wskey="+europeanaapikey
        response = requests.get(europeana_api_url)
        response.raise_for_status()
        json_data = response.json()

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
            print(f"No 'en' key found in 'prefLabel' for {org_id}")
            return pref_label
        else:
            print(f"No 'prefLabel' found for {org_id}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Organization API URL: {e}")
        return None

if __name__ == "__main__":
    input_api_id = input("Enter the Contentful blog ID: ")
    input_api_url = f"https://preview.contentful.com/spaces/i01duvb6kq77/environments/master/entries/{input_api_id}?access_token={contentfulkey}"

    id_values = get_id_values(input_api_url)
    europeana_urls = []
    europeana_providers = []
    organization_names = []

    if id_values:
        for id_value in id_values:
            replacement_url = f"https://preview.contentful.com/spaces/i01duvb6kq77/environments/master/entries/{id_value}?access_token={contentfulkey}"
            
            url_values = get_url_values(replacement_url)
            
            if url_values:
                for url_value in url_values:
                    if '/item/' in url_value:
                        europeana_urls.append(url_value)
                        print(f"URL value with 'europeana.eu' for id={id_value}: {url_value}")

    if europeana_urls:
        print("\nFetching Europeana information:")
        for eu_url in europeana_urls:
            provider_info = get_europeana_info(eu_url)
            if provider_info:
                europeana_providers.append(provider_info)
                print(f"Europeana Data Provider for {eu_url}: {provider_info}")
            else:
                print(f"No Data Provider found for {eu_url}")

    if europeana_providers:
        print("\nFetching Organization names:")
        for provider_url in europeana_providers:
            organization_name = get_organization_name(provider_url)
            if organization_name:
                organization_names.append(organization_name)
                print(f"Organization name for {provider_url}: {organization_name}")
            else:
                print(f"No Organization name found for {provider_url}")

    if organization_names:
        print("\nOrganization Names:")
        for org_name in organization_names:
            print(org_name)
    else:
        print("No Organization Names found.")
