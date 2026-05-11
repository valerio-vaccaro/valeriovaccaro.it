import os
import re
import uuid
import markdown
from markupsafe import Markup
from werkzeug.utils import secure_filename


def render_markdown(text):
    html = markdown.markdown(text or '', extensions=['fenced_code', 'tables', 'nl2br'])
    return Markup(html)


def normalize_slug(raw):
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', (raw or '').strip().lower()).strip('-')
    return slug or str(uuid.uuid4())[:8]


def store_upload(uploaded_file, upload_folder):
    original_name = uploaded_file.filename or 'file'
    safe_name = secure_filename(original_name)
    ext = os.path.splitext(safe_name)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_folder, filename)
    uploaded_file.save(filepath)
    size_bytes = os.path.getsize(filepath)
    mime_type = uploaded_file.mimetype
    return filename, original_name, size_bytes, mime_type


def normalize_tags(raw_tags):
    if not raw_tags:
        return ''
    seen = set()
    out = []
    for item in raw_tags.split(','):
        tag = item.strip().lower()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        out.append(tag)
    return ', '.join(out)
