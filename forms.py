from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, DateField, EmailField, FileField
from wtforms.validators import DataRequired, URL, ValidationError, Optional
from flask_ckeditor import CKEditorField


class LoginForm(FlaskForm):
    username = EmailField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class EmailForm(FlaskForm):

    def is_email(form, email):
        if "@" not in email.data or "." not in email.data:
            raise ValidationError("That is not a valid email address")
        
    name = StringField("Name", validators=[DataRequired()])
    email = EmailField("Email", validators=[DataRequired(), is_email])
    message = CKEditorField("Message", validators=[DataRequired()], render_kw={"style": "height: 250px"})
    submit = SubmitField("Send")


class UploadImageForm(FlaskForm):
    title = StringField("Image Title", validators=[DataRequired()])
    img_url = StringField("Image URL", validators=[Optional(), URL()])
    img_file = FileField("Upload an Image", validators=[Optional()])
    submit = SubmitField("Submit")