from flask import Flask, redirect, url_for, render_template, flash, make_response, abort,request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from flask import render_template_string
from oauth import OAuthSignIn
import pickle

import json
import tasks

APP = Flask(__name__)
APP.config['SECRET_KEY'] = 'top secret!'
APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
APP.config['OAUTH_CREDENTIALS'] = pickle.load(open('credentials.p', 'rb'))
APP.altitude_plot = None

db = SQLAlchemy(APP)
lm = LoginManager(APP)
lm.login_view = 'index'

APP.user_token = 'None'

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=True)
    imurl = db.Column(db.String(64), nullable=True)
    access_token = db.Column(db.String(64), nullable=True)

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@APP.route('/progress')
def progress():
    '''
    Get the progress of our task and return it using a JSON object
    '''
    jobid = request.values.get('jobid')
    if jobid:
        job = tasks.get_job(jobid)
        if job.state == 'PROGRESS':
            return json.dumps(dict(
                state=job.state,
                progress=job.result['current'],
            ))
        elif job.state == 'SUCCESS':
            return json.dumps(dict(
                state=job.state,
                progress=1.0,
            ))
    return '{}'

@APP.route('/result.png')
def result():
    '''
    Pull our generated .png binary from redis and return it
    '''
    jobid = request.values.get('jobid')
    if jobid:
        job = tasks.get_job(jobid)
        png_output = job.get()
        response = make_response(png_output)
        response.headers['Content-Type'] = 'image/png'
        return response
    else:
        return 404


@APP.route('/')
def index():
    return render_template('index.html')

@APP.route('/inr_ring')
def inr_ring():
    if current_user.is_authenticated:
        job = tasks.simple.delay(current_user.access_token)
        return render_template('TIM_PLATE', JOBID=job.id)
    else:
        # abort(404)
        return redirect(url_for('index'))

@APP.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@APP.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@APP.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email,imurl,access_token = oauth.callback()
    APP.user_token = access_token
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email,imurl=imurl, access_token=access_token)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))


if __name__ == '__main__':
    db.create_all()
    APP.run(host='0.0.0.0')
