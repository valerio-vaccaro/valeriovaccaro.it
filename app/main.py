from datetime import datetime
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user
from app import db
from app.forms import MePageForm
from app.models import AnalyticsEvent, Article, ArticleTranslation, AssetShortUrl, Profile, Project, User
from app.utils import render_markdown


main_bp = Blueprint('main', __name__)


@main_bp.app_context_processor
def inject_markdown_renderer():
    return {
        'render_markdown': render_markdown,
        'language_flag': language_flag,
        'split_tags': split_tags,
        'tag_color_class': tag_color_class,
    }


@main_bp.route('/')
def home():
    track_event(event_type='page_view', entity_type='home')
    featured_projects = Project.query.filter_by(show_on_homepage=True, is_visible=True).order_by(Project.created_at.desc()).limit(6).all()
    featured_articles = Article.query.filter_by(show_on_homepage=True, is_visible=True).order_by(Article.published_at.desc()).limit(6).all()
    intro_profile = get_global_profile()
    return render_template('home.html', featured_projects=featured_projects, featured_articles=featured_articles, intro_profile=intro_profile)


@main_bp.route('/articles')
def all_articles_page():
    track_event(event_type='page_view', entity_type='articles_listing')
    tag = (request.args.get('tag') or '').strip().lower()
    language = (request.args.get('lang') or '').strip().lower()
    from_date_raw = (request.args.get('from') or '').strip()
    to_date_raw = (request.args.get('to') or '').strip()

    query = Article.query.join(User, User.id == Article.user_id)
    query = query.filter(Article.is_visible.is_(True))
    if tag:
        query = query.filter(Article.tags.ilike(f'%{tag}%'))
    if language:
        query = query.filter(Article.language_code == language)

    from_dt = parse_date(from_date_raw, end_of_day=False)
    to_dt = parse_date(to_date_raw, end_of_day=True)
    if from_dt:
        query = query.filter(Article.published_at >= from_dt)
    if to_dt:
        query = query.filter(Article.published_at <= to_dt)

    articles = query.order_by(Article.published_at.desc()).all()
    language_codes = [
        row[0] for row in Article.query.with_entities(Article.language_code).distinct().order_by(Article.language_code.asc()).all()
        if row[0]
    ]
    return render_template(
        'all_articles.html',
        articles=articles,
        tag=tag,
        language=language,
        language_codes=language_codes,
        from_date=from_date_raw,
        to_date=to_date_raw,
    )


@main_bp.route('/projects')
def all_projects_page():
    track_event(event_type='page_view', entity_type='projects_listing')
    tag = (request.args.get('tag') or '').strip().lower()
    from_date_raw = (request.args.get('from') or '').strip()
    to_date_raw = (request.args.get('to') or '').strip()

    query = Project.query.join(User, User.id == Project.user_id)
    query = query.filter(Project.is_visible.is_(True))
    if tag:
        query = query.filter(Project.tags.ilike(f'%{tag}%'))

    from_dt = parse_date(from_date_raw, end_of_day=False)
    to_dt = parse_date(to_date_raw, end_of_day=True)
    if from_dt:
        query = query.filter(Project.created_at >= from_dt)
    if to_dt:
        query = query.filter(Project.created_at <= to_dt)

    projects = query.order_by(Project.created_at.desc()).all()
    return render_template('all_projects.html', projects=projects, tag=tag, from_date=from_date_raw, to_date=to_date_raw)


@main_bp.route('/s/<code>')
def short_asset_redirect(code):
    item = AssetShortUrl.query.filter_by(code=code).first()
    if not item:
        abort(404)
    return redirect(url_for('static', filename=f'uploads/{item.asset.filename}'))


@main_bp.route('/licensing')
def licensing_page():
    return render_template('licensing.html')


@main_bp.route('/me', methods=['GET', 'POST'])
def me_page():
    track_event(event_type='page_view', entity_type='me')
    profile = get_global_profile()
    form = MePageForm()

    if request.method == 'POST':
        if not current_user.is_authenticated:
            flash('Login required to edit this page.', 'warning')
            return redirect(url_for('auth.login'))
        if form.validate_on_submit():
            profile.markdown_me = form.markdown_me.data
            db.session.commit()
            flash('Me page saved.', 'success')
            return redirect(url_for('main.me_page'))

    if profile and not form.is_submitted():
        form.markdown_me.data = profile.markdown_me or profile.markdown_bio
    return render_template('me.html', profile=profile, form=form)


@main_bp.route('/<username>')
def profile_page(username):
    user = User.query.filter_by(username=username).first_or_404()
    track_event(event_type='page_view', entity_type='profile', owner_user_id=user.id)
    profile = get_global_profile()
    return render_template('profile.html', user=user, profile=profile)


@main_bp.route('/<username>/projects')
def projects_page(username):
    user = User.query.filter_by(username=username).first_or_404()
    track_event(event_type='page_view', entity_type='projects_page', owner_user_id=user.id)
    projects = Project.query.filter_by(user_id=user.id, is_visible=True).order_by(Project.created_at.desc()).all()
    return render_template('projects.html', user=user, projects=projects)


