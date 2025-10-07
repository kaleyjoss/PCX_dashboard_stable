import os
import pickle
import logging
import re
def find_file(target_file, search_dir, regex=False):
    """Walk through the filesystem to find the folder recursively.
    
    Args:
        target_folder (str): The name of the folder to search for.
        search_dir (str): The root directory to start searching from.

    Returns:
        str or None: The full path to the found folder, or None if not found.
    """

    # Makes sure search_dir is an absolute path. If it's relative, adds the current directory
    if not os.path.isabs(search_dir):
        search_dir = os.path.abspath(os.path.join(os.getcwd(), search_dir))    
    #logging.info(f'Looking in {search_dir} for "{target_file}"')

    for root, dirnames, files in os.walk(search_dir):
        if regex==True:
            for file in files:
                match = re.search(target_file, file)
            if match:
                target_file = match.group(0) #full string match, even if searching for multiple variable patterns within string
                full_path = os.path.join(root, target_file)
                logging.info(f'✅ Found file: {os.path.basename(full_path)}')
                return full_path

        elif target_file in files:
            full_path = os.path.join(root, target_file)
            logging.info(f'✅ Found file: {os.path.basename(full_path)}')
            return full_path
        #else:
            #logging.debug(f'Searching in: {root} — Files: {files}')

    return None



def find_folder(target_folder, search_dir):
    """Walk through the filesystem to find the folder recursively.
    
    Args:
        target_folder (str): The name of the folder to search for.
        search_dir (str): The root directory to start searching from.

    Returns:
        str or None: The full path to the found folder, or None if not found.
    """
    #logging.info(f'Looking in {search_dir} for folder "{target_folder}"')

    for root, dirnames, _ in os.walk(search_dir):
        if target_folder in dirnames:
            full_path = os.path.join(root, target_folder)
            logging.info(f'✅ Found folder: {full_path}')
            return full_path
        else:
            logging.debug(f'Searching in: {root} — Subfolders: {dirnames}')

    logging.warning(f'❌💗💗 Folder "{target_folder}" not found in "{search_dir}"')
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



def get_path(target, search_dir, isdir=False, cache_file='path_cache.pkl'):
    """
    Retrieve the full path to a target file by checking a cache or searching the filesystem.

    This function first attempts to load a previously cached path from a pickle file. If the
    cached path exists and is valid, it returns that. If the cache is missing or invalid,
    it searches the given directory recursively for the target file. Once found, the path
    is cached for future use and returned.

    Args:
        target (str): The name of the file to search for (e.g., 'data.csv').
        search_dir (str): The root directory to begin the recursive search.
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
    #logging.info("🔍 Searching for target...")
    if isdir:
        path = find_folder(target, search_dir)
    if not isdir:
        path = find_file(target, search_dir)
    if path:
        logging.info(f"✅ Found target: {path}")
        save_cached_path(path)
        return path
    else:
        logging.error(f"❌💗💗 Could not find {target} in {search_dir}")
        raise FileNotFoundError(f"❌💗💗 Could not find {target} in {search_dir}")
