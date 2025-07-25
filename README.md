# PubMed Non-Academic Paper Extractor

This is a Python command-line tool that extracts non-academic scientific papers from PubMed based on a given search query. It is specifically designed to identify papers written by authors not affiliated with academic institutions such as universities or colleges.

## Features

- Accepts a query as a command-line argument
- Filters affiliations to include only non-academic ones (e.g., "Inc", "Ltd", "LLC", "Pharma") and exclude academic ones (e.g., "University", "Institute", "College")
- Saves the results in a CSV file or prints them to the console
- Provides options for:
  - -h or --help: Show usage instructions
  - -d or --debug: Enable debug mode for detailed logs
  - -f or --file: Specify the output CSV filename

## How to Use

Run the script using the following format:

python -m get_papers_list.main "your search term" [-f filename.csv] [--debug]

## Example:

python -m get_papers_list.main "cancer immunotherapy" -f results.csv --debug

## Output

The CSV or console output will include:

- PubMed ID
- Paper Title
- Publication Date
- Non-Academic Author(s)
- Affiliation(s)
- Corresponding Email (if available)

## Tech Stack

- Python 3.8+
- Modules: requests, argparse, csv, xml.etree.ElementTree
- Uses NCBI PubMed API

## File Structure

- main.py: Entry point of the command-line program
- papers.py: Contains logic to fetch, parse, and filter paper data

## Requirements

- Python 3.8 or higher
- Internet connection to fetch data from PubMed
- Dependencies :
  - pandas
  - requests