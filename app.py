from flask import Flask, render_template, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
import json
import os
import math
from datetime import datetime

from werkzeug.utils import redirect

with open('config.json', 'r') as c:
    params = json.load(c)["params"]
local_server = True
app = Flask(__name__)
app.secret_key = 'the random string'
app.config['UPLOAD_FOLDER'] = params['upload_location']
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params['gmail-user'],
    MAIL_PASSWORD = params['gmail-pass']
)
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)


class Contact(db.Model):
    """`id``name``email``mob``msg``date`"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    mob = db.Column(db.String(12),  nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Blog(db.Model):
    """`id`, `title`, `slug`, `content`, `date`"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


@app.route("/")
def home():
    posts = Blog.query.filter_by().all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    #[0: params['no_of_posts']]
    #posts = posts[]
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page = 1
    page= int(page)
    posts = posts[(page-1)*int(params['no_of_posts']): (page-1)*int(params['no_of_posts'])+ int(params['no_of_posts'])]
    #Pagination Logic
    #First
    if (page==1):
        prev = "#"
        next = "/?page="+ str(page+1)
    elif(page==last):
        prev = "/?page=" + str(page - 1)
        next = "#"
    else:
        prev = "/?page=" + str(page - 1)
        next = "/?page=" + str(page + 1)



    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)


@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post = Blog.query.filter_by(slug=post_slug).first()
    return render_template('post.html', params=params , post=post)


@app.route('/about')
def about():
    return render_template('about.html', params=params)

@app.route('/dashboard', methods = ['GET', 'POST'])
def dashboard():

    if('user' in session and session['user'] == params['admin_user']):
        post = Blog.query.all()
        return render_template('dashboard.html', params=params, post=post)

    if (request.method == 'POST'):
        uname = request.form.get('uname')
        pwd = request.form.get('pass')
        if (uname == params['admin_user'] and pwd == params['admin_password']):
            session['user'] = uname
            post = Blog.query.all()
            return render_template('dashboard.html', params=params, post=post)

    return render_template('login.html', params=params)



@app.route('/edit/<string:id>', methods = ['GET', 'POST'])
def edit(id):
    if ('user' in session and session['user'] == params['admin_user']):
        if request.method == 'POST':
            title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('con')
            img_file = request.form.get('img_file')
            date = datetime.now()

            if id == '0':
                post = Blog(title=title, slug=slug, content=content, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post = Blog.query.filter_by(id=id).first()
                post.title = title
                post.slug = slug
                post.content = content
                post.img_file = img_file
                post.date = date
                db.session.add(post)
                db.session.commit()
                return redirect('/edit/'+id)
        post = Blog.query.filter_by(id=id).first()
        return render_template('edit.html',params=params , post=post, id=id)


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route("/delete/<string:id>", methods = ['GET','POST'])
def delete(id):
    if ('user' in session and session['user'] == params['admin_user']):
        post = Blog.query.filter_by(id=id).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route('/uploader', methods = ['GET', 'POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if(request.method == 'POST'):
            f = request.files['file']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Upload Successfully"

@app.route('/contact', methods = ['GET', 'POST'])
def contact():
    if(request.method == 'POST'):
        '''Add entry to the database'''
        name=request.form.get('name')
        email=request.form.get('email')
        mob=request.form.get('mob')
        msg=request.form.get('msg')
        entry = Contact(name=name, email=email, mob=mob, msg=msg, date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message(
            'New message from blog name is ' + name ,
            sender=email,
            recipients = [params['gmail-user']],
            body = msg + "\n" + mob
        )
    return render_template('contact.html', params=params)


app.run(debug=True)
