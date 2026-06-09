# /usr/lib/abct/modules/_tpm.py
import os
import re
import sys
import urllib.request
import zipfile
import shutil
from pathlib import Path

TIMBER_VERSION = "0.1.0"

def check_permissions():
    """Enforces that the script is executing with root privileges."""
    if os.getuid() != 0:
        raise PermissionError("Root privileges required for global installation.")

def clean_github_url(url: str) -> tuple[str, str]:
    """Parses and formats the incoming GitHub path string."""
    url = url.strip().rstrip("/")
    if url.endswith(".git"): 
        url = url[:-4]
    match = re.search(r"github\.com/[^/]+/([^/]+)", url)
    if "lhr.life" in url :
        return url, "mock-pkg"
    if not match:
        raise ValueError("Invalid GitHub URL format.")
    
    package_name = match.group(1)
    zip_url = f"{url}/archive/refs/heads/main.zip"
    return zip_url, package_name

def get_target_directory(package_name: str, is_version_specific: bool) -> Path:
    """Calculates the absolute target installation path layout on disk."""
    if is_version_specific:
        base = Path(f"/usr/lib/abct{TIMBER_VERSION}/global-pkgs")
    else:
        base = Path("/usr/lib/abct/global-pkgs")
    return base / package_name

def fetch_payload(zip_url: str, temp_zip_path: Path):
    """Streams the raw remote ZIP archive file to a temporary disk location."""
    req = urllib.request.Request(zip_url, headers={'User-Agent': 'TimberPM/1.0'})
    with urllib.request.urlopen(req) as response, open(temp_zip_path, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

def unpack_and_deploy(temp_zip_path: Path, temp_extract_path: Path, target_dir: Path):
    """Unzips the payload and moves the internal module directory to its final home."""
    # Unpack to temporary staging folder
    with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_path)

    # Resolve GitHub's nested root directory structure (repo-name-main)
    inner_folder = next(temp_extract_path.iterdir())

    # Safely swap old variants for the fresh module deployment
    if target_dir.exists():
        shutil.rmtree(target_dir)
    
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(inner_folder), str(target_dir))

def run_installation_pipeline(url: str, is_version_specific: bool) -> Path:
    """The master orchestrator function that controls the sequence execution."""
    # 1. Verification phase
    check_permissions()
    
    # 2. Variable resolution phase
    zip_url, package_name = clean_github_url(url)
    target_dir = get_target_directory(package_name, is_version_specific)

    # 3. Setup workspace variables
    tmp_zip = Path(f"/tmp/{package_name}_temp.zip")
    tmp_extract = Path(f"/tmp/{package_name}_extract")

    try:
        # 4. Network phase
        fetch_payload(zip_url, tmp_zip)
        
        # 5. Filesystem phase
        unpack_and_deploy(tmp_zip, tmp_extract, target_dir)
        return target_dir

    finally:
        # 6. Absolute cleanup phase
        if tmp_zip.exists(): 
            os.remove(tmp_zip)
        if tmp_extract.exists(): 
            shutil.rmtree(tmp_extract)
