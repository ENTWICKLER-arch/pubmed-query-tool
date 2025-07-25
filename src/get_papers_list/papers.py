# src/get_papers_list/papers.py

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

# Heuristics to identify non-academic authors [cite: 56]
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
    # This is a basic heuristic as per the instructions [cite: 56]
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
    response = requests.get(base_url, params=params)
    response.raise_for_status() # Raise an exception for HTTP errors
    data = response.json()
    return data.get("esearchresult", {}).get("idlist", [])

def fetch_paper_details(pmids: List[str]) -> str:
    """Fetches full paper details from PubMed for a list of PMIDs."""
    if not pmids:
        return ""
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml"
    }
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    return response.text

def parse_and_filter_papers(xml_data: str) -> List[Dict[str, Any]]:
    """Parses XML data and filters for papers with non-academic authors."""
    root = ET.fromstring(xml_data)
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
                pub_date = f"{year}-{month}-{day}"

                # The corresponding author email is often part of an affiliation
                # This heuristic just grabs the first affiliation that looks like an email
                corr_author_email = "N/A"
                for aff in company_affiliations:
                    if '@' in aff:
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
            # Skip this article if there's a parsing error
            print(f"Warning: Could not parse an article. Error: {e}", file=sys.stderr)
            continue
            
    return filtered_papers