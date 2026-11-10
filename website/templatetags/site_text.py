import html
import re

from django import template
from django.utils.html import conditional_escape, format_html
from django.utils.safestring import mark_safe

register = template.Library()
BR_RE = re.compile(r"\s*<br\s*/?>\s*")


class EditableTextNode(template.Node):
    def __init__(self, parts, nodelist, readonly):
        self.parts = parts
        self.nodelist = nodelist
        self.readonly = readonly

    def render(self, context):
        key = ".".join(str(part.resolve(context)) for part in self.parts)
        default = " ".join(self.nodelist.render(context).split())
        default = BR_RE.sub("\n", default)
        default = html.unescape(default)

        value = (context.get("site_texts") or {}).get(key, default)
        body = mark_safe(str(conditional_escape(value)).replace("\n", "<br>"))

        if not context.get("edit_mode"):
            return body
        if self.readonly:
            return format_html('<span data-text-sync="{}">{}</span>', key, body)
        return format_html(
            '<span class="ed-text" data-text-key="{}" data-default="{}"{}>{}</span>',
            key,
            default,
            mark_safe(' data-multiline="1"') if "\n" in default else "",
            body,
        )


@register.tag("et")
def do_editable_text(parser, token):
    """{% et "hero" "title" %}Default text{% endet %}

    Renders the edited text for that key when there is one, otherwise the
    default written inside the tag. In the visual editor the text is wrapped so
    it can be edited in place; with a trailing `ro` it is only kept in sync
    (used for copies of a text that appear in menus or tabs)."""
    bits = token.split_contents()[1:]
    readonly = bool(bits) and bits[-1] == "ro"
    if readonly:
        bits = bits[:-1]
    if not bits:
        raise template.TemplateSyntaxError("et needs at least one key part")
    parts = [parser.compile_filter(bit) for bit in bits]
    nodelist = parser.parse(("endet",))
    parser.delete_first_token()
    return EditableTextNode(parts, nodelist, readonly)
