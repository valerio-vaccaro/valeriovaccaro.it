import os
import secrets
from collections import Counter
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from werkzeug.utils import secure_filename
from app import db
from app.forms import ASSET_ALLOWED_EXTENSIONS, ArticleForm, ArticleTranslationForm, ProfileForm, ProjectForm, UploadForm
from app.models import AnalyticsEvent, Article, ArticleTranslation, AssetShortUrl, MediaAsset, Profile, Project
from app.utils import normalize_slug, normalize_tags, store_upload


manage_bp = Blueprint('manage', __name__, url_prefix='/manage')


@manage_bp.route('/')
@login_required
def dashboard():
    profile = get_global_profile()
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).all()
    articles = Article.query.filter_by(user_id=current_user.id).order_by(Article.published_at.desc()).all()
    assets = MediaAsset.query.filter_by(user_id=current_user.id).order_by(MediaAsset.created_at.desc()).all()
    return render_template('dashboard.html', profile=profile, projects=projects, articles=articles, assets=assets)


@manage_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    profile = get_global_profile()
    form = ProfileForm(obj=profile)
    if form.validate_on_submit():
        profile.title = form.title.data.strip()
        profile.markdown_bio = form.markdown_bio.data
        db.session.commit()
        flash('Profile saved.', 'success')
        return redirect(url_for('manage.dashboard'))

    return render_template('profile_form.html', form=form)


def get_global_profile():
    profile = Profile.query.order_by(Profile.updated_at.desc()).first()
    if profile:
        return profile
    profile = Profile(
        user_id=current_user.id,
        title='My Personal Website',
        markdown_bio='Write your profile text from the dashboard.',
        markdown_me='Write your long About Me page in Markdown.',
    )
    db.session.add(profile)
    db.session.commit()
    return profile


@manage_bp.route('/projects/new', methods=['GET', 'POST'])
@login_required
def new_project():
    form = ProjectForm()
    if form.validate_on_submit():
        slug = normalize_slug(form.slug.data)
        cover_image_filename = None
        if form.cover_image.data:
            cover_image_filename, _, _, _ = store_upload(form.cover_image.data, current_app.config['UPLOAD_FOLDER'])
        project = Project(
            user_id=current_user.id,
            title=form.title.data.strip(),
            slug=slug,
            markdown_description=form.markdown_description.data,
            external_url=form.external_url.data or None,
            cover_image_filename=cover_image_filename,
            tags=normalize_tags(form.tags.data),
            is_visible=bool(form.is_visible.data),
            show_on_homepage=bool(form.show_on_homepage.data),
        )
        db.session.add(project)
        db.session.commit()
        flash('Project created.', 'success')
        return redirect(url_for('manage.dashboard'))

    return render_template('project_form.html', form=form, editing=False)


@manage_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    form = ProjectForm(obj=project)
    if form.validate_on_submit():
        project.title = form.title.data.strip()
        project.slug = normalize_slug(form.slug.data)
        project.markdown_description = form.markdown_description.data
        project.external_url = form.external_url.data or None
        project.tags = normalize_tags(form.tags.data)
        project.is_visible = bool(form.is_visible.data)
        project.show_on_homepage = bool(form.show_on_homepage.data)
        if form.cover_image.data:
            cover_image_filename, _, _, _ = store_upload(form.cover_image.data, current_app.config['UPLOAD_FOLDER'])
            project.cover_image_filename = cover_image_filename
        db.session.commit()
        flash('Project updated.', 'success')
        return redirect(url_for('manage.dashboard'))

    return render_template('project_form.html', form=form, editing=True)


@manage_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    db.session.delete(project)
    db.session.commit()
    flash('Project deleted.', 'info')
    return redirect(url_for('manage.dashboard'))


