from flask import Flask, redirect, url_for, render_template, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user,\
    current_user
from oauth import OAuthSignIn
import pickle
import stravalib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'top secret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = pickle.load(open('credentials.p', 'rb'))

db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'index'


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
def simple():

    if current_user.is_authenticated:
        import datetime
        try:
            from StringIO import StringIO
        except ImportError:
            from io import BytesIO
        import random
        import matplotlib.pyplot as plt

        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
        from matplotlib.figure import Figure
        from matplotlib.dates import DateFormatter
        client = stravalib.client.Client()
        client.access_token = current_user.access_token
        athlete = client.get_athlete()
        # TODO : Make this better
        for activity in client.get_activities(before="3000-01-01T00:00:00Z", limit=1):
            latest_ride = activity

        types = ['distance', 'time', 'latlng', 'altitude', 'heartrate', 'temp', ]
        streams = client.get_activity_streams(latest_ride.id, types=types, resolution='medium')
        y = streams['altitude'].data
        x = streams['distance'].data
        fig=Figure()
        ax=fig.add_subplot(111)
        ax.plot(x,y)
        ax.set_title('Keri\'s last ride')
        ax.set_xlabel('Distance [m]')
        ax.set_ylabel('Altitude [m]')
        canvas=FigureCanvas(fig)
        png_output = BytesIO()
        canvas.print_png(png_output)
        response=make_response(png_output.getvalue())
        response.headers['Content-Type'] = 'image/png'
    else:
        response = 'error'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/inr_ring')
def inr_ring():
    client = stravalib.Client()
    client.access_token = current_user.access_token
    athlete = client.get_athlete()
    message = 'For {id}, I now have an access token {token}'.format(id=athlete.firstname, token=current_user.access_token)

    return render_template('inr_rng.html', string_variable=message)

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
