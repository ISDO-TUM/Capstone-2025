class AgentVerifier:
    def __init__(self):
        self.schema = PaperCard

    def __call__(self, agent_out: dict) -> dict:
        try:
            cleaned = self.schema(**agent_out).dict()
            check_year(cleaned["year"])
            safe_url(cleaned["url"])
            if not crossref_verify(cleaned["title"]):
                cleaned["verified"] = False
            else:
                cleaned["verified"] = True
            return cleaned
        except (ValidationError, ValueError) as exc:
            # Log + raise custom exception for API layer
            log.error("Verifier failed", exc_info=exc)
            raise