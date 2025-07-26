import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import json
import sys

# Heuristics to identify non-academic authors
COMPANY_KEYWORDS = [
    'inc', 'ltd', 'llc', 'corp', 'corporation', 'pharmaceuticals',
    'therapeutics', 'diagnostics', 'biotech', 'ventures', 'gmbh', 'pharma'
]
ACADEMIC_KEYWORDS = [
    'university', 'college', 'school', 'hospital', 'institute',
    'center', 'foundation', 'research', 'academy', 'medical center', 'univerzita'
]

def is_non_academic(affiliation: str) -> bool:
    """Applies heuristics to determine if an affiliation is non-academic."""
    if not affiliation:
        return False
    lower_affiliation = affiliation.lower()
    
    # If it contains a company keyword, it's likely non-academic
    if any(keyword in lower_affiliation for keyword in COMPANY_KEYWORDS):
        return True
    
    # If it contains an academic keyword, it's likely academic
    if any(keyword in lower_affiliation for keyword in ACADEMIC_KEYWORDS):
        return False
    
    # As a fallback, assume it's non-academic if it doesn't match academic keywords
    # This is a basic heuristic as per the instructions
    return True

def search_pubmed(query: str, max_results: int = 100) -> List[str]:
    """Searches PubMed and returns a list of matching PubMed IDs (PMIDs)."""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": str(max_results),
        "retmode": "json"
    }
    
    # Debugging print statement
    print(f"DEBUG: Making PubMed ESearch request to: {base_url} with params: {params}") 
    
    try:
        response = requests.get(base_url, params=params, timeout=10) # Added timeout
        response.raise_for_status() # Raise an exception for HTTP errors (e.g., 4xx or 5xx)

        # Debugging print statements for response inspection
        print(f"DEBUG: ESearch HTTP Status Code: {response.status_code}")
        print(f"DEBUG: ESearch Response Headers: {response.headers}")
        print(f"DEBUG: ESearch Raw Response Text (first 500 chars): {response.text[:500]}...")

        # Check if the response text is empty or not valid JSON
        if not response.text.strip():
            print("ERROR: ESearch response text is empty! This might be a temporary API issue or rate limit.", file=sys.stderr)
            return []

        try:
            data = response.json()
            # Debugging print for parsed JSON (first 200 chars for brevity)
            print(f"DEBUG: ESearch Parsed JSON data (first 200 chars): {json.dumps(data, indent=2)[:200]}...") 
        except json.JSONDecodeError as e:
            # Modified error message to be more direct about the likely cause
            print(f"ERROR: Failed to decode JSON from ESearch response: {e}. The API likely returned non-JSON data (e.g., HTML error page). Please check your internet connection and try again after a few minutes, as you might be hitting a rate limit.", file=sys.stderr)
            print(f"ERROR: Full ESearch Response Text: {response.text}", file=sys.stderr)
            return []

        return data.get("esearchresult", {}).get("idlist", [])
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network or API request error in search_pubmed: {e}. Please check your internet connection.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"ERROR: An unexpected error occurred in search_pubmed: {e}", file=sys.stderr)
        return []

def fetch_paper_details(pmids: List[str]) -> str:
    """Fetches full paper details from PubMed for a list of PMIDs."""
    if not pmids:
        print("DEBUG: No PMIDs provided to fetch_paper_details. Returning empty string.") # Debug
        return ""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    print(f"DEBUG: Making PubMed EFetch request for {len(pmids)} PMIDs.") # Debug
    try:
        response = requests.get(base_url, params=params, timeout=10) # Added timeout
        response.raise_for_status()
        print(f"DEBUG: EFetch HTTP Status Code: {response.status_code}") # Debug
        print(f"DEBUG: EFetch Raw Response Text (first 500 chars): {response.text[:500]}...") # Debug
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network or API request error in fetch_paper_details: {e}. Please check your internet connection.", file=sys.stderr)
        return ""
    except Exception as e:
        print(f"ERROR: An unexpected error occurred in fetch_paper_details: {e}", file=sys.stderr)
        return ""

def parse_and_filter_papers(xml_data: str) -> List[Dict[str, Any]]:
    """Parses XML data and filters for papers with non-academic authors."""
    if not xml_data:
        print("DEBUG: No XML data provided to parse_and_filter_papers. Returning empty list.") # Debug
        return []
        
    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        print(f"ERROR: Failed to parse XML data: {e}. The fetched data might not be valid XML. Full XML data (first 500 chars): {xml_data[:500]}...", file=sys.stderr)
        return []

    filtered_papers = []

    for article in root.findall('.//PubmedArticle'):
        try:
            non_academic_authors = []
            company_affiliations = set()

            author_list = article.findall('.//AuthorList/Author')
            for author in author_list:
                affiliation_info = author.find('.//AffiliationInfo/Affiliation')
                if affiliation_info is not None and affiliation_info.text:
                    if is_non_academic(affiliation_info.text):
                        last_name_node = author.find('.//LastName')
                        initials_node = author.find('.//Initials')
                        
                        author_name = "N/A"
                        if last_name_node is not None and initials_node is not None:
                             author_name = f"{initials_node.text} {last_name_node.text}"
                        elif last_name_node is not None: # Case where only last name is available
                            author_name = last_name_node.text
                        
                        non_academic_authors.append(author_name)
                        company_affiliations.add(affiliation_info.text)

            # If we found at least one non-academic author, process the paper
            if non_academic_authors:
                pmid_node = article.find('.//PMID')
                pmid = pmid_node.text if pmid_node is not None else "N/A"

                title_node = article.find('.//ArticleTitle')
                title = title_node.text if title_node is not None else "No Title"

                pub_date_node = article.find('.//PubDate')
                year = pub_date_node.findtext('Year', "N/A")
                month = pub_date_node.findtext('Month', "N/A")
                day = pub_date_node.findtext('Day', "N/A")
                pub_date = f"{year}-{month}-{day}" if year != "N/A" else "N/A" # Format date if year exists

                # The corresponding author email is often part of an affiliation
                # This heuristic just grabs the first affiliation that looks like an email
                corr_author_email = "N/A"
                for aff in company_affiliations:
                    if '@' in aff and len(aff) > 5: # Basic check for email-like string and reasonable length
                        # Simple extraction, could be more sophisticated
                        corr_author_email = aff
                        break
                
                filtered_papers.append({
                    "PubmedID": pmid,
                    "Title": title,
                    "Publication Date": pub_date,
                    "Non-academic Author(s)": ", ".join(non_academic_authors),
                    "Company Affiliation(s)": ", ".join(list(company_affiliations)),
                    "Corresponding Author Email": corr_author_email
                })
        except Exception as e:
            # Skip this article if there's a parsing error in an individual article
            pmid_in_error = "Unknown"
            pmid_node_temp = article.find('.//PMID')
            if pmid_node_temp is not None:
                pmid_in_error = pmid_node_temp.text
            print(f"Warning: Could not parse details for article PMID {pmid_in_error}. Error: {e}. This article will be skipped.", file=sys.stderr)
            continue
            
    return filtered_papers
       

               
