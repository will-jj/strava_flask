''' Tasks related to our celery functions '''

import time
import random
import datetime
import numpy as np
from io import BytesIO
from celery import Celery, current_task
from celery.result import AsyncResult
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
import stravalib
import json
from python_weather import tcxweather

import configparser

Config = configparser.ConfigParser()
Config.read('config.ini')
ds_api = Config['Authentication']['client_secret']

REDIS_URL = 'redis://redis:6379/0'
BROKER_URL = 'amqp://admin:mypass@rabbit//'

CELERY = Celery('tasks',
                backend=REDIS_URL,
                broker=BROKER_URL)

CELERY.conf.accept_content = ['json', 'msgpack']
CELERY.conf.result_serializer = 'msgpack'

def get_job(job_id):
    '''
    To be called from our web app.
    The job ID is passed and the celery job is returned.
    '''
    return AsyncResult(job_id, app=CELERY)

@CELERY.task()
def simple_json_c():
    x = [1,2,3,4,5]
    y = [3,4,3,2,2]
    jmeme = json.dumps(({'x': x, 'y': y}))
    return jmeme

@CELERY.task()
def celery_json_strava(userkey):
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
    hr = streams['time'].data
    x = np.array(x)
    x = x/1000
    x= np.around(x, decimals=3)
    x = x.tolist()

    #my_list = list()
    #for ii, data in enumerate(y):
    #    my_list.append((x[ii], data))

    jmeme = json.dumps([{'key': ['Distance [km]', 'Altitude [m]'], 'x': x, 'y':y,'hr':hr}])

    return jmeme

@CELERY.task()
def celery_json_weather(userkey, course_id, date):
    current_task.update_state(state='PROGRESS', meta={'current': 0.1})
    client = stravalib.client.Client()
    client.access_token = userkey
    athlete = client.get_athlete()
    route = client.get_route_streams(course_id)
    current_task.update_state(state='PROGRESS', meta={'current': 0.2})
    weather = tcxweather.RideWeather(strava_course=route)
    weather.speed(kph=25)
    weather.set_ride_start_time(unix=date)
    weather.decimate(Points=10)
    current_task.update_state(state='PROGRESS', meta={'current': 0.3})
    weather.get_weather_data(ds_api, fileDirectory='weatherWEB_TEST', fileName='weatherWebTest', units='si')
    current_task.update_state(state='PROGRESS', meta={'current': 0.4})
    weather.get_forecast()
    current_task.update_state(state='PROGRESS', meta={'current': 0.5})
    dist = weather.dist
    #y = route['altitude'].data
    #x = route['distance'].data
    #hr = route['altitude'].data
    app_temp = weather.weather['apparent_temperature']
    rel_wind = weather.weather['rel_wind_bear']
    dist = np.array(dist)
    dist = dist/1000
    dist = np.around(dist, decimals=3)
    dist = dist.tolist()
    wind_speed = weather.weather['wind_speed']
    wind_head = weather.weather['wind_head']
    wind_precip = weather.weather['precip_intensity']
    wind_cross = weather.weather['wind_cross']
    #my_list = list()
    #for ii, data in enumerate(y):
    #    my_list.append((x[ii], data))
    # TODO prepare data ready to dump straight into graph
    jmeme = json.dumps([{'key': ['Distance [km]', 'Apparent Temperature [°C]', 'Rel Wind Bearing [°]',
                                 'Wind Speed [km/h]', 'Head Wind Component [km/h]', 'Cross Wind Component [km/h]',
                                 'Precipitation'],
                         'dist': dist, 'app_temp':app_temp, 'rel_wind':rel_wind, 'wind_speed':wind_speed,
                         'wind_head':wind_head, 'wind_cross':wind_cross, 'wind_precip':wind_precip}])
    return jmeme


@CELERY.task()
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
    ax.set_title('{name} lives in {city}, {key}'.format(name=athlete.city,city=athlete.city,key=userkey))
    #ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    #fig.autofmt_xdate()
    canvas=FigureCanvas(fig)
    current_task.update_state(state='PROGRESS', meta={'current':0.8})
    png_output = BytesIO()
    canvas.print_png(png_output)
    out = png_output.getvalue()
    return out



@CELERY.task()
def get_data_from_strava():
    '''
    Generate a random image.
    A sleep makes this task take artifically longer.
    '''
    current_task.update_state(state='PROGRESS', meta={'current':0.1})
    time.sleep(2)
    current_task.update_state(state='PROGRESS', meta={'current':0.3})
    fig = Figure()
    ax_handle = fig.add_subplot(111)
    x_axis = []
    y_axis = []
    now = datetime.datetime.now()
    delta = datetime.timedelta(days=1)
    current_task.update_state(state='PROGRESS', meta={'current':0.5})
    for _ in range(10):
        x_axis.append(now)
        now += delta
        y_axis.append(random.randint(0, 1000))
    ax_handle.plot_date(x_axis, y_axis, '-')
    ax_handle.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()
    canvas = FigureCanvas(fig)
    current_task.update_state(state='PROGRESS', meta={'current':0.8})
    png_output = BytesIO()
    canvas.print_png(png_output)
    out = png_output.getvalue()
    return out