@manage_bp.route('/projects/<int:project_id>/visibility', methods=['POST'])
@login_required
def toggle_project_visibility(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first_or_404()
    project.is_visible = not bool(project.is_visible)
    db.session.commit()
    flash(f'Project {"shown" if project.is_visible else "hidden"} on website.', 'success')
    return redirect(url_for('manage.dashboard'))


@manage_bp.route('/articles/new', methods=['GET', 'POST'])
@login_required
def new_article():
    form = ArticleForm()
    if not form.is_submitted():
        form.published_at.data = article_now()
    if request.method == 'POST' and request.form.get('action') == 'upload_assets':
        uploaded_count, skipped_count = upload_multiple_assets(request.files.getlist('inline_assets'))
        if uploaded_count:
            flash(f'{uploaded_count} file(s) uploaded for article editing.', 'success')
        if skipped_count:
            flash(f'{skipped_count} file(s) skipped (unsupported or empty).', 'warning')
        assets = load_user_assets()
        return render_template('article_form.html', form=form, editing=False, assets=assets)
    if form.validate_on_submit():
        slug = normalize_slug(form.slug.data)
        cover_image_filename = None
        if form.cover_image.data:
            cover_image_filename, _, _, _ = store_upload(form.cover_image.data, current_app.config['UPLOAD_FOLDER'])
        article = Article(
            user_id=current_user.id,
            title=form.title.data.strip(),
            slug=slug,
            markdown_body=form.markdown_body.data,
            published_at=form.published_at.data,
            language_code=(form.language_code.data or 'en').strip().lower(),
            tags=normalize_tags(form.tags.data),
            is_visible=bool(form.is_visible.data),
            show_on_homepage=bool(form.show_on_homepage.data),
            external_url=form.external_url.data or None,
            cover_image_filename=cover_image_filename,
        )
        db.session.add(article)
        db.session.commit()
        flash('Article created.', 'success')
        return redirect(url_for('manage.dashboard'))

    assets = load_user_assets()
    return render_template('article_form.html', form=form, editing=False, assets=assets)


@manage_bp.route('/articles/<int:article_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    form = ArticleForm(obj=article)
    if request.method == 'POST' and request.form.get('action') == 'upload_assets':
        uploaded_count, skipped_count = upload_multiple_assets(request.files.getlist('inline_assets'))
        if uploaded_count:
            flash(f'{uploaded_count} file(s) uploaded for article editing.', 'success')
        if skipped_count:
            flash(f'{skipped_count} file(s) skipped (unsupported or empty).', 'warning')
        translations = ArticleTranslation.query.filter_by(article_id=article.id).order_by(ArticleTranslation.language_code.asc()).all()
        assets = load_user_assets()
        return render_template('article_form.html', form=form, editing=True, article=article, translations=translations, assets=assets)
    if form.validate_on_submit():
        article.title = form.title.data.strip()
        article.slug = normalize_slug(form.slug.data)
        article.markdown_body = form.markdown_body.data
        article.published_at = form.published_at.data
        article.language_code = (form.language_code.data or 'en').strip().lower()
        article.tags = normalize_tags(form.tags.data)
        article.is_visible = bool(form.is_visible.data)
        article.show_on_homepage = bool(form.show_on_homepage.data)
        article.external_url = form.external_url.data or None
        if form.cover_image.data:
            cover_image_filename, _, _, _ = store_upload(form.cover_image.data, current_app.config['UPLOAD_FOLDER'])
            article.cover_image_filename = cover_image_filename
        db.session.commit()
        flash('Article updated.', 'success')
        return redirect(url_for('manage.dashboard'))

    translations = ArticleTranslation.query.filter_by(article_id=article.id).order_by(ArticleTranslation.language_code.asc()).all()
    assets = load_user_assets()
    return render_template('article_form.html', form=form, editing=True, article=article, translations=translations, assets=assets)


def article_now():
    from datetime import datetime
    return datetime.utcnow().replace(second=0, microsecond=0)


@manage_bp.route('/articles/<int:article_id>/delete', methods=['POST'])
@login_required
def delete_article(article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    db.session.delete(article)
    db.session.commit()
    flash('Article deleted.', 'info')
    return redirect(url_for('manage.dashboard'))


@manage_bp.route('/articles/<int:article_id>/visibility', methods=['POST'])
@login_required
def toggle_article_visibility(article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    article.is_visible = not bool(article.is_visible)
    db.session.commit()
    flash(f'Article {"shown" if article.is_visible else "hidden"} on website.', 'success')
    return redirect(url_for('manage.dashboard'))


@manage_bp.route('/assets', methods=['GET', 'POST'])
@login_required
def upload_asset():
    form = UploadForm()
    if request.method == 'POST':
        uploaded_count, skipped_count = upload_multiple_assets(request.files.getlist('file'))
        if uploaded_count:
            flash(f'{uploaded_count} file(s) uploaded.', 'success')
        if skipped_count:
            flash(f'{skipped_count} file(s) skipped (unsupported or empty).', 'warning')
        return redirect(url_for('manage.upload_asset'))

    assets = MediaAsset.query.filter_by(user_id=current_user.id).order_by(MediaAsset.created_at.desc()).all()
    short_urls = AssetShortUrl.query.filter_by(user_id=current_user.id).order_by(AssetShortUrl.created_at.desc()).all()
    short_by_asset = {}
    for item in short_urls:
        short_by_asset.setdefault(item.asset_id, []).append(item)
    base = request.url_root.rstrip('/')
    return render_template('assets.html', form=form, assets=assets, short_by_asset=short_by_asset, base=base)


def load_user_assets():
    return MediaAsset.query.filter_by(user_id=current_user.id).order_by(MediaAsset.created_at.desc()).all()


def upload_multiple_assets(files):
    uploaded_count = 0
    skipped_count = 0
    for uploaded_file in files:
        if not uploaded_file:
            skipped_count += 1
            continue
        original_name = (uploaded_file.filename or '').strip()
        if not original_name:
            skipped_count += 1
            continue
        ext = os.path.splitext(secure_filename(original_name))[1].lower().lstrip('.')
        if ext not in ASSET_ALLOWED_EXTENSIONS:
            skipped_count += 1
            continue
        filename, original_name, size_bytes, mime_type = store_upload(uploaded_file, current_app.config['UPLOAD_FOLDER'])
        asset = MediaAsset(
            user_id=current_user.id,
            filename=filename,
            original_name=original_name,
            size_bytes=size_bytes,
            mime_type=mime_type,
        )
        db.session.add(asset)
        uploaded_count += 1
    if uploaded_count:
        db.session.commit()
    return uploaded_count, skipped_count


@manage_bp.route('/content', methods=['GET'])
@login_required
def content_analysis():
    return redirect(url_for('manage.upload_asset'))


@manage_bp.route('/content/assets/<int:asset_id>/delete', methods=['POST'])
@login_required
def delete_asset(asset_id):
    asset = MediaAsset.query.filter_by(id=asset_id, user_id=current_user.id).first_or_404()
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], asset.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(asset)
    db.session.commit()
    flash('Asset deleted.', 'info')
    return redirect(url_for('manage.upload_asset'))


@manage_bp.route('/content/assets/<int:asset_id>/shorten', methods=['POST'])
@login_required
def create_asset_short_url(asset_id):
    asset = MediaAsset.query.filter_by(id=asset_id, user_id=current_user.id).first_or_404()
    code = request.form.get('code', '').strip().lower()
    if code:
        if len(code) < 4 or len(code) > 32 or not code.replace('-', '').replace('_', '').isalnum():
            flash('Short code must be 4-32 chars and use letters, numbers, - or _.', 'danger')
            return redirect(url_for('manage.upload_asset'))
        exists = AssetShortUrl.query.filter_by(code=code).first()
        if exists:
            flash('Short code already in use.', 'danger')
            return redirect(url_for('manage.upload_asset'))
    else:
        while True:
            code = secrets.token_urlsafe(5).replace('-', '').replace('_', '')[:8].lower()
            if not AssetShortUrl.query.filter_by(code=code).first():
                break
    item = AssetShortUrl(user_id=current_user.id, asset_id=asset.id, code=code)
    db.session.add(item)
    db.session.commit()
    flash('Short URL created.', 'success')
    return redirect(url_for('manage.upload_asset'))


@manage_bp.route('/content/short/<int:short_id>/delete', methods=['POST'])
@login_required
def delete_asset_short_url(short_id):
    item = AssetShortUrl.query.filter_by(id=short_id, user_id=current_user.id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    flash('Short URL deleted.', 'info')
    return redirect(url_for('manage.upload_asset'))


@manage_bp.route('/statistics')
@login_required
def statistics():
    base_query = AnalyticsEvent.query.filter_by(owner_user_id=current_user.id)

    total_events = base_query.count()
    total_article_clicks = base_query.filter_by(entity_type='article').count()
    total_project_clicks = base_query.filter_by(entity_type='project').count()
    unique_ips = base_query.with_entities(AnalyticsEvent.ip_address).filter(AnalyticsEvent.ip_address.isnot(None)).distinct().count()

    top_articles = (
        db.session.query(Article.title, func.count(AnalyticsEvent.id).label('views'))
        .join(AnalyticsEvent, AnalyticsEvent.entity_id == Article.id)
        .filter(
            AnalyticsEvent.owner_user_id == current_user.id,
            AnalyticsEvent.entity_type == 'article',
        )
        .group_by(Article.id, Article.title)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(10)
        .all()
    )

    top_projects = (
        db.session.query(Project.title, func.count(AnalyticsEvent.id).label('views'))
        .join(AnalyticsEvent, AnalyticsEvent.entity_id == Project.id)
        .filter(
            AnalyticsEvent.owner_user_id == current_user.id,
            AnalyticsEvent.entity_type == 'project',
        )
        .group_by(Project.id, Project.title)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(10)
        .all()
    )

    top_languages = (
        db.session.query(
            Article.language_code,
            func.count(AnalyticsEvent.id).label('views'),
        )
        .join(AnalyticsEvent, AnalyticsEvent.entity_id == Article.id)
        .filter(
            Article.user_id == current_user.id,
            AnalyticsEvent.owner_user_id == current_user.id,
            AnalyticsEvent.entity_type == 'article',
        )
        .group_by(Article.language_code)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .all()
    )

    per_article_stats = (
        db.session.query(
            Article.id,
            Article.title,
            func.count(AnalyticsEvent.id).label('views'),
            func.count(func.distinct(AnalyticsEvent.ip_address)).label('unique_ips'),
            func.max(AnalyticsEvent.created_at).label('last_click_at'),
        )
        .outerjoin(
            AnalyticsEvent,
            db.and_(
                AnalyticsEvent.entity_type == 'article',
                AnalyticsEvent.entity_id == Article.id,
                AnalyticsEvent.owner_user_id == current_user.id,
            ),
        )
        .filter(Article.user_id == current_user.id)
        .group_by(Article.id, Article.title)
        .order_by(func.count(AnalyticsEvent.id).desc(), Article.published_at.desc())
        .all()
    )

    per_project_stats = (
        db.session.query(
            Project.id,
            Project.title,
            func.count(AnalyticsEvent.id).label('views'),
            func.count(func.distinct(AnalyticsEvent.ip_address)).label('unique_ips'),
            func.max(AnalyticsEvent.created_at).label('last_click_at'),
        )
        .outerjoin(
            AnalyticsEvent,
            db.and_(
                AnalyticsEvent.entity_type == 'project',
                AnalyticsEvent.entity_id == Project.id,
                AnalyticsEvent.owner_user_id == current_user.id,
            ),
        )
        .filter(Project.user_id == current_user.id)
        .group_by(Project.id, Project.title)
        .order_by(func.count(AnalyticsEvent.id).desc(), Project.created_at.desc())
        .all()
    )

    ip_stats = (
        db.session.query(AnalyticsEvent.ip_address, func.count(AnalyticsEvent.id).label('events'))
        .filter(AnalyticsEvent.owner_user_id == current_user.id)
        .group_by(AnalyticsEvent.ip_address)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(20)
        .all()
    )

    daily_stats = (
        db.session.query(func.date(AnalyticsEvent.created_at).label('day'), func.count(AnalyticsEvent.id).label('events'))
        .filter(AnalyticsEvent.owner_user_id == current_user.id)
        .group_by(func.date(AnalyticsEvent.created_at))
        .order_by(func.date(AnalyticsEvent.created_at).desc())
        .limit(30)
        .all()
    )

    tag_counter = Counter()
    tag_rows = base_query.with_entities(AnalyticsEvent.tags_snapshot).filter(AnalyticsEvent.tags_snapshot.isnot(None)).all()
    for (raw_tags,) in tag_rows:
        if not raw_tags:
            continue
        for tag in [t.strip().lower() for t in raw_tags.split(',') if t.strip()]:
            tag_counter[tag] += 1
    tag_stats = tag_counter.most_common(25)
    daily_labels = [str(day) for day, _ in reversed(daily_stats)]
    daily_values = [events for _, events in reversed(daily_stats)]
    article_chart_labels = [item.title for item in per_article_stats[:10]]
    article_chart_values = [item.views for item in per_article_stats[:10]]
    project_chart_labels = [item.title for item in per_project_stats[:10]]
    project_chart_values = [item.views for item in per_project_stats[:10]]

    return render_template(
        'statistics.html',
        total_events=total_events,
        total_article_clicks=total_article_clicks,
        total_project_clicks=total_project_clicks,
        unique_ips=unique_ips,
        top_articles=top_articles,
        top_projects=top_projects,
        top_languages=top_languages,
        ip_stats=ip_stats,
        daily_stats=daily_stats,
        tag_stats=tag_stats,
        per_article_stats=per_article_stats,
        per_project_stats=per_project_stats,
        daily_labels=daily_labels,
        daily_values=daily_values,
        article_chart_labels=article_chart_labels,
        article_chart_values=article_chart_values,
        project_chart_labels=project_chart_labels,
        project_chart_values=project_chart_values,
    )


@manage_bp.route('/articles/<int:article_id>/translations/new', methods=['GET', 'POST'])
@login_required
def new_article_translation(article_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    form = ArticleTranslationForm()
    if form.validate_on_submit():
        language_code = form.language_code.data.strip().lower()
        exists = ArticleTranslation.query.filter_by(article_id=article.id, language_code=language_code).first()
        if exists:
            flash('Translation for this language already exists.', 'danger')
            return render_template('article_translation_form.html', form=form, article=article, editing=False)
        translation = ArticleTranslation(
            article_id=article.id,
            language_code=language_code,
            title=form.title.data.strip(),
            markdown_body=form.markdown_body.data,
        )
        db.session.add(translation)
        db.session.commit()
        flash('Translation created.', 'success')
        return redirect(url_for('manage.edit_article', article_id=article.id))
    return render_template('article_translation_form.html', form=form, article=article, editing=False)


@manage_bp.route('/articles/<int:article_id>/translations/<int:translation_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article_translation(article_id, translation_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    translation = ArticleTranslation.query.filter_by(id=translation_id, article_id=article.id).first_or_404()
    form = ArticleTranslationForm(obj=translation)
    if form.validate_on_submit():
        language_code = form.language_code.data.strip().lower()
        exists = ArticleTranslation.query.filter(
            ArticleTranslation.article_id == article.id,
            ArticleTranslation.language_code == language_code,
            ArticleTranslation.id != translation.id,
        ).first()
        if exists:
            flash('Translation for this language already exists.', 'danger')
            return render_template('article_translation_form.html', form=form, article=article, editing=True, translation=translation)
        translation.language_code = language_code
        translation.title = form.title.data.strip()
        translation.markdown_body = form.markdown_body.data
        db.session.commit()
        flash('Translation updated.', 'success')
        return redirect(url_for('manage.edit_article', article_id=article.id))
    return render_template('article_translation_form.html', form=form, article=article, editing=True, translation=translation)


@manage_bp.route('/articles/<int:article_id>/translations/<int:translation_id>/delete', methods=['POST'])
@login_required
def delete_article_translation(article_id, translation_id):
    article = Article.query.filter_by(id=article_id, user_id=current_user.id).first_or_404()
    translation = ArticleTranslation.query.filter_by(id=translation_id, article_id=article.id).first_or_404()
    db.session.delete(translation)
    db.session.commit()
    flash('Translation deleted.', 'info')
    return redirect(url_for('manage.edit_article', article_id=article.id))
