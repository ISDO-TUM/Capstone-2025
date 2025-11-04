import pyalex
import requests
from pypdf import PdfReader
import io
import os
from dotenv import load_dotenv
import openai
import csv
import re
import random

from fuzzywuzzy import fuzz


def reconstruct_abstract(work):
    """
    Reconstructs the abstract from the 'abstract_inverted_index' field of an OpenAlex work object.
    Args:
        work (dict): An OpenAlex work object.
    Returns:
        str: The reconstructed abstract, or "No abstract available" if not found.
    """
    abstract_idx = work.get("abstract_inverted_index")
    if abstract_idx:
        index_map = {v: k for k, values in abstract_idx.items() for v in values}
        abstract = " ".join(index_map[i] for i in sorted(index_map))
        # Optionally add validation here if needed, similar to paper_handler.py's is_valid_abstract
        return abstract
    return "No abstract available"


def get_random_open_access_paper():
    """
    Gets a random open access paper from OpenAlex, ensuring the full work object is returned.

    Returns:
        dict: A dictionary representing the full paper object, or None if an error occurs.
    """
    try:
        # First, get a random paper sample to get an ID
        random_paper_sample = (
            pyalex.Works()
            .filter(is_oa=True, has_abstract=True, type="article")
            .sample(1)
            .get()
        )

        if random_paper_sample:
            paper_id = random_paper_sample[0]["id"].split("/")[-1]
            # Then, fetch the full work object using the ID to ensure all fields are present
            full_paper_object = pyalex.Works()[paper_id]
            # Reconstruct abstract
            full_paper_object["abstract"] = reconstruct_abstract(full_paper_object)
            return full_paper_object
        else:
            print("Could not retrieve a random paper sample.")
            return None
    except Exception as e:
        print(f"An error occurred while fetching a random paper: {e}")
        return None


def get_pdf_url(paper):
    """
    Finds the best available PDF URL for a paper.

    Args:
        paper (dict): A dictionary representing the paper from OpenAlex.

    Returns:
        str: The PDF URL, or None if not found.
    """
    # 1. Check the main open access URL
    if paper.get("open_access") and paper["open_access"].get("oa_url"):
        oa_url = paper["open_access"]["oa_url"]
        if oa_url and oa_url.endswith(".pdf"):
            return oa_url

    # 2. Check the locations for a PDF URL
    if paper.get("locations"):
        for location in paper["locations"]:
            if (
                location.get("pdf_url")
                and isinstance(location["pdf_url"], str)
                and location["pdf_url"].endswith(".pdf")
            ):
                return location["pdf_url"]

    # 3. As a fallback, check if any URL has a PDF content type
    urls_to_check = []
    if paper.get("open_access") and paper["open_access"].get("oa_url"):
        urls_to_check.append(paper["open_access"]["oa_url"])
    if paper.get("locations"):
        for location in paper["locations"]:
            if location.get("pdf_url") and isinstance(location["pdf_url"], str):
                urls_to_check.append(location["pdf_url"])
            # Also check the landing page url, it might be a pdf
            if location.get("landing_page_url") and isinstance(
                location["landing_page_url"], str
            ):
                urls_to_check.append(location["landing_page_url"])

    for url in set(urls_to_check):  # use set to avoid checking same url multiple times
        if not url:
            continue
        try:
            response = requests.head(url, allow_redirects=True, timeout=5)
            if (
                response.status_code == 200
                and "application/pdf" in response.headers.get("Content-Type", "")
            ):
                return url
        except requests.exceptions.RequestException:
            continue

    return None


