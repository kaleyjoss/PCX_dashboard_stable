import os
import pickle
import logging
import pandas as pd

def find(target_folder, search_dir):
    """Walk through the filesystem to find the folder recursively.
    
    Args:
        target_folder (str): The name of the folder to search for.
        search_dir (str): The root directory to start searching from.

    Returns:
        str or None: The full path to the found folder, or None if not found.
    """

    for filenames in os.listdir(search_dir):
        if target_folder in filenames:
            full_path = os.path.join(search_dir, target_folder)
            logging.info(f'✅ Found folder: {full_path}')
            return full_path
        else:
            logging.debug(f'Searching in: {search_dir} — didnt find {target_folder}, found subfolders: {filenames}. If you would like to change what directory to look for this file, change it in /scripts/paths.py')

    return None



def get_cached_path(target, cache_prefix='path_'):
    """Try to load a cached path based on the target's base name."""
    cache_file = f"{cache_prefix}{target}.pkl"
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            cached_path = pickle.load(f)
            if os.path.exists(cached_path):
                return cached_path
    return None   # Not found or invalid path

def save_cached_path(path, cache_prefix='path_'):
    """Save a path to a uniquely named pickle file based on the target name."""
    base = os.path.basename(os.path.normpath(path))  # e.g., 'PCR927.csv' or 'subject_logs'
    cache_file = f"{cache_prefix}{base}.pkl"
    with open(cache_file, 'wb') as f:
        pickle.dump(path, f)
    logging.info(f"Saved path as {cache_prefix}{base}.pkl")



def get_path(target, search_dir, cache_file='path_cache.pkl'):
    """
    Retrieve the full path to a target file by checking a cache or searching the filesystem.

    This function first attempts to load a previously cached path from a pickle file. If the
    cached path exists and is valid, it returns that. If the cache is missing or invalid,
    it searches the given directory one-level-deep for the target file. Once found, the path
    is cached for future use and returned.

    Args:
        target (str): The name of the file to search for (e.g., 'data.csv').
        search_dir (str): The root directory to begin the search.
        isdir (bool, optional): Note whether you're searching for a file or directory
                                Defaults to file
        cache_file (str, optional): Path to the pickle file used to cache the result.
                                    Defaults to 'path_cache.pkl'.

    Returns:
        str: The full file path to the target file.

    Raises:
        FileNotFoundError: If the file is not found in the specified search directory.

    Example:
        >>> path = get_file_path('results.csv', '/Users/myname/Documents')
        ✅ Using cached path: /Users/myname/Documents/ProjectA/results.csv
    """

    # Try to load a cached path
    path = get_cached_path(target)
    if path:
        logging.info(f"Using cached path: {path}")
        return path

    # Otherwise, search for it
    path = find(target, search_dir)
    if path:
        save_cached_path(path)
        return path


project_dir = (os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2'))
logging.info(f'Using projet_dir {project_dir}')
               
rmr_path = get_path('RMR_running.xlsx', os.path.join(project_dir, 'Admin'))
rmr_df = pd.read_excel(rmr_path)
tracker_path = get_path('Subject_tracker_PCR.xlsx', project_dir)
tracker_df = pd.read_excel(tracker_path)
subs_df = tracker_df

pcx_dir = get_path('PCX', os.path.expanduser('~/Library/CloudStorage/Box-Box/(Restricted)_PCR'))
mri_dir = get_path('fmriprep_reports', pcx_dir, isdir=True)
data_dir = get_path('PCX', os.path.expanduser('~/Library/CloudStorage/Box-Box/(Restricted)_PCR'))
surveys_dir = get_path('behavioral',data_dir)


