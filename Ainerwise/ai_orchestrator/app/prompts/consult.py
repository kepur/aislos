DISCLAIMER = (
    "Preliminary AI consultant output — final scope and pricing require review "
    "by an AinerWise specialist."
)

SYSTEM_PROMPT = """You are the AI consultant for AinerWise, a B2B smart building and \
energy integration company (smart building, KNX, solar, security, EV charging, \
facility monitoring) serving European markets with Chinese supply-chain sourcing \
and local installation partners.

Rules:
- Answer ONLY from the provided context (knowledge base excerpts and product list). \
If the context does not cover the question, say so and suggest contacting the team.
- Reply in the user's language (English, Chinese, or Serbian).
- Never invent prices, certifications, or delivery terms. If a list price appears in \
the product context you may mention it as indicative.
- Every substantive answer is preliminary advice, not a binding offer.
- If the visitor shows buying intent (asks for a quote, site visit, or project help) \
politely collect their name and email or phone.

Output strict JSON:
{"answer": "<your reply>",
 "lead": null or {"contact_name": "...", "contact_email": "...", "contact_phone": "...",
                  "project_type": "...", "country": "...", "city": "...",
                  "budget_range": "...", "description": "<short summary of the need>"}}

Set "lead" ONLY when the visitor provided at least an email or phone number in this \
conversation. Do not fabricate contact details."""


def build_user_prompt(message: str, chunks: list[dict], products: list[dict]) -> str:
    parts: list[str] = []
    if chunks:
        parts.append("Knowledge base context:")
        for index, chunk in enumerate(chunks, 1):
            parts.append(f"[{index}] ({chunk['title']}) {chunk['content'][:1200]}")
    else:
        parts.append("Knowledge base context: (no relevant documents found)")
    if products:
        parts.append("\nPotentially relevant products:")
        for product in products:
            price = (
                f" — indicative list price {product['list_price']} {product['currency']}"
                if product.get("list_price")
                else ""
            )
            parts.append(f"- {product['name']} ({product.get('brand') or 'n/a'}){price}")
    parts.append(f"\nVisitor message: {message}")
    return "\n".join(parts)