def get_paper_full_text(paper):
    """
    Downloads and extracts the full text of a paper.

    Args:
        paper (dict): A dictionary representing the paper from OpenAlex.

    Returns:
        str: The full text of the paper, or None if it cannot be retrieved.
    """
    pdf_url = get_pdf_url(paper)

    if not pdf_url:
        print(f"No suitable PDF URL found for paper {paper.get('id')}")
        return None

    try:
        response = requests.get(pdf_url, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes

        with io.BytesIO(response.content) as pdf_file:
            reader = PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

        return text
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF from {pdf_url}: {e}")
        return None
    except Exception as e:
        print(f"An error occurred while processing the PDF from {pdf_url}: {e}")
        return None


from abc import ABC, abstractmethod


class RelevantPapersFinder(ABC):
    """Interface for finding relevant cited papers."""

    @abstractmethod
    def find_papers(self, paper_text, paper=None):
        """
        Finds relevant cited papers.

        Args:
            paper_text (str): The full text of the paper (used by some implementations).
            paper (dict): The paper object from OpenAlex (used by some implementations).

        Returns:
            list: A list of titles of relevant cited papers.
        """
        pass


class OpenAIPapersFinder(RelevantPapersFinder):
    """Finds relevant papers using the OpenAI API."""

    def find_papers(self, paper_text, paper=None):
        if not paper_text:
            print("OpenAIPapersFinder requires the 'paper_text'.")
            return []
        try:
            client = openai.OpenAI()
            prompt = """
            You are a research assistant. I will provide you with the full text of a research paper.
            Your task is to identify the "Related Work" section (or a similar section with a different name, like "Literature Review").
            From this section, please extract the titles of the most relevant cited papers.
            Return a JSON object with a single key "papers" containing a list of the paper titles as strings.
            For example: {"papers": ["Paper Title 1", "Paper Title 2", "Paper Title 3"]}
            If no papers are found, return an empty list: {"papers": []}
            """

            # Aggressively clean the string
            cleaned_paper_text = paper_text[:8000].replace("\\", "").replace("\n", " ")

            response = client.chat.completions.create(
                model="gpt-5.1",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": cleaned_paper_text},
                ],
            )

            response_content = response.choices[0].message.content
            try:
                import json

                json_response = json.loads(response_content)
                if "papers" in json_response and isinstance(
                    json_response["papers"], list
                ):
                    return json_response["papers"]
                else:
                    print(
                        f"OpenAI response did not contain a valid 'papers' list: {response_content}"
                    )
                    return []
            except json.JSONDecodeError:
                print(f"Failed to decode JSON from OpenAI response: {response_content}")
                return []

        except Exception as e:
            print(f"An error occurred while communicating with OpenAI: {e}")
            return None


class MockPapersFinder(RelevantPapersFinder):
    """Finds relevant papers using mock data for testing."""

    def find_papers(self, paper_text=None, paper=None, num_papers_to_return=3):
        print("Using mock data for relevant cited papers.")
        if not paper:
            print("MockPapersFinder requires the 'paper' object.")
            return []

        referenced_works_ids = paper.get("referenced_works", [])
        if not referenced_works_ids:
            print("Paper has no referenced works to use for mock data.")
            return []

        try:
            suitable_cited_papers = []
            # Iterate through referenced works to find ones with an abstract
            for cited_work_url in referenced_works_ids[:50]:  # Limit to first 50
                work_id = cited_work_url.split("/")[-1]
                cited_work = pyalex.Works()[work_id]
                cited_work["abstract"] = reconstruct_abstract(
                    cited_work
                )  # Reconstruct abstract
                if (
                    cited_work.get("abstract")
                    and cited_work["abstract"] != "No abstract available"
                ):
                    suitable_cited_papers.append(cited_work)

            if not suitable_cited_papers:
                print(
                    "Could not find any referenced work with an abstract in the first 50 references of this paper."
                )
                return []

            # Randomly select a subset of suitable papers
            num_to_select = min(num_papers_to_return, len(suitable_cited_papers))
            selected_papers = random.sample(suitable_cited_papers, num_to_select)

            mock_titles = [p.get("title") for p in selected_papers if p.get("title")]
            if mock_titles:
                print(
                    f"Found {len(mock_titles)} referenced papers with abstracts: {mock_titles}"
                )
                return mock_titles
            else:
                print(
                    "Could not find any referenced work with a title among the selected papers."
                )
                return []

        except Exception as e:
            print(
                f"An error occurred while fetching referenced work details for mock data: {e}"
            )
            return []


