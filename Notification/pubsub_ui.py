import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, redirect, url_for, flash

# Import PubSub and SendMail modules
from Notification.PubSub import (
    TAGS, MAX_NUMBER_OF_SENT_MAIL, fetch_works_multiple_queries,
    simplify_paper_results, rank_and_filter_similar_papers, split_ranked_papers
)
from Notification.SendMail import sendmail
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
app.secret_key = "supersecret"  # Required for flash messages


# In-memory list of subscribers (for demo purposes)
subscribers = []

@app.route("/", methods=["GET", "POST"])
def home():
    """
    Main page: shows recommended papers and allows email subscription.
    """
    # Fetch and process recommended papers
    result = fetch_works_multiple_queries(TAGS)
    #print("FETCH RESULT:", result)
    #print("TYPE:", type(result))
    papers = simplify_paper_results(fetch_works_multiple_queries(TAGS)[0])

    # Simulate the full process: get all hashes as similar_ids (for demo)
    similar_ids = [p["hash"] for p in papers]
    results = rank_and_filter_similar_papers(papers, similar_ids)
    email_papers, ui_papers = split_ranked_papers(results, MAX_NUMBER_OF_SENT_MAIL)


    if request.method == "POST":
        # Handle subscription form
        email = request.form.get("email")
        topic = request.form.get("topic")
        if email and topic:
            subscribers.append({"email": email, "topic": topic})
            flash(f"Subscribed {email} to topic '{topic}'!")
        else:
            flash("Please fill in all fields.")
        return redirect(url_for("home"))
    
    print("UI papers:", ui_papers)
    print("Email papers:", email_papers)
    print("Subscribers:", subscribers)

    return render_template(
        "pubsub_home.html",
        email_papers=email_papers,
        ui_papers=ui_papers,
        subscribers=subscribers
    )

@app.route("/send", methods=["POST"])
def send_notifications():
    """
    Sends the selected top papers by email to all subscribers.
    """
    email_papers = request.form.getlist('email_paper')
    # Format papers as HTML content for email
    html_content = "<br>".join(email_papers)
    # Send email to each subscriber (demo: just prints result)
    for sub in subscribers:
        email = sub['email']
        sendmail(email, html_content)
    flash("Emails sent to subscribers!")
    return redirect(url_for("home"))

if __name__ == "__main__":
    # Ensure template folder is set if not default
    app.run(debug=True)
