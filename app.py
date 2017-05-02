from flask import Flask, redirect, url_for, render_template, flash, make_response, abort, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, \
    current_user
from oauth import OAuthSignIn
import pickle

import tasks
import numpy as np
import stravalib
import json

APP = Flask(__name__)
APP.config['SECRET_KEY'] = 'top secret!'
APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
APP.config['OAUTH_CREDENTIALS'] = pickle.load(open('credentials.p', 'rb'))
APP.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

APP.altitude_plot = None

db = SQLAlchemy(APP)
lm = LoginManager(APP)
lm.login_view = 'index'

APP.user_token = 'None'


def currency(value):
    return "${:,.2f}".format(value)


APP.add_template_filter(currency)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), nullable=True)
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


@APP.route('/start', methods=['POST'])
def get_weather():
    # get url
    data = json.loads(request.data.decode())
    course_id = data["course_id"]
    date = data["date_time"]
    # raise Exception('Wow {} and {}'.format(date,course_id))
    job = tasks.celery_json_weather.delay(current_user.access_token, course_id, date)
    # return created job id
    return job.id

@APP.route('/d3_test')
def d3_test():
    return render_template('d3_test.html')


@APP.route('/nvd3')
def nvd3():
    if current_user.is_authenticated:
        client = stravalib.client.Client()
        client.access_token = current_user.access_token
        routes = client.get_routes()
        routes = list(routes)
        data = list()
        for ride in routes:
            meme = {}
            meme['name'] = ride.name
            meme['id'] = ride.id
            data.append(meme)
        json_data = json.dumps(data)
        return render_template('nvd3_index.html', courses=json_data)
    else:
        return render_template('index.html')

@APP.route('/topojson')
def topojson():
    return jsonify(pickle.load(open('topojson.p', 'rb')))


@APP.route('/get_desired_data', methods=['GET', 'POST'])
def get_desired_data():
    errors = []
    results = {}
    if request.method == "POST":
        # get text that the user has entered
        try:
            data = request.form['thedata']

            results.append(
                "You entered: {0}".format(data))
        except:
            errors.append("srs no data")

    return render_template('get_desired_data.html', errors=errors, results=results)


@APP.route('/results')
def get_results():
    messages = {
        0.1:'Job Started',
        0.2:'Course Stream Acquired',
        0.3:'Gathering Weather Data',
        0.4:'Processing Weather Data',
        0.5:'Packing the Data'}

    jobid = request.args.get('jobid')
    if current_user.is_authenticated:
        if jobid:
            job = tasks.get_job(jobid)
            # raise Exception('{}'.format(job.state))
            if job.state == 'SUCCESS':
                output = job.get()

                return (output)
            elif job.state == 'PROGRESS':
                return messages[job.result['current']], 202
            elif job.state == 'PENDING':
                return "Pending", 202
            else:
                return "unknown", 202
        else:
            return "No", 202
    else:
        return "Nay!", 404


def simple_json_strava(userkey):
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
    my_list = list()
    for ii, data in enumerate(y):
        my_list.append((x[ii], data))

    jmeme = json.dumps([{'key': 'Altitude', 'values': my_list}])

    return jmeme


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


@APP.route('/test2')
def test2():
    if current_user.is_authenticated:

        json_array = simple_json_strava(current_user.access_token)
        # json_array = simple_json_2()

        return render_template('strava_plot.html', test_data=json_array)
    else:
        return redirect(url_for('index'))


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



@APP.route('/key')
def keypage():
    if current_user.is_authenticated:

        return render_template('keypage.html', key=current_user.access_token)
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
    id, email, access_token = oauth.callback()
    APP.user_token = access_token
    if id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(id=id).first()
    if not user:
        user = User(id=id, email=email, access_token=access_token)
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))


if __name__ == '__main__':
    db.create_all()
    APP.run(host='0.0.0.0')
