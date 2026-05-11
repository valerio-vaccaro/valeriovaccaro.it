from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.fields.datetime import DateTimeLocalField
from wtforms.validators import DataRequired, Length, Optional, URL

ASSET_ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'pdf', 'zip', 'txt', 'md']


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')


class ProfileForm(FlaskForm):
    title = StringField('Page title', validators=[DataRequired(), Length(max=255)])
    markdown_bio = TextAreaField('Markdown bio', validators=[DataRequired()])
    submit = SubmitField('Save profile')


class MePageForm(FlaskForm):
    markdown_me = TextAreaField('About me text (Markdown)', validators=[DataRequired()])
    submit = SubmitField('Save me page')


class ProjectForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=255)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=255)])
    markdown_description = TextAreaField('Markdown description', validators=[DataRequired()])
    external_url = StringField('External URL', validators=[Optional(), URL()])
    tags = StringField('Tags (comma separated)', validators=[Optional(), Length(max=512)])
    is_visible = BooleanField('Show on website', default=True)
    show_on_homepage = BooleanField('Show on homepage', default=True)
    cover_image = FileField('Cover image', validators=[Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'])])
    submit = SubmitField('Save project')


class ArticleForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=255)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=255)])
    markdown_body = TextAreaField('Markdown article', validators=[DataRequired()])
    published_at = DateTimeLocalField('Publish date', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    language_code = SelectField(
        'Article language',
        choices=[
            ('en', '🇬🇧 English'),
            ('it', '🇮🇹 Italian'),
            ('es', '🇪🇸 Spanish'),
            ('fr', '🇫🇷 French'),
            ('de', '🇩🇪 German'),
            ('pt', '🇵🇹 Portuguese'),
            ('hu', '🇭🇺 Hungarian'),
            ('ru', '🇷🇺 Russian'),
            ('zh', '🇨🇳 Chinese'),
        ],
        default='en',
        validators=[DataRequired()],
    )
    tags = StringField('Tags (comma separated)', validators=[Optional(), Length(max=512)])
    is_visible = BooleanField('Show on website', default=True)
    show_on_homepage = BooleanField('Show on homepage', default=True)
    external_url = StringField('External URL', validators=[Optional(), URL()])
    cover_image = FileField('Cover image', validators=[Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'])])
    submit = SubmitField('Save article')


class UploadForm(FlaskForm):
    file = FileField('Upload image/file', validators=[Optional(), FileAllowed(ASSET_ALLOWED_EXTENSIONS)])
    submit = SubmitField('Upload')


class ArticleTranslationForm(FlaskForm):
    language_code = SelectField(
        'Language',
        choices=[
            ('en', '🇬🇧 English'),
            ('it', '🇮🇹 Italian'),
            ('es', '🇪🇸 Spanish'),
            ('fr', '🇫🇷 French'),
            ('de', '🇩🇪 German'),
            ('pt', '🇵🇹 Portuguese'),
            ('hu', '🇭🇺 Hungarian'),
            ('ru', '🇷🇺 Russian'),
            ('zh', '🇨🇳 Chinese'),
        ],
        validators=[DataRequired()],
    )
    title = StringField('Translated title', validators=[DataRequired(), Length(max=255)])
    markdown_body = TextAreaField('Translated markdown body', validators=[DataRequired()])
    submit = SubmitField('Save translation')
