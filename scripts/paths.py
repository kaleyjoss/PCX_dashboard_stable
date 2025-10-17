import os
import pickle
import logging
import pandas as pd

'''
Example of use:
1. Load paths dict 
paths = load_paths()
2. Use the below list of dicts to reference specific paths, ie `surveys_dir = paths["surveys_dir"]`
'''




def find(search_dir, target_folder):
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
            return full_path
        else:
            logging.debug(f'Searching in: {search_dir} — didnt find {target_folder}, found subfolders: {filenames}. If you would like to change what directory to look for this file, change it in /scripts/paths.py')

    return None



def get_cached_path(target, cache_prefix='path_'):
    """Try to load a cached path based on the target's base name."""
    cache_file = f"/paths/{cache_prefix}{target}.pkl"
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            cached_path = pickle.load(f)
            if os.path.exists(cached_path):
                return cached_path
    return None   # Not found or invalid path

def save_cached_path(path, cache_prefix='path_'):
    """Save a path to a uniquely named pickle file based on the target name."""
    base = os.path.basename(os.path.normpath(path))  # e.g., 'PCR927.csv' or 'subject_logs'
    cache_file = f"/paths/{cache_prefix}{base}.pkl"
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

    """

    # Try to load a cached path
    path = get_cached_path(target)
    if path:
        return path

    # Otherwise, search for it
    path = find(search_dir, target)
    if path:
        save_cached_path(path)
        return path


def check_path(path):
    if os.path.exists(path):
        return path
    else:
        logging.warning(f"Missing: {path}. This must have moved. Change the filepath location each item is looking for in /scripts/paths.py")
        return None

def load_paths():
    project_dir = os.path.expanduser('~/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2')
    logging.info(f'Using project_dir {project_dir}')


    pcx_dir = find(os.path.expanduser('~/Library/CloudStorage/Box-Box/(Restricted)_PCR'), 'PCX')
    mindlamp_dir = find(pcx_dir, 'mindlamp_mri_data')
    mri_dir = find(pcx_dir, 'fmriprep_reports')
    data_dir = find(pcx_dir, 'PCX')
    surveys_dir = find(pcx_dir, 'behavioral')
    REPORTS_DIR = find(pcx_dir, 'fmriprep_reports')
    tracker_df = pd.read_csv('/Users/demo/Library/CloudStorage/Box-Box/Holmes_Lab_Wiki/PCX_Round2/Subject_tracker_PCR.csv')
    demographic_df_dir = find(pcx_dir, 'demographic_df')

    logging.info('Using cached paths from /scripts/paths.py. If you move a file, change its location in /scripts/paths.py.')

    return {
        "project_dir": project_dir,
        "pcx_dir": pcx_dir,
        "mri_dir": mri_dir,
        "REPORTS_DIR": REPORTS_DIR,
        "data_dir": data_dir,
        "surveys_dir": surveys_dir,
        "tracker_df": tracker_df,
        "demographic_df_dir": demographic_df_dir,
        "mindlamp_dir": mindlamp_dir
    }
