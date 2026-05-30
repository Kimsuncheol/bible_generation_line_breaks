import gettext
import json
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["client"])

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"
TRANSLATIONS_DIR = BASE_DIR / "translations"
SUPPORTED_LOCALES = {"en", "ko"}
DEFAULT_LOCALE = "en"

templates = Jinja2Templates(directory=TEMPLATE_DIR)

_ = lambda message: message

CLIENT_MESSAGE_IDS = {
    "chars_suffix": _("chars"),
    "lines_suffix": _("lines"),
    "no_output": _("No output text to copy."),
    "copied": _("Output copied."),
    "copy_failed": _("Unable to copy output."),
    "request_failed": _("Request failed with status {status}"),
    "processing": _("Processing text..."),
    "processed": _("Processed successfully."),
    "preparing": _("Preparing {filename}..."),
    "downloaded": _("{filename} downloaded."),
    "reference_required": _("Reference is required."),
    "generating": _("Generating Bible text..."),
    "generated": _("{count} unique reference(s) generated."),
    "lookup_used": _("Lookup text copied into input."),
    "lookup_empty": _("No lookup text available."),
    "ready": _("Ready."),
    "criterion_required": _("Select a line-break criterion first."),
    "general_input_required": _("General text is required."),
    "general_processed": _("General text processed successfully."),
}


def normalize_locale(locale: str | None) -> str | None:
    if not locale:
        return None

    normalized = locale.lower().replace("_", "-").split("-", 1)[0]
    return normalized if normalized in SUPPORTED_LOCALES else None


def locale_from_accept_language(header_value: str | None) -> str | None:
    if not header_value:
        return None

    for language_range in header_value.split(","):
        locale = normalize_locale(language_range.split(";", 1)[0].strip())
        if locale:
            return locale

    return None


def select_locale(request: Request, lang: str | None) -> str:
    return (
        normalize_locale(lang)
        or locale_from_accept_language(request.headers.get("accept-language"))
        or DEFAULT_LOCALE
    )


def get_translator(locale: str):
    translation = gettext.translation(
        "messages",
        localedir=TRANSLATIONS_DIR,
        languages=[locale],
        fallback=True,
    )
    return translation.gettext


def translated_client_messages(gettext_func):
    return {
        key: gettext_func(message_id)
        for key, message_id in CLIENT_MESSAGE_IDS.items()
    }


@router.get("/client", response_class=HTMLResponse)
def read_client(request: Request, lang: str | None = None):
    locale = select_locale(request, lang)
    gettext_func = get_translator(locale)
    return templates.TemplateResponse(
        request,
        "client.html",
        {
            "_": gettext_func,
            "locale": locale,
            "i18n_json": json.dumps(
                translated_client_messages(gettext_func),
                ensure_ascii=False,
            ),
        },
    )
