# src/get_papers_list/main.py

import sys
import argparse
import pandas as pd

# Import the core logic from your 'papers.py' file
from . import papers

def main():
    """
    Main function to parse arguments and run the paper fetching process.
    """
    # 1. Set up the argument parser
    parser = argparse.ArgumentParser(
        description="Fetches PubMed papers and filters for non-academic authors."
    )
    parser.add_argument(
        "query",
        type=str,
        help="The search query for PubMed (e.g., 'cancer therapeutics')."
    )
    parser.add_argument(
        "-f", "--file",
        type=str,
        help="Filename to save the results as a CSV file."
    )
    parser.add_argument(
        "-d", "--debug",
        action="store_true", # This makes --debug a flag
        help="Enable debug mode to print execution steps."
    )

    args = parser.parse_args()

    if args.debug:
        print(f"✅ Starting search with query: '{args.query}'")

    try:
        # 2. Call the core logic functions from papers.py
        pmids = papers.search_pubmed(args.query)
        if not pmids:
            print("No results found for your query.")
            return
        if args.debug:
            print(f"🔍 Found {len(pmids)} paper IDs.")

        xml_data = papers.fetch_paper_details(pmids)
        if not xml_data:
            print("Error: Failed to fetch paper details from PubMed.")
            sys.exit(1)
        if args.debug:
            print("📄 Successfully fetched paper details.")

        results = papers.parse_and_filter_papers(xml_data)
        if not results:
            print("No papers with non-academic authors were found in the results.")
            return
        if args.debug:
            print(f"🏆 Found {len(results)} papers matching the criteria.")

        # 3. Use pandas to create a DataFrame and save to CSV
        df = pd.DataFrame(results)
        
        # Ensure columns are in the correct order as per requirements
        required_columns = [
            "PubmedID", "Title", "Publication Date",
            "Non-academic Author(s)", "Company Affiliation(s)",
            "Corresponding Author Email"
        ]
        df = df[required_columns]

        if args.file:
            # Save to a file
            df.to_csv(args.file, index=False)
            print(f"\n✅ Results successfully saved to {args.file}")
        else:
            # Print to the console (standard output)
            df.to_csv(sys.stdout, index=False)

    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        sys.exit(1)

# This makes the script executable
if __name__ == "__main__":
    main()