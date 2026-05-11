from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    profile = db.relationship('Profile', backref='owner', uselist=False, cascade='all, delete-orphan')
    projects = db.relationship('Project', backref='owner', cascade='all, delete-orphan', lazy=True)
    articles = db.relationship('Article', backref='owner', cascade='all, delete-orphan', lazy=True)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False, default='My Personal Website')
    markdown_bio = db.Column(db.Text, nullable=False, default='Write your bio in Markdown')
    markdown_me = db.Column(db.Text, nullable=False, default='Write your long About Me page in Markdown')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), nullable=False)
    markdown_description = db.Column(db.Text, nullable=False)
    external_url = db.Column(db.String(1024), nullable=True)
    cover_image_filename = db.Column(db.String(255), nullable=True)
    tags = db.Column(db.String(512), nullable=True)
    show_on_homepage = db.Column(db.Boolean, nullable=False, default=True)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)
    source_platform = db.Column(db.String(20), nullable=True)
    last_commit_at = db.Column(db.DateTime, nullable=True)
    stars_count = db.Column(db.Integer, nullable=True)
    forks_count = db.Column(db.Integer, nullable=True)
    watchers_count = db.Column(db.Integer, nullable=True)
    open_issues_count = db.Column(db.Integer, nullable=True)
    default_branch = db.Column(db.String(255), nullable=True)
    repo_size_kb = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'slug', name='uq_project_user_slug'),)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), nullable=False)
    markdown_body = db.Column(db.Text, nullable=False)
    external_url = db.Column(db.String(1024), nullable=True)
    cover_image_filename = db.Column(db.String(255), nullable=True)
    tags = db.Column(db.String(512), nullable=True)
    language_code = db.Column(db.String(10), nullable=False, default='en')
    show_on_homepage = db.Column(db.Boolean, nullable=False, default=True)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)
    published_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    translations = db.relationship('ArticleTranslation', backref='article', cascade='all, delete-orphan', lazy=True)

    __table_args__ = (db.UniqueConstraint('user_id', 'slug', name='uq_article_user_slug'),)


class MediaAsset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(255), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('assets', lazy=True, cascade='all, delete-orphan'))
    short_urls = db.relationship('AssetShortUrl', backref='asset', lazy=True, cascade='all, delete-orphan')


class AssetShortUrl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    asset_id = db.Column(db.Integer, db.ForeignKey('media_asset.id'), nullable=False)
    code = db.Column(db.String(32), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship('User', backref=db.backref('asset_short_urls', lazy=True, cascade='all, delete-orphan'))


class AnalyticsEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    event_type = db.Column(db.String(64), nullable=False)
    entity_type = db.Column(db.String(64), nullable=True)
    entity_id = db.Column(db.Integer, nullable=True)
    path = db.Column(db.String(1024), nullable=True)
    ip_address = db.Column(db.String(128), nullable=True)
    user_agent = db.Column(db.String(512), nullable=True)
    referrer = db.Column(db.String(1024), nullable=True)
    tags_snapshot = db.Column(db.String(1024), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class ArticleTranslation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    language_code = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    markdown_body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (db.UniqueConstraint('article_id', 'language_code', name='uq_article_translation_lang'),)
