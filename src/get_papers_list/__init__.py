from typing import List

def fetch_papers() -> List[str]:
    # Simulated API call
    return [
        "Efficient Transformer Models by Google",
        "Understanding GANs in 2023",
        "Introduction to LLMs - OpenAI",
        "Basic NLP Techniques by University XYZ",
        "Quantum AI Basics"
    ]

def filter_papers(papers: List[str]) -> List[str]:
    # Filter out non-academic sources (heuristics)
    academic_keywords = ["University", "Institute", "Research", "OpenAI", "Google"]
    return [paper for paper in papers if any(k in paper for k in academic_keywords)]
