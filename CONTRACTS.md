## router.route_query(query) -> dict
{
  source: "faq" | "rag" | "out_of_scope"
  confidence: float
  reason: str
}

## faq_matcher.match_faq(query) -> dict | None
{
  answer: str
  confidence: float
}

## workflow.handle_query(query) -> dict
{
  answer: str
  source: "admin" | "rag" | "out_of_scope"
  confidence: float | None
}
