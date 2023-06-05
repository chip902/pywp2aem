import os
import re
import requests
from requests.exceptions import RequestException
import xml.etree.ElementTree as ET

def create_aem_folder(folder_path, aem_base_url, aem_username, aem_password):
    url = aem_base_url + folder_path + "?cmd=mkdir"
    response = requests.get(url, auth=(aem_username, aem_password))
    if response.status_code == 200:
        print("AEM folder already exists:", folder_path)
        return
    data = {
        "jcr:primaryType": "sling:Folder"
    }
    response = requests.post(url, auth=(aem_username, aem_password), json=data)
    if response.status_code == 201:
        print("Successfully created AEM folder:", folder_path)
    else:
        print("Failed to create AEM folder:", folder_path)
        #print("Response:", response.text)

def sanitize_title(title):
    # Replace special characters with an underscore (_)
    sanitized_title = re.sub(r'[^\w\s-]', '_', title)
    # Remove leading/trailing spaces
    sanitized_title = sanitized_title.strip()
    # Replace consecutive spaces with a single space
    sanitized_title = re.sub(r'\s+', ' ', sanitized_title)
    # Replace spaces with hyphens (-)
    sanitized_title = sanitized_title.replace(' ', '-')
    return sanitized_title

def create_aem_page(page_title, aem_folder_path, aem_base_url, aem_username, aem_password):
    folder_url = aem_base_url + aem_folder_path + ".html"
    response = requests.get(folder_url, auth=(aem_username, aem_password))
    if response.status_code == 200:
        print("AEM folder already exists:", aem_folder_path)
        return

    page_url = aem_base_url + aem_folder_path + page_title.replace(' ', '-') + ".html"  # Remove the extra slash
    data = {
        "jcr:primaryType": "cq:Page",
        "jcr:title": page_title,
        "jcr:content": {
            "jcr:primaryType": "cq:PageContent"
        }
    }
    response = requests.post(page_url, auth=(aem_username, aem_password), json=data)  # Use json parameter instead of data
    if response.status_code == 201:
        print("Successfully created AEM page:", page_title)
    else:
        print("Failed to create AEM page:", page_title)
        print("Response:", response.text)
        

def import_dam_content(folder_path, title, content, aem_base_url, aem_username, aem_password):
    url = aem_base_url + folder_path + "/" + title
    response = requests.put(url, auth=(aem_username, aem_password), data=content.encode('utf-8'))
    if response.status_code == 201:
        print("Successfully imported DAM content:", title)
    else:
        print("Failed to import DAM content:", title)
        #print("Response:", response.text)

def import_page_content(folder_path, title, content, aem_base_url, aem_username, aem_password):
    url = aem_base_url + folder_path + "/" + title
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "jcr:primaryType": "cq:Page",
        "jcr:title": title,
        "jcr:content": {
            "jcr:primaryType": "cq:PageContent",
            "jcr:data": content
            # Add more properties as needed
        }
    }
    response = requests.post(url, auth=(aem_username, aem_password), headers=headers, json=data)
    if response.status_code == 201:
        print("Successfully imported page content:", title)
    else:
        print("Failed to import page content:", title)
        #print("Response:", response.text)

def parse_wordpress_export(export_file, aem_base_url, aem_username, aem_password):
    tree = ET.parse(export_file)
    root = tree.getroot()

    nsmap = {
        "excerpt": "http://wordpress.org/export/1.2/excerpt/",
        "content": "http://purl.org/rss/1.0/modules/content/",
        "wfw": "http://wellformedweb.org/CommentAPI/",
        "dc": "http://purl.org/dc/elements/1.1/",
        "wp": "http://wordpress.org/export/1.2/"
    }

    for item in root.findall("channel/item"):
        title_element = item.find("title")
        if title_element is None:
            print("Skipping item without a title element")
            continue

        title = title_element.text or "Untitled"  # Provide a default value if title is None

        content_element = item.find("content:encoded", nsmap)
        if content_element is None:
            print("Skipping item without a content element")
            continue

        content = content_element.text
        if content is None:
            print("Skipping item without content")
            continue

        if "wp-content" in content:
            # Extract the URLs of the images or videos
            urls = extract_media_urls(content)

            # Create a DAM folder to store the media files
            folder_path = "/content/dam/" + export_file.strip('.xml') + "/" + title
            create_aem_folder(folder_path, aem_base_url, aem_username, aem_password)

            # Import each media file into the DAM folder
            for url in urls:
                filename = os.path.basename(url)
                import_dam_content(folder_path, filename, url, aem_base_url, aem_username, aem_password)
        else:
            folder_path = "/content/sky/"  # Update the parent folder path according to your needs
            create_aem_folder(folder_path, aem_base_url, aem_username, aem_password)
            create_aem_page(title, folder_path, aem_base_url, aem_username, aem_password)
            import_page_content(folder_path, title, content, aem_base_url, aem_username, aem_password)


def extract_media_urls(content):
    """
    Extracts the URLs of the media files (images or videos) from the content.
    Assumes that the media files have 'wp-content' in their path.
    """
    urls = []
    start_index = 0

    while True:
        start_index = content.find("wp-content", start_index)
        if start_index == -1:
            break

        end_index = content.find('"', start_index)
        if end_index == -1:
            break

        url = content[start_index:end_index]
        urls.append(url)
        start_index = end_index + 1

    return urls

if __name__ == "__main__":
    wordpress_export_file = "sky.xml"
    aem_base_url = "http://localhost:4502"
    aem_username = "admin"
    aem_password = "admin"

    parse_wordpress_export(wordpress_export_file, aem_base_url, aem_username, aem_password)
