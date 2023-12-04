#!/bin/bash

repos=("hashicorp/boundary website/content" "hashicorp/consul docs" "hashicorp/nomad website/content" "hashicorp/packer website/content" "hashicorp/terraform website/docs" "hashicorp/tutorials content/tutorials" "hashicorp/vagrant website/content" "hashicorp/vault website/content")
# hashicorp/tutorials is a private repo with public content
output_dir="output"
mkdir -p "$output_dir"
date=$(date +%Y%m%d)

process_repo() {
    local repo_url=$1
    local folder=$2
    local repo_name=$(basename "$repo_url")
    local local_path="cloned_repos/$repo_name"

    [[ -d $local_path ]] && git -C "$local_path" pull || git clone --depth 1 "https://github.com/$repo_url.git" "$local_path"
    local short_sha=$(git -C "$local_path" rev-parse --short HEAD)
    local output_file="${output_dir}/${repo_name}_${date}_${short_sha}.mdx"

    {
        echo "Generated on: $(date +"%Y-%m-%d %H:%M:%S")"
        echo "Latest Commit SHA: $short_sha"
        echo
        find "$local_path/$folder" -name '*.md' -o -name '*.mdx' | while read -r file; do
            echo "<!-- $file -->"
            cat "$file"
        done
    } > "$output_file"
    echo "Updated $repo_name - Output file: $output_file"
}

for repo in "${repos[@]}"; do
    read -r repo_url folder <<< $(echo $repo | sed 's/ /\n/')
    process_repo "$repo_url" "$folder" &
done

wait
