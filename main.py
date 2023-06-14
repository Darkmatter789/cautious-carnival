from flask import Flask, render_template, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.utils import secure_filename
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from dotenv import load_dotenv
from contact import Contact
from forms import EmailForm, LoginForm
from PIL import Image
import imageio
import skimage.transform as sk
import numpy as np
import os


app = Flask(__name__)


app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET')
ckeditor = CKEditor(app)
Bootstrap(app)
login_manager = LoginManager()
login_manager.init_app(app)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///Users.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def upload_img(img_obj):
    filename = secure_filename(img_obj.filename)
    path = "./static/uploads/" + filename
    img_obj.save((path))
    image = imageio.imread(path).astype(np.uint8)
    resized_image = sk.resize(image, (400, 600))
    pillow_image = Image.fromarray((resized_image * 255).astype(np.uint8))
    pillow_image.save(path)
    

def delete_img(img_filename):
    file_path = os.path.join('./static/uploads', img_filename)
    if os.path.exists(file_path):
        os.remove(file_path)


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


# Opens and creates database tables
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


# Searches database for authenticated user. Returns 404 status if user not in database.
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)


# Route for Home page
@app.route("/")
def home():
    return render_template("index.html")


# Route for Gallery page
@app.route("/gallery")
def gallery():
    return render_template("gallery.html")


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


# Route for Admin Dashboard page.
@app.route("/admin-dashboard", methods=["GET", "POST"])
@login_required
@admin_only
def admin_dashboard():
    return render_template("admin-dashboard.html")


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)