def search_papers_in_openalex(paper_titles):
    """
    Searches for papers in OpenAlex by title and retrieves their OpenAlex IDs.

    Args:
        paper_titles (list): A list of paper titles.

    Returns:
        list: A list of dictionaries, each containing the title and OpenAlex ID.
    """
    results = []
    for title in paper_titles:
        try:
            # Search for the paper by title
            works = pyalex.Works().search(title).get()
            if works:
                # Assume the first result is the most relevant
                work = works[0]
                results.append({"title": title, "openalex_id": work.get("id")})
            else:
                results.append({"title": title, "openalex_id": None})
        except Exception as e:
            print(f"An error occurred while searching for '{title}': {e}")
            results.append({"title": title, "openalex_id": None})
    return results


from fuzzywuzzy import fuzz


def find_cited_papers_in_openalex(original_paper_id, paper_titles):
    """
    Searches for papers within the citations of an original paper in OpenAlex.

    Args:
        original_paper_id (str): The OpenAlex ID of the original paper.
        paper_titles (list): A list of paper titles to search for.

    Returns:
        list: A list of dictionaries, each containing the title and OpenAlex ID.
    """
    results = []
    try:
        # Get the citations of the original paper
        original_work = pyalex.Works()[original_paper_id]
        referenced_works_ids = original_work.get("referenced_works", [])

        if not referenced_works_ids:
            print(f"No referenced works found for paper {original_paper_id}")
            return []

        # Fetch details of referenced works in batches
        referenced_works = []
        for i in range(0, len(referenced_works_ids), 50):  # 50 is the max per page
            batch_ids = "|".join(referenced_works_ids[i : i + 50])
            referenced_works.extend(pyalex.Works().filter(openalex_id=batch_ids).get())

        for title_to_find in paper_titles:
            best_match = None
            highest_ratio = 0
            for cited_work in referenced_works:
                cited_title = cited_work.get("title")
                if cited_title:
                    ratio = fuzz.token_set_ratio(title_to_find, cited_title)
                    if ratio > highest_ratio:
                        highest_ratio = ratio
                        best_match = cited_work

            if best_match and highest_ratio > 80:  # Using a threshold of 80
                best_match["abstract"] = reconstruct_abstract(
                    best_match
                )  # Reconstruct abstract
                results.append(
                    {
                        "searched_title": title_to_find,
                        "found_title": best_match.get("title"),
                        "openalex_id": best_match.get("id"),
                        "abstract": best_match.get("abstract"),
                        "match_ratio": highest_ratio,
                    }
                )
            else:
                results.append(
                    {
                        "searched_title": title_to_find,
                        "found_title": None,
                        "openalex_id": None,
                        "match_ratio": 0,
                    }
                )

    except Exception as e:
        print(f"An error occurred: {e}")

    return results


def get_negative_samples(exclude_ids, num_samples=5):
    """
    Gets a number of random open access papers from OpenAlex, excluding a given list of IDs.

    Args:
        exclude_ids (list): A list of OpenAlex IDs to exclude.
        num_samples (int): The number of negative samples to retrieve.

    Returns:
        list: A list of dictionaries representing the paper objects.
    """
    negative_samples = []
    exclude_ids_set = set(exclude_ids)

    # Fetch more than num_samples to account for filtering
    try:
        random_papers = (
            pyalex.Works()
            .filter(is_oa=True, has_abstract=True, type="article")
            .sample(num_samples * 2)
            .get()
        )

        if not random_papers:
            return []

        for paper in random_papers:
            if paper["id"] not in exclude_ids_set:
                paper["abstract"] = reconstruct_abstract(paper)
                negative_samples.append(paper)
                if len(negative_samples) >= num_samples:
                    break
    except Exception as e:
        print(f"An error occurred while fetching negative samples: {e}")

    return negative_samples


def generate_pairs_csv(citing_paper, papers_list, label, filename="paper_pairs.csv"):
    """
    Generates a CSV file with pairs of papers.
    Each row represents a pair where the 'first' paper is related to the 'second' paper.

    Args:
        citing_paper (dict): The main paper (the 'second' paper).
        papers_list (list): A list of dictionaries, each representing a paper to be paired.
        label (int): The label for the pairs (1 for positive, 0 for negative).
        filename (str): The name of the CSV file to write to.
    """
    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "openalexid_first",
            "title_first",
            "abstract_first",
            "openalexid_second",
            "title_second",
            "abstract_second",
            "label",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        citing_openalex_id = citing_paper.get("id")
        citing_title = citing_paper.get("title")
        citing_abstract = citing_paper.get("abstract")

        for paper in papers_list:
            # Handle different structures for positive (cited) and negative (random) papers
            paper_id = (
                paper.get("openalex_id") if "openalex_id" in paper else paper.get("id")
            )
            title = (
                paper.get("found_title")
                if "found_title" in paper
                else paper.get("title")
            )
            abstract = paper.get("abstract")

            if paper_id:
                writer.writerow(
                    {
                        "openalexid_first": paper_id,
                        "title_first": title,
                        "abstract_first": abstract,
                        "openalexid_second": citing_openalex_id,
                        "title_second": citing_title,
                        "abstract_second": citing_abstract,
                        "label": label,
                    }
                )
            else:
                print(f"Skipping paper due to missing ID: {title}")


