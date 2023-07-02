import os
import requests
import xml.etree.ElementTree as ET
import zipfile
import re
import shutil
import socket
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# Parse the WordPress XML export file
tree = ET.parse('sky.xml')
root = tree.getroot()

# Namespace map
ns = {'content': 'http://purl.org/rss/1.0/modules/content/'}

# Create directories
os.makedirs('jcr_root', exist_ok=True)
os.makedirs('META-INF/vault', exist_ok=True)

# Function to sanitize filenames
def sanitize_filename(filename):
    if filename is None:
        return None

    # Remove invalid characters
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    
    # Remove leading/trailing whitespace
    filename = filename.strip()
    
    return filename

# Function to download assets
# Function to download assets
def download_asset(url):
    # Parse the URL
    parsed_url = urlparse(url)

    # Check if the URL seems valid
    if not all([parsed_url.scheme, parsed_url.netloc]):
        print(f'Skipping invalid URL: {url}')
        return

    # Check if the host is resolvable
    try:
        socket.gethostbyname(parsed_url.netloc)
    except socket.gaierror:
        print(f'Skipping unresolvable host: {parsed_url.netloc}')
        return

    # Replace http with https
    url = url.replace('http://', 'https://')

    # Download the asset
    try:
        response = requests.get(url, timeout=5)
        # Save the asset
        filename = os.path.join('jcr_root', sanitize_filename(os.path.basename(url)))
        with open(filename, 'wb') as f:
            f.write(response.content)
    except requests.exceptions.RequestException as e:
        print(f'Error downloading {url}: {e}')

## Process the posts and pages
for item in root.findall('.//item'):
    # Get the post type
    post_type = item.find('{http://wordpress.org/export/1.2/}post_type').text

    # Only process posts and pages
    if post_type not in ['post', 'page']:
        continue

    # Get the post content
    content_element = item.find('content:encoded', ns)
    if content_element is not None:
        content = content_element.text

        # Write the content to a file
        if content is not None:
            filename = sanitize_filename(item.find("title").text)
            if filename is not None:
                with open(f'jcr_root/{filename}.html', 'w') as f:
                    f.write(content)

                # Parse the HTML content
                soup = BeautifulSoup(content, 'html.parser')

                # Extract and download images
                for img in soup.find_all('img'):
                    url = img.get('src')
                    if url:
                        download_asset(url)

                # Extract and download videos
                for video in soup.find_all('video'):
                    for source in video.find_all('source'):
                        url = source.get('src')
                        if url:
                            download_asset(url)

                # Extract and download PDFs
                for a in soup.find_all('a'):
                    url = a.get('href')
                    if url and url.lower().endswith('.pdf'):
                        download_asset(url)

# Write the filter.xml file
with open('META-INF/vault/filter.xml', 'w') as f:
    f.write('<workspaceFilter version="1.0">\n')
    f.write('  <filter root="/jcr_root"/>\n')
    f.write('</workspaceFilter>\n')

# Create a zip file
with zipfile.ZipFile('wordpress_to_aem.zip', 'w') as zipf:
    # Add the jcr_root directory
    for foldername, subfolders, filenames in os.walk('jcr_root'):
        for filename in filenames:
            zipf.write(os.path.join(foldername, filename), 
                       os.path.relpath(os.path.join(foldername,filename), '.'))

    # Add the META-INF directory
    for foldername, subfolders, filenames in os.walk('META-INF'):
        for filename in filenames:
            zipf.write(os.path.join(foldername, filename), 
                       os.path.relpath(os.path.join(foldername,filename), '.'))

# Cleanup: remove the temporary directories
shutil.rmtree('jcr_root')
shutil.rmtree('META-INF')