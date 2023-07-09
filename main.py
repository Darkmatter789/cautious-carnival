from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from dotenv import load_dotenv
from contact import Contact
from forms import EmailForm, LoginForm, UploadImageForm, RegisterForm
from PIL import Image
import imageio
import skimage.transform as sk
import numpy as np
import os


# Loads .env file with environment variables
load_dotenv()


# Creates Flask application instance
app = Flask(__name__)


# Fix proxy headers when application is behind a proxy server
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


# Set secret key for the application
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET')


# Initialize CKEditor and Bootstrap extensions
ckeditor = CKEditor(app)
Bootstrap(app)


# Initialize LoginManager for user authentication
login_manager = LoginManager()
login_manager.init_app(app)


# Configure SQLite database URI and track modifications
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Users.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Initialize SQLAlchemy database
db = SQLAlchemy(app)


# Function to create a thumbnail image
def create_thumbnail(filename):
    dir_path = './static/images/' + filename
    thumbnail_dir = './static/thumbnails/'
    thumbnail_path = os.path.join(thumbnail_dir, filename)
    image = imageio.imread(dir_path).astype(np.uint8)
    resized_image = sk.resize(image, (300, 400))
    pillow_image = Image.fromarray((resized_image * 255).astype(np.uint8))
    pillow_image.save(thumbnail_path, "JPEG")


# Function to handle image upload
def upload_img(img_obj):
    filename = secure_filename(img_obj.filename)
    path = "./static/images/" + filename
    img_obj.save((path))
    create_thumbnail(filename)


# Function to delete an image
def delete_img(img_filename):
    file_path = os.path.join('./static/images', img_filename)
    thumb_path = os.path.join('./static/thumbnails/', img_filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    if os.path.exists(thumb_path):
        os.remove(thumb_path)


# User model representing a user in the database
class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))


# ImageUpload model representing an image in the database
class ImageUpload(db.Model):
    __tablename__ = "image"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    filename = db.Column(db.String(250), nullable=False)


# Create database tables
with app.app_context():
    db.create_all()


# Decorator function that checks if current_user is Admin
def admin_only(f):
    @wraps(f)
    def decorator(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorator


# Callback function to load a user from the database
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# Route for Home page
@app.route("/")
def home():
    all_images = ImageUpload.query.all()
    latest = all_images[len(all_images)-3:]
    return render_template("index.html", images=latest)


# Route for Gallery page
@app.route("/gallery", methods=["GET", "POST"])
def gallery():
    images = ImageUpload.query.all()
    return render_template("gallery.html", images=images)


# Route for about page
@app.route("/about")
def about():
    return render_template("about.html")


# Route for Contact page
@app.route("/contact")
def contact():
    contact_form = EmailForm()
    if contact_form.validate_on_submit():
        new_message = Contact(
            contact_form.name.data, 
            contact_form.email.data,  
            contact_form.body.data
            )
        Contact.send_message(new_message)
        flash("Message Sent")
        return redirect(url_for("contact"))
    return render_template("contact.html", form=contact_form)


# Route for admin login page
@app.route("/admin-login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    all_users = User.query.all()
    if form.validate_on_submit():
        for user in all_users:
            if form.username.data == user.username and check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for("admin_dashboard"))
        if form.username != user.username:
            flash("That username does not exist. Please try again")
            return redirect(url_for("login"))
        elif not check_password_hash(user.password, form.password.data):
            flash("That password is incorrect. Please try again.")
            return redirect(url_for("login"))
    return render_template("admin-login.html", form=form)


# Route for logout
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("login"))


# Route for user registration
@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data,
            password=generate_password_hash(form.password.data, 'pbkdf2:sha256', 8)
        )
        db.session.add(new_user)
        db.session.commit()
        load_user(new_user)
        return redirect(url_for("admin_dashboard"))
    return render_template("admin-login.html", form=form)


# Route for Admin Dashboard page.
@app.route("/admin-dashboard", methods=["GET", "POST"])
@login_required
@admin_only
def admin_dashboard():
    form = UploadImageForm()
    if form.validate_on_submit():
        img = ImageUpload(
            title=form.title.data,
            filename=form.file.data.filename
        )
        db.session.add(img)
        db.session.commit()
        upload_img(form.file.data)
        return redirect(url_for("admin_dashboard"))
    return render_template("admin-dashboard.html", form=form)


# Route for deleting an image
@app.route("/delete/<filename>", methods=["GET", "POST"])
@login_required
@admin_only
def delete(filename):
    all_images = ImageUpload.query.all()
    img_ids = {image.id:image.filename for image in all_images}
    for key,value in img_ids.items():
        if value == filename:
            entry = ImageUpload.query.get(key)
            db.session.delete(entry)
            db.session.commit()
    delete_img(filename)
    return redirect(url_for("gallery"))


# Run the application
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)