if __name__ == "__main__":
    # To use the OpenAI implementation, change the line below to:
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")
    finder = OpenAIPapersFinder()

    # finder = MockPapersFinder()

    # Hyperparameter for the target number of pairs
    TARGET_PAIRS_COUNT = 100
    OUTPUT_FILENAME = "paper_pairs.csv"
    total_pairs_generated = 0

    # Ensure we start with a fresh file
    if os.path.exists(OUTPUT_FILENAME):
        os.remove(OUTPUT_FILENAME)
        print(f"Removed existing file: {OUTPUT_FILENAME}")

    print(
        f"Starting dataset generation. Target: {TARGET_PAIRS_COUNT} positive and negative pairs."
    )

    while total_pairs_generated < TARGET_PAIRS_COUNT:
        paper = get_random_open_access_paper()
        if not paper:
            print("Could not get a random paper. Continuing...")
            continue

        print(f"\nAttempting to process paper: {paper.get('title')}")
        print(f"OpenAlex ID: {paper.get('id')}")

        # Ensure the citing paper has an abstract and referenced works
        if (
            paper.get("abstract")
            and paper.get("abstract") != "No abstract available"
            and paper.get("referenced_works")
        ):
            print("Citing paper has abstract and referenced works. Proceeding.")

            paper_text = None
            if isinstance(finder, OpenAIPapersFinder):
                paper_text = get_paper_full_text(paper)
                if not paper_text:
                    print(
                        f"Could not retrieve full text for paper {paper.get('id')}. Skipping."
                    )
                    continue

            relevant_papers = finder.find_papers(paper_text=paper_text, paper=paper)

            if relevant_papers:
                print(
                    f"Found {len(relevant_papers)} relevant paper titles: {relevant_papers}"
                )
                openalex_papers = find_cited_papers_in_openalex(
                    paper.get("id"), relevant_papers
                )

                valid_openalex_papers = [
                    p for p in openalex_papers if p.get("openalex_id")
                ]

                if valid_openalex_papers:
                    num_positive_pairs = len(valid_openalex_papers)

                    exclude_ids = paper.get("referenced_works", [])
                    exclude_ids.extend(
                        [p.get("openalex_id") for p in valid_openalex_papers]
                    )

                    negative_samples = get_negative_samples(
                        exclude_ids=exclude_ids, num_samples=num_positive_pairs
                    )

                    if negative_samples:
                        num_to_generate = min(
                            len(valid_openalex_papers), len(negative_samples)
                        )

                        # Write pairs to CSV, ensuring we don't exceed the target
                        remaining_needed = TARGET_PAIRS_COUNT - total_pairs_generated
                        num_to_generate = min(num_to_generate, remaining_needed)

                        if num_to_generate > 0:
                            generate_pairs_csv(
                                paper,
                                valid_openalex_papers[:num_to_generate],
                                label=1,
                                filename=OUTPUT_FILENAME,
                            )
                            generate_pairs_csv(
                                paper,
                                negative_samples[:num_to_generate],
                                label=0,
                                filename=OUTPUT_FILENAME,
                            )

                            total_pairs_generated += num_to_generate
                            print(
                                f"Generated {num_to_generate} positive and {num_to_generate} negative pairs. Total: {total_pairs_generated}/{TARGET_PAIRS_COUNT}"
                            )
        else:
            print(f"Skipping paper as it lacks a valid abstract or referenced works.")

        print("-" * 50)

    print(
        f"\nFinished dataset generation. Total pairs generated: {total_pairs_generated}"
    )
