import re
import logging


# This only finds the first instance of a match
def extract(filename, list=False):
    """
    This function takes either a single string or a list of strings and returns the subject ID
    The function looks for "PCXXXX_" with the string(s). XXXX can be any numbers/letters, any length.
    The returned subject ID will be formatted like "sub-PCXXXX"

    Args:
        filename (str or list): Single string or list of strings to search.
        is_list (bool): Set to True if input is a list.
    
    Returns:
        str or None: Extracted subject ID or None if not found.
    """
    sub=None
    sub_id=None
    if list: 
        for file in filename:
            match = re.search(r'PCX-PC[a-zA-Z0-9]+', file)
            if match:
                sub_id = match.group() 
            
            if sub_id is not None:    
                sub = 'sub-' + sub_id
                logging.info(f"✅ Found {sub} in {file}")
                return sub
    else:
        if '$' in filename:
            return None
        else:
            match = re.search(r'PCX-PC[a-zA-Z0-9]+', filename)
            if match:
                sub_id = match.group() 
            else: 
                match = re.search(r'PC[a-zA-Z0-9]+', filename)
                if match:
                    sub_id = match.group()
            if sub_id is not None:
                sub = 'sub-' + sub_id
                logging.info(f" Found {sub} in {filename}")
                return sub
                
    
    logging.warning(f"⚠️ Warning: no subject ID found in {filename}. Type: {type(filename)}")
    return None
