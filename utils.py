# Function to calculate the hash of a file
import hashlib
import pickle
from pathlib import Path


def calculate_hash(file_path: Path):
    hasher = hashlib.sha256()
    with file_path.open('rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
            break
    return hasher.hexdigest()


def load_hashes_from_file(file_path):
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return set()


def save_hashes_to_file(file_path, hashes_set):
    with open(file_path, 'wb') as f:
        pickle.dump(hashes_set, f)

