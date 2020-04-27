from flask import Flask,render_template,request,session,redirect,flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import math
import json
import os
from werkzeug.utils import secure_filename
from datetime import  datetime
with open("config.json","r") as c:
    params=json.load(c)["params"]

local_server=params["local_server"]
app=Flask(__name__)
app.secret_key='super-secret-key'
app.config['UPLOAD_FOLDER']=params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params["email_user"],
    MAIL_PASSWORD=params["email_pass"],
    MAIL_ASCII_ATTACHMENTS=True
)
mail=Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params["local_uri"]
else:
    app.config['SQLALCHEMY_DATABASE_URI']=params["prod_uri"]

db=SQLAlchemy(app)#initialize db

class Contacts(db.Model):   #define the structure of my table

    SNO=db.Column(db.Integer,primary_key=True)
    NAME=db.Column(db.String(20),nullable=False)
    EMAIL= db.Column(db.String(20),nullable=False)
    PHONE_NUMBER= db.Column(db.String(11),nullable=False)
    MSG= db.Column(db.String(120),nullable=False)
    DATE=db.Column(db.String(20))

class Post(db.Model):

    SNO = db.Column(db.Integer, primary_key=True)
    TITLE = db.Column(db.String(20), nullable=False)
    tag_line=db.Column(db.String(20),nullable=False)
    CONTENT = db.Column(db.String(100), nullable=False)
    DATE = db.Column(db.String(11))
    slug = db.Column(db.String(20),nullable=False)
    imG_file=db.Column(db.String(20))

@app.route("/dashboard",methods=['GET','POST'])
def dashboard():
    if "user" in session and session['user']==params['admin_user']:
        posts = Post.query.all()
        return render_template('dashboard.html',params=params,posts=posts)
    if request.method=='POST':
        username=request.form.get('user')
        userpass=request.form.get('password')
        if username==params["admin_user"] and userpass==params["admin_pass"]:
            session['user']=username
            posts=Post.query.all()
            return render_template("dashboard.html", params=params,posts=posts)
    else:
        return render_template('sign.html',params=params)
@app.route("/")
def index():
    flash("Subscribe to my site","warning")

    posts=Post.query.filter_by().all()
    last=math.ceil(len(posts)/int(params['no_of_post']))
    page=request.args.get('page')

    if not str(page).isnumeric():

        page=1
    page=int(page)
    posts=posts[(page-1)*int(params['no_of_post']):(page)*int(params['no_of_post'])]

    if page==1:
        prev="#"
        next="/?page=" +str(page+1)
        print(page)
    elif page==last:
        prev="/?page="+str(page-1)
        next="#"
        print(page)
    else:
        prev="/?page="+str(page-1)
        next="/?page=" +str(page+1)
    return render_template('index.html',params=params,posts=posts,prev=prev,next=next)


@app.route("/about")
def about():
    return render_template('about.html',params=params)


@app.route("/contact", methods=['GET','POST']) #fetching the data from contact page
def contact():
    if request.method=='POST':
        name = request.form.get('namehtm')
        email_id = request.form.get('emailhtm')
        phone_num = request.form.get('phonehtm')
        message= request.form.get('msghml')

        entry=Contacts(NAME=name,EMAIL=email_id,PHONE_NUMBER=phone_num,MSG=message,DATE=datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message("NEW POST FROM "+ name.upper(),
                          sender=email_id,
                          recipients=[params["email_user"]],
                          body=message +"\n"+ phone_num)
        flash("we will update you soon.")

    return render_template('contact.html',params=params)


@app.route("/post/<string:post_slug>",methods=['GET'])
def post(post_slug):
    posts=Post.query.filter_by(slug=post_slug).first()
    return render_template('post.html',params=params,post=posts)

@app.route("/edit/<string:sno>",methods=['GET','POST'])
def edit(sno):

    if 'user' in session and session['user']==params['admin_user']:

        if request.method=='POST':
            title=request.form.get("title")
            tagline= request.form.get("tagline")
            slug = request.form.get("slug")
            content = request.form.get("content")
            imgfile= request.form.get("imgfile")


            if sno=="0":
                post=Post(TITLE=title,slug=slug,tag_line=tagline,CONTENT=content,imG_file=imgfile,DATE=datetime.now())
                db.session.add(post)
                db.session.commit()
            else:
                posts=Post.query.filter_by(SNO=int(sno)).first()
                print(posts.tag_line)
                posts.TITLE=title
                posts.slug=slug
                posts.tag_line=tagline
                posts.CONTENT=content
                posts.imG_file=imgfile
                posts.DATE=datetime.now()
                db.session.commit()
                return redirect("/edit/"+sno)
        post=Post.query.filter_by(SNO=int(sno)).first()

        return render_template("edit.html",params=params,post=post,sno=sno)
@app.route("/logout")
def logout():
    session.pop('user')
    return redirect("/dashboard")

@app.route("/delete/<string:sno>",methods=['GET','POST'])
def delete(sno):
    if 'user' in session and session['user'] ==params['admin_user']:
        post=Post.query.filter_by(SNO=sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')


@app.route("/uploader",methods=['GET','POST'])
def uploader():
    if 'user' in session and session['user'] ==params['admin_user']:
        if request.method=='POST':
            f=request.files['file1']
            print(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER']),secure_filename(f.filename))
            return "Uploaded Successfully."

app.run(debug=True)




