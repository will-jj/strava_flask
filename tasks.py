''' Tasks related to our celery functions '''

import time
import random
import datetime

from io import BytesIO
from celery import Celery, current_task
from celery.result import AsyncResult
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.dates import DateFormatter
import stravalib
import json
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