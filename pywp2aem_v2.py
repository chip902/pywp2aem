import xml.etree.ElementTree as ET
import os
import shutil
import zipfile

def process_post_node(post_node):
    # Extract necessary data from the post node
    post_title = post_node.find('title').text
    post_content = post_node.find('content:encoded', namespaces).text
    post_date = post_node.find('wp:post_date', namespaces).text
    
    # Process the extracted data (replace with your desired logic)
    processed_title = post_title.upper()
    processed_content = post_content.replace('foo', 'bar')
    
    # Return the processed data as a dictionary
    return {
        'title': processed_title,
        'content': processed_content,
        'date': post_date
    }

def process_page_node(page_node):
    # Extract necessary data from the page node
    page_title = page_node.find('title').text
    page_content = page_node.find('content:encoded', namespaces).text
    
    # Process the extracted data (replace with your desired logic)
    processed_title = page_title.upper()
    processed_content = page_content.replace('foo', 'bar')
    
    # Return the processed data as a dictionary
    return {
        'title': processed_title,
        'content': processed_content,
    }

# Define the namespace mappings
namespaces = {'wp': 'http://wordpress.org/export/1.2/'}

# Parse the XML file
tree = ET.parse('wordpress_export.xml')
root = tree.getroot()

# Find all post nodes in the XML file
post_nodes = root.findall(".//wp:item[wp:post_type='post']", namespaces)

# Find all page nodes in the XML file
page_nodes = root.findall(".//wp:item[wp:post_type='page']", namespaces)

# Create a temporary directory to store the processed content
temp_dir = 'temp'
os.makedirs(temp_dir, exist_ok=True)

# Process and store the post content in the temporary directory
for post_node in post_nodes:
    processed_data = process_post_node(post_node)
    post_title = processed_data['title']
    post_content = processed_data['content']
    post_date = processed_data['date']
    
    # Create a directory in the temporary directory for each processed post
    post_dir_name = f"{post_date}-{post_title}"
    post_dir_path = os.path.join(temp_dir, 'jcr_root', 'content', 'my-site', 'posts', post_dir_name)
    os.makedirs(post_dir_path, exist_ok=True)
    
    # Create the .content.xml file for the post
    content_xml_path = os.path.join(post_dir_path, '.content.xml')
    with open(content_xml_path, 'w') as file:
        file.write(f'''
<my-post>
    <title>{post_title}</title>
    <content>{post_content}</content>
</my-post>
''')

# Process and store the page content in the temporary directory
for page_node in page_nodes:
    processed_data = process_page_node(page_node)
    page_title = processed_data['title']
    page_content = processed_data['content']
    
    # Create a directory in the temporary directory for each processed page
    page_dir_name = f"{page_title}"
    page_dir_path = os.path.join(temp_dir, 'jcr_root', 'content', 'my-site', 'pages', page_dir_name)
    os.makedirs(page_dir_path, exist_ok=True)
    
    # Create the .content.xml file for the page
    content_xml_path = os.path.join(page_dir_path, '.content.xml')
    with open(content_xml_path, 'w') as file:
        file.write(f'''
<my-page>
    <title>{page_title}</title>
    <content>{page_content}</content>
</my-page>
''')

# Copy the assets to the temporary directory
assets_dir = os.path.join(temp_dir, 'jcr_root', 'content', 'my-site', 'assets')
os.makedirs(assets_dir, exist_ok=True)

# Assuming the assets are located in a specific directory in the WordPress export file
assets_source_dir = 'wp-content/uploads'
shutil.copytree(assets_source_dir, assets_dir)

# Create the META-INF folder in the temporary directory
meta_inf_dir = os.path.join(temp_dir, 'META-INF')
os.makedirs(meta_inf_dir, exist_ok=True)

# Create the .content.xml file for the root node
root_content_xml_path = os.path.join(temp_dir, 'jcr_root', '.content.xml')
with open(root_content_xml_path, 'w') as file:
    file.write('''
<jcr:root xmlns:sling="http://sling.apache.org/jcr/sling/1.0"
           xmlns:cq="http://www.day.com/jcr/cq/1.0"
           xmlns:jcr="http://www.jcp.org/jcr/1.0"
           xmlns:nt="http://www.jcp.org/jcr/nt/1.0"
           jcr:primaryType="cq:Page"
           jcr:title="My Site"
           sling:resourceType="foundation/components/page"
           cq:lastModified="{CurrentTime}"
           cq:lastModifiedBy="admin"
           cq:distribute="false">
    <jcr:content
        jcr:primaryType="cq:PageContent"
        sling:resourceType="foundation/components/page"
        cq:lastModified="{CurrentTime}"
        cq:lastModifiedBy="admin"
        cq:distribute="false"/>
</jcr:root>
''')

# Create the AEM import package (ZIP)
zip_file_name = 'my-site-package.zip'
with zipfile.ZipFile(zip_file_name, 'w') as package:
    # Add the jcr_root and META-INF directories to the package
    for folder_name in ['jcr_root', 'META-INF']:
        folder_path = os.path.join(temp_dir, folder_name)
        for root_dir, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root_dir, file)
                archive_path = os.path.relpath(file_path, temp_dir)
                package.write(file_path, archive_path)

# Clean up the temporary directory
shutil.rmtree(temp_dir)

print(f"AEM import package '{zip_file_name}' created successfully.")
