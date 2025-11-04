import pyalex
import requests
from pypdf import PdfReader
import io
import os
from dotenv import load_dotenv
import openai

def get_random_open_access_paper():
    """
    Gets a random open access paper from OpenAlex.

    Returns:
        dict: A dictionary representing the paper, or None if an error occurs.
    """
    try:
        # Get a random work that is open access
        random_paper = pyalex.Works().filter(is_oa=True, type='article').sample(1).get()

        if random_paper:
            return random_paper[0]
        else:
            print("Could not retrieve a random paper.")
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
    if paper.get('open_access') and paper['open_access'].get('oa_url'):
        oa_url = paper['open_access']['oa_url']
        if oa_url and oa_url.endswith('.pdf'):
            return oa_url

    # 2. Check the locations for a PDF URL
    if paper.get('locations'):
        for location in paper['locations']:
            if location.get('pdf_url') and isinstance(location['pdf_url'], str) and location['pdf_url'].endswith('.pdf'):
                return location['pdf_url']

    # 3. As a fallback, check if any URL has a PDF content type
    urls_to_check = []
    if paper.get('open_access') and paper['open_access'].get('oa_url'):
        urls_to_check.append(paper['open_access']['oa_url'])
    if paper.get('locations'):
        for location in paper['locations']:
            if location.get('pdf_url') and isinstance(location['pdf_url'], str):
                urls_to_check.append(location['pdf_url'])
            # Also check the landing page url, it might be a pdf
            if location.get('landing_page_url') and isinstance(location['landing_page_url'], str):
                urls_to_check.append(location['landing_page_url'])

    for url in set(urls_to_check): # use set to avoid checking same url multiple times
        if not url:
            continue
        try:
            response = requests.head(url, allow_redirects=True, timeout=5)
            if response.status_code == 200 and 'application/pdf' in response.headers.get('Content-Type', ''):
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

def find_relevant_cited_papers(paper_text):
    """
    Uses OpenAI to find relevant cited papers in the text of a paper.

    Args:
        paper_text (str): The full text of the paper.

    Returns:
        list: A list of titles of relevant cited papers, or None if an error occurs.
    """
    try:
        client = openai.OpenAI()
        prompt = """
        You are a research assistant. I will provide you with the full text of a research paper.
        Your task is to identify the "Related Work" section (or a similar section with a different name, like "Literature Review").
        From this section, please extract the titles of the most relevant cited papers.
        Return a list of the paper titles as a Python list of strings.
        For example: ['Paper Title 1', 'Paper Title 2', 'Paper Title 3']
        """

        # Aggressively clean the string
        cleaned_paper_text = paper_text[:8000].replace('\\', '').replace('\n', ' ')

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": cleaned_paper_text
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"An error occurred while communicating with OpenAI: {e}")
        return None

if __name__ == '__main__':
    load_dotenv()
    openai.api_key = os.getenv("OPENAI_API_KEY")

    found_paper_with_full_text = False
    tries = 10
    for i in range(tries):
        paper = get_random_open_access_paper()
        print(f"Attempting to process paper: {paper.get('title')}")
        print(f"OpenAlex ID: {paper.get('id')}")
        print(f"DOI: {paper.get('doi')}")

        full_text = get_paper_full_text(paper)
        if full_text:
            print("\nSuccessfully extracted full text.\n")
            relevant_papers = find_relevant_cited_papers(full_text)
            if relevant_papers:
                    print(f"Results: {relevant_papers}")
            else:
                print("\nCould not find relevant cited papers.")
            found_paper_with_full_text = True
            break # Break after finding the first paper with full text
        else:
            print(f"Could not extract full text for {paper.get('title')}.")
        print("-" * 50) # Separator for readability

    if not found_paper_with_full_text:
        print("\nCould not find any paper with extractable full text in the sample.")
