from .config import ZLIBRARY_BASE_URL

def create_filtered_search_url(website, book_name= None, language="english", file_types=["MOBI", "EPUB"], year = 0):
    # Use config parameter if website is not provided
    if website is None:
        website = ZLIBRARY_BASE_URL

    if book_name:
        # Replace spaces with %20 for URL encoding
        encoded_name = book_name.replace(' ', '%20')  
        # Build the base URL
        base_url = f"{website}/s/{encoded_name}/"
    else:
        base_url = f"{website}/s/"
    
    if(language):
        # Add language parameter
        url_params = [f"languages%5B0%5D={language}"]
    
    if(file_types is not None and len(file_types) != 0):
        # Add file type parameters
        for i, file_type in enumerate(file_types):
            url_params.append(f"extensions%5B{i}%5D={file_type}")
    
    if(year > 0): 
        #Add the year parameter if it exists in the config
        url_params.append(f"yearFrom={year}&yearTo={year}")

    url_params.append("order=bestmatch")

    # Combine all parameters
    return base_url + "?" + "&".join(url_params)
