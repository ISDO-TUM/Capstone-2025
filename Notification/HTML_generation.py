from datetime import datetime
from typing import List, Dict


def load_template(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def format_paper_html(paper: dict) -> str:
    tags_html = "".join(
        f'<span style="background:#eef2ff; color:#1e3a8a; font-size:12px; padding:4px 10px; border-radius:999px; margin:2px; display:inline-block;">{tag}</span>'
        for tag in paper.get("tags", [])
    )
    authors = ", ".join(paper.get("authors", []))
    journal = paper.get("published_in", "Unbekanntes Journal")
    category = paper.get("category", "Allgemein")
    link = paper.get("link", "#")

    return f"""
    <tr>
      <td style="padding:24px 30px; border-bottom:1px solid #e9ecef;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="font-size:13px; color:#6c757d; text-align:right;">{paper['date']}</td>
          </tr>
          <tr>
            <td style="font-size:13px; color:#1e3a8a; font-weight:bold; padding-top:4px;">{category}</td>
          </tr>
          <tr>
            <td style="font-size:18px; font-weight:600; color:#212529; padding:6px 0;">{paper['title']}</td>
          </tr>
          <tr>
            <td style="font-size:14px; color:#495057; line-height:1.5; padding-bottom:10px;">{paper['summary']}</td>
          </tr>
          <tr>
            <td style="font-size:13px; color:#6c757d;">
              <strong>Autoren:</strong> {authors}<br/>
              <strong>Veröffentlicht in:</strong> {journal}
            </td>
          </tr>
          <tr>
            <td style="padding:10px 0 6px;">{tags_html}</td>
          </tr>
          <tr>
            <td>
              <a href="{link}" target="_blank" style="display:inline-block; margin-top:10px; padding:10px 18px; background-color:#007bff; color:#ffffff; text-decoration:none; font-size:13px; border-radius:6px;">
                Paper lesen
              </a>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    """


def generate_newsletter_html(papers: List[Dict]) -> str:
    """

    Render the newsletter and save it to *output.html*.

    Workflow
    --------
    1. Load **Test.html** – the HTML template that contains the
       placeholders ``{{date}}`` and ``{{papers}}``.
    2. Turn every paper dictionary in *papers* into an HTML snippet with
       :pyfunc:`format_paper_html`, then concatenate the snippets.
    3. Substitute
       - ``{{date}}``  → today’s date in “DD. Month YYYY” format
       - ``{{papers}}`` → the concatenated paper snippets
    4. Write the final HTML to **output.html** (UTF-8).
    5. Return the rendered HTML as a string so callers can send, preview,
       or further process it.

    Parameters
    ----------
    papers : list[dict]
        Paper records in whatever structure `format_paper_html` expects
        (e.g. *title*, *authors*, *abstract*, *url*, …).

    Returns
    -------
    str
        The fully rendered HTML newsletter.
    """

    template_path = "Test.html"
    template = load_template(template_path)
    papers_html = "".join(format_paper_html(p) for p in papers)
    today_str = datetime.today().strftime("%d. %B %Y")

    result = template.replace("{{date}}", today_str)
    result = result.replace("{{papers}}", papers_html)
    with open("output.html", "w", encoding="utf-8") as f:
        f.write(result)

    return result


if __name__ == '__main__':
    paper1 = {
        "title": "Distributed Event Streaming in Modern Microservices Architecture",
        "summary": "This paper explores distributed event streaming in microservice architectures.",
        "date": "28.5.2024",
        "authors": ["Dr. Sarah Chen", "Prof. Michael Rodriguez", "Dr. Aisha Patel"],
        "published_in": "Journal of Distributed Computing",
        "tags": ["microservices", "event streaming", "scalability"],
        "category": "Distributed Systems",
        "link": "https://example.com/paper1"
    }
    paper2 = {
        "title": "Distributed Event Streaming in Modern Microservices Architecture",
        "summary": "This paper explores distributed event streaming in microservice architectures.",
        "date": "28.5.2024",
        "authors": ["Dr. Sarah Chen", "Prof. Michael Rodriguez", "Dr. Aisha Patel"],
        "published_in": "Journal of Distributed Computing",
        "tags": ["microservices", "event streaming", "scalability"],
        "category": "Distributed Systems",
        "link": "https://example.com/paper1"
    }
    paper3 = {
        "title": "Distributed Event Streaming in Modern Microservices Architecture",
        "summary": "This paper explores distributed event streaming in microservice architectures.",
        "date": "28.5.2024",
        "authors": ["Dr. Sarah Chen", "Prof. Michael Rodriguez", "Dr. Aisha Patel"],
        "published_in": "Journal of Distributed Computing",
        "tags": ["microservices", "event streaming", "scalability"],
        "category": "Distributed Systems",
        "link": "https://example.com/paper1"
    }

    papers = [paper1, paper2, paper3]
    html = generate_newsletter_html(papers)
    print(html)
