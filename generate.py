import os
import subprocess
import hashlib
import shutil
import concurrent.futures
from datetime import datetime

# List of repositories and their corresponding documentation folders
repos_and_folders = [
    {"repo_url": "https://github.com/hashicorp/boundary.git", "docs_folder": "website/content"},
    {"repo_url": "https://github.com/hashicorp/consul.git", "docs_folder": "docs"},
    {"repo_url": "https://github.com/hashicorp/nomad.git", "docs_folder": "website/content"},
    {"repo_url": "https://github.com/hashicorp/packer.git", "docs_folder": "website/content"},
    {"repo_url": "https://github.com/hashicorp/terraform.git", "docs_folder": "website/docs"},
    {"repo_url": "https://github.com/hashicorp/tutorials.git", "docs_folder": "content/tutorials"}, // private repo, public content
    {"repo_url": "https://github.com/hashicorp/vagrant.git", "docs_folder": "website/content"},
    {"repo_url": "https://github.com/hashicorp/vault.git", "docs_folder": "website/content"},
]

# Output directory for the generated documentation files
output_directory = "output"

# Function to calculate the MD5 checksum of a string
def calculate_md5_checksum(content):
    md5 = hashlib.md5()
    md5.update(content.encode("utf-8"))
    return md5.hexdigest()

# Function to clone or pull a Git repository
def clone_or_pull_repo(repo_info):
    repo_url = repo_info["repo_url"]
    local_repo_path = "cloned_repos/" + repo_url.split("/")[-1].split(".git")[0]
    docs_folder = repo_info["docs_folder"]
    full_docs_path = os.path.join(local_repo_path, docs_folder)

    try:
        if os.path.exists(local_repo_path):
            # Optionally, reset local changes here
            subprocess.run(["git", "pull"], cwd=local_repo_path, check=True)
        else:
            os.makedirs(local_repo_path, exist_ok=True)
            subprocess.run(["git", "clone", "--depth", "1", repo_url, local_repo_path], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Git operation failed for {repo_url}: {e}")
        return None  # or handle differently
        
    # Get the latest commit SHA
    try:
        completed_process = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=local_repo_path,
            check=True,
            stdout=subprocess.PIPE,
            text=True
        )
        short_commit_sha = completed_process.stdout.strip()[:7]
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to get latest commit SHA for {repo_url}: {e}")
        short_commit_sha = "unknown"

    return full_docs_path, short_commit_sha

# Function to process a single repository
def process_repository(repo_info):
    clone_or_pull_repo(repo_info)
    # Rest of the script to concatenate and update documentation files...

# Use concurrent.futures to process repositories in parallel
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = [executor.submit(process_repository, repo_info) for repo_info in repos_and_folders]
    concurrent.futures.wait(futures)

# Function to concatenate Markdown and MDX files in a folder
def concatenate_docs(docs_folder):
    concatenated_content = ""
    for root, _, files in os.walk(docs_folder):
        for file in files:
            if file.endswith(".md") or file.endswith(".mdx"):
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    concatenated_content += f"\n<!-- {file_path} -->\n{content}"
    return concatenated_content

# Ensure the output directory exists or create it
os.makedirs(output_directory, exist_ok=True)

# Loop through the list of repositories and concatenate their documentation
for repo_info in repos_and_folders:
    repo_url = repo_info["repo_url"]
    docs_folder = repo_info["docs_folder"]

    # Clone or pull the repository
    full_docs_path, short_commit_sha = clone_or_pull_repo(repo_info)
    if not full_docs_path:
        continue

    # Concatenate the documentation in the folder
    concatenated_content = concatenate_docs(full_docs_path)

    # Generate a unique output filename based on the repository name
    repo_name = repo_url.split("/")[-1].split(".git")[0]
    output_filename = os.path.join(output_directory, f"{repo_name}.mdx")

    # Generate a unique output filename based on the repository name, date, and SHA
    current_date = datetime.now().strftime("%Y%m%d")
    repo_name = repo_url.split("/")[-1].split(".git")[0]
    output_filename = os.path.join(output_directory, f"{repo_name}_{current_date}_{short_commit_sha}.mdx")

    # Calculate the MD5 checksum of the concatenated content
    content_checksum = calculate_md5_checksum(concatenated_content)

    # Check if the MD5 checksum matches a previous version of the file
    if os.path.exists(output_filename):
        with open(output_filename, "r", encoding="utf-8") as existing_file:
            existing_content = existing_file.read()
            existing_checksum = calculate_md5_checksum(existing_content)
        if content_checksum == existing_checksum:
            print(f"Skipping {repo_name} - No changes detected.")
            continue

    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Write the concatenated content along with the commit SHA and timestamp
    with open(output_filename, "w", encoding="utf-8") as output:
        output.write(f"Generated on: {timestamp}\nLatest Commit SHA: {short_commit_sha}\n\n")
        output.write(concatenated_content)

    print(f"Updated {repo_name} - MD5 checksum: {content_checksum}")
