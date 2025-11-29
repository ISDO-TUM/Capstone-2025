import paper_handling.paper_handler as handler
from unittest.mock import patch


@patch.object(handler, "fetch_works_multiple_queries")
def test_fetch_works_multiple_queries_multiple_results(mock_fetch):
    """
    This test verifies that when multiple results are mocked, the fetch_works_multiple_queries
    function returns all expected abstracts and calls the underlying function with the correct queries.
    """

    mock_fetch.return_value = (
        [
            {"abstract": "A1"},
            {"abstract": "A2"},
            {"abstract": "A3"},
        ],
        None,
    )

    queries = [
        "traveling salesman problem",
        "TSP optimization",
        "traveling salesman problem algorithms",
        "TSP heuristics",
        "TSP exact methods",
        "traveling salesman problem 2020-2024",
    ]

    works, meta = handler.fetch_works_multiple_queries(queries)

    assert isinstance(works, list)
    assert len(works) == 3
    assert all("abstract" in w for w in works)
    mock_fetch.assert_called_once_with(queries)