@main_bp.route('/<username>/projects/<slug>')
def project_detail(username, slug):
    user = User.query.filter_by(username=username).first_or_404()
    project = Project.query.filter_by(user_id=user.id, slug=slug, is_visible=True).first()
    if not project:
        abort(404)
    track_event(
        event_type='project_click',
        entity_type='project',
        entity_id=project.id,
        owner_user_id=user.id,
        tags_snapshot=project.tags,
    )
    return render_template('project_detail.html', user=user, project=project)


@main_bp.route('/<username>/articles')
def articles_page(username):
    user = User.query.filter_by(username=username).first_or_404()
    track_event(event_type='page_view', entity_type='articles_page', owner_user_id=user.id)
    articles = Article.query.filter_by(user_id=user.id, is_visible=True).order_by(Article.published_at.desc()).all()
    return render_template('articles.html', user=user, articles=articles)


@main_bp.route('/<username>/articles/<slug>')
def article_detail(username, slug):
    user = User.query.filter_by(username=username).first_or_404()
    article = Article.query.filter_by(user_id=user.id, slug=slug, is_visible=True).first()
    if not article:
        abort(404)
    track_event(
        event_type='article_click',
        entity_type='article',
        entity_id=article.id,
        owner_user_id=user.id,
        tags_snapshot=article.tags,
    )
    requested_lang = (request.args.get('lang') or '').strip().lower()
    translation = None
    if requested_lang:
        translation = ArticleTranslation.query.filter_by(article_id=article.id, language_code=requested_lang).first()
    available_translations = ArticleTranslation.query.filter_by(article_id=article.id).order_by(ArticleTranslation.language_code.asc()).all()
    return render_template(
        'article_detail.html',
        user=user,
        article=article,
        translation=translation,
        requested_lang=requested_lang,
        article_language_code=article.language_code or 'en',
        available_translations=available_translations,
    )


def parse_date(raw, end_of_day=False):
    if not raw:
        return None
    try:
        date_value = datetime.strptime(raw, '%Y-%m-%d')
        if end_of_day:
            return date_value.replace(hour=23, minute=59, second=59)
        return date_value
    except ValueError:
        return None


def get_global_profile():
    profile = Profile.query.order_by(Profile.updated_at.desc()).first()
    if profile:
        return profile

    if not current_user.is_authenticated:
        return None

    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if profile:
        return profile

    profile = Profile(
        user_id=current_user.id,
        title='My Personal Website',
        markdown_bio='Write your profile text from the dashboard.',
        markdown_me='Write your long About Me page in Markdown.',
    )
    from app import db
    db.session.add(profile)
    db.session.commit()
    return profile


def language_flag(language_code):
    if not language_code:
        return '🌐'

    code = language_code.strip().lower()
    if '-' in code:
        region = code.split('-')[-1]
        if len(region) == 2 and region.isalpha():
            return iso_to_flag(region.upper())
        code = code.split('-')[0]
    if '_' in code:
        region = code.split('_')[-1]
        if len(region) == 2 and region.isalpha():
            return iso_to_flag(region.upper())
        code = code.split('_')[0]

    mapping = {
        'en': '🇬🇧',
        'it': '🇮🇹',
        'es': '🇪🇸',
        'fr': '🇫🇷',
        'de': '🇩🇪',
        'pt': '🇵🇹',
        'nl': '🇳🇱',
        'sv': '🇸🇪',
        'da': '🇩🇰',
        'no': '🇳🇴',
        'fi': '🇫🇮',
        'pl': '🇵🇱',
        'cs': '🇨🇿',
        'ro': '🇷🇴',
        'hu': '🇭🇺',
        'el': '🇬🇷',
        'tr': '🇹🇷',
        'ru': '🇷🇺',
        'uk': '🇺🇦',
        'ar': '🇸🇦',
        'he': '🇮🇱',
        'hi': '🇮🇳',
        'zh': '🇨🇳',
        'ja': '🇯🇵',
        'ko': '🇰🇷',
        'id': '🇮🇩',
        'vi': '🇻🇳',
        'th': '🇹🇭',
    }
    return mapping.get(code, '🌐')


def iso_to_flag(country_code):
    if len(country_code) != 2 or not country_code.isalpha():
        return '🌐'
    base = 127397
    return chr(ord(country_code[0]) + base) + chr(ord(country_code[1]) + base)


def split_tags(raw_tags):
    if not raw_tags:
        return []
    return [tag.strip() for tag in raw_tags.split(',') if tag.strip()]


def tag_color_class(tag):
    if not tag:
        return 'tag-palette-0'
    value = sum(ord(c) for c in tag.strip().lower())
    return f'tag-palette-{value % 8}'


def track_event(event_type, entity_type=None, entity_id=None, owner_user_id=None, tags_snapshot=None):
    try:
        viewer_user_id = current_user.id if current_user.is_authenticated else None
        event = AnalyticsEvent(
            user_id=viewer_user_id,
            owner_user_id=owner_user_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            path=request.path[:1024] if request.path else None,
            ip_address=(request.headers.get('X-Forwarded-For') or request.remote_addr or '')[:128],
            user_agent=(request.headers.get('User-Agent') or '')[:512],
            referrer=(request.referrer or '')[:1024],
            tags_snapshot=(tags_snapshot or '')[:1024] or None,
        )
        db.session.add(event)
        db.session.commit()
    except Exception:
        db.session.rollback()
