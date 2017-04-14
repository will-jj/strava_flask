from flask import Flask, redirect, url_for, render_template, flash, make_response, abort,request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from flask import render_template_string
from oauth import OAuthSignIn
import pickle
import stravalib
import os
import uuid
import random
import string
import time
import json
import datetime
from io import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
from celery import Celery, current_task
from celery.result import AsyncResult
app = Flask(__name__)
app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = pickle.load(open('credentials.p', 'rb'))
app.altitude_plot = None
celery = Celery(app.name,
        backend='redis://localhost:6379/0',
        broker='amqp://localhost')
celery.conf.accept_content = ['json', 'msgpack']
celery.conf.result_serializer = 'msgpack'

db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'index'

app.user_token = 'None'

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

@app.route('/simple.png')
def getplot():
    return app.altitude_plot

@celery.task()
def simple(userkey):
    current_task.update_state(state='PROGRESS', meta={'current':0.1})
    current_task.update_state(state='PROGRESS', meta={'current':0.3})
    fig=Figure()
    ax=fig.add_subplot(111)
    client = stravalib.client.Client()
    client.access_token = userkey
    athlete = client.get_athlete()
    # TODO : Make this better
    for activity in client.get_activities(before="3000-01-01T00:00:00Z", limit=1):
        latest_ride = activity

    types = ['distance', 'time', 'latlng', 'altitude', 'heartrate', 'temp', ]
    streams = client.get_activity_streams(latest_ride.id, types=types, resolution='medium')
    y = streams['altitude'].data
    x = streams['distance'].data
    ax.plot(x, y, '-')
    #ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    #fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    current_task.update_state(state='PROGRESS', meta={'current':0.8})
    png_output = BytesIO()
    canvas.print_png(png_output)
    out = png_output.getvalue()
    return out


@app.route('/progress')
def progress():
    jobid = request.values.get('jobid')
    if jobid:
        job = AsyncResult(jobid, app=celery)
        if job.state == 'PROGRESS':
            return json.dumps(dict(
                state = job.state,
                progress = job.result['current'],
            ))
        elif job.state == 'SUCCESS':
            return json.dumps(dict(
                state = job.state,
                progress = 1.0,
            ))
    return '{}'

@app.route('/result.png')
def result():
    jobid = request.values.get('jobid')
    if jobid:
        job = AsyncResult(jobid, app=celery)
        png_output = job.get()
        response = make_response(png_output)
        response.headers['Content-Type'] = 'image/png'
        return response
    else:
        return 404

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inr_ring')
def inr_ring():
    if current_user.is_authenticated:
        job = simple.delay(current_user.access_token)
        return render_template('TIM_PLATE', JOBID=job.id)
    else:
        # abort(404)
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email,imurl,access_token = oauth.callback()
    app.user_token = access_token
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
    app.run(debug=True,port=50001)
