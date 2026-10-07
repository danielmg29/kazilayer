from html import unescape

import bleach
from django.db import models

RICH_TEXT_TAGS = {
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "a",
    "code",
    "h2",
    "h3",
    "blockquote",
}
RICH_TEXT_ATTRIBUTES = {"a": ["href", "title", "rel"]}


def sanitize_rich_text(value):
    return bleach.clean(
        value or "",
        tags=RICH_TEXT_TAGS,
        attributes=RICH_TEXT_ATTRIBUTES,
        protocols={"http", "https", "mailto"},
        strip=True,
    )


def rich_text_to_plain(value):
    return unescape(bleach.clean(value or "", tags=set(), strip=True)).strip()


class RichTextField(models.TextField):
    """Restricted HTML persisted only after allow-list sanitisation."""

    description = "Sanitised restricted rich text"

    def get_prep_value(self, value):
        return super().get_prep_value(sanitize_rich_text(value))
