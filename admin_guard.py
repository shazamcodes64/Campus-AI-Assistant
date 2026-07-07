def admin_guard(faq_hit):
    if not faq_hit:
        return (
            "I don’t have verified information for this yet.\n\n"
            "Please check the SRM portal or confirm with the CR / faculty."
        )
    return faq_hit["answer"]

