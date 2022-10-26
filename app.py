import logging
import sys
import time
import ldclient
from ldclient.config import Config
import redis
from flask import (Flask, abort, jsonify, make_response, render_template,
                   request, url_for)

root = logging.getLogger()
root.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

r = redis.StrictRedis(host='localhost', port=6379, db=0)
ldclient.set_config(Config('project_server_sdk_key'))

app = Flask(__name__)


# resource stored in memory
flavors = [
    {
        'id': 1,
        'name': u'Chocolate',
        'stock': 150
    },
    {
        'id': 2,
        'name': u'Banana',
        'stock': 400
    },
    {
        'id': 3,
        'name': u'Chocolate Chip',
        'stock': 250
    }
]

# get rate limit (x per minute) from feature flag and enforce it
# returns a dict containing rate limit values for response and a flag if
# the limit has been exceeded


def limit_requests():
    ip = request.remote_addr
    limit = ldclient.get().variation('api-rate-limiter',
                                     {'key': request.method, 'ip': ip}, False)
    t = int(time.time())
    key = ip + request.method + str(t / 60)
    current = r.get(key)
    if current is None:
        current = 0
    header_values = {'429': False, 'limit': limit,
                     'remaining': limit - int(current) - 1, 'reset': 60 - t % 60}
    if int(current) >= limit:
        header_values['429'] = True
    else:
        p = r.pipeline()
        p.incr(key, 1)
        p.expire(key, 60)
        p.execute()
    return header_values

# check feature flag for write permission


def has_write_permission():
    ip = request.remote_addr
    return ldclient.get().variation('api-write-permission', {'key': ip, 'ip': ip}, False)

# make the API traversable


def convert_id_to_uri(flavor):
    new_flavor = {}
    for field in flavor:
        if field == 'id':
            new_flavor['uri'] = url_for('get_flavor', name=flavor[
                'name'], _external=True)
        else:
            new_flavor[field] = flavor[field]
    return new_flavor

# create a response with configured mimetype and headers


def create_response(dat, header_values):
    resp = make_response(dat)
    resp.mimetype = 'application/json'
    resp.headers['X-Rate-Limit-Limit'] = header_values.get('limit')
    resp.headers['X-Rate-Limit-Remaining'] = header_values.get('remaining')
    resp.headers['X-Rate-Limit-Reset'] = header_values.get('reset')
    return resp

# get all flavors


@app.route('/api/v1/flavors', methods=['GET'])
def get_flavors():
    header_values = limit_requests()
    if header_values.get('429'):
        return render_template('429.html',
                               limit=header_values.get('limit'),
                               interval='minute',
                               reset=header_values.get('reset'))
    if len(flavors) == 0:
        abort(404)
    dat = jsonify({'flavors': map(convert_id_to_uri, flavors)})
    return create_response(dat, header_values)

# get a flavor


@app.route('/api/v1/flavors/<string:name>', methods=['GET'])
def get_flavor(name):
    header_values = limit_requests()
    if header_values.get('429'):
        return render_template('429.html',
                               limit=header_values.get('limit'),
                               interval='minute',
                               reset=header_values.get('reset'))
    flavor = [flavor for flavor in flavors if name.lower() == flavor[
        'name'].lower()]
    if len(flavor) == 0:
        abort(404)
    dat = jsonify({'flavor': convert_id_to_uri(flavor[0])})
    return create_response(dat, header_values)

# create a flavor


@app.route('/api/v1/flavors', methods=['POST'])
def create_flavor():
    header_values = limit_requests()
    if header_values.get('429'):
        return render_template('429.html',
                               limit=header_values.get('limit'),
                               interval='minute',
                               reset=header_values.get('reset'))
    if not has_write_permission():
        abort(403)
    name = request.json['name']
    if len([f for f in flavors if f['name'].lower() == name.lower()]) > 0:
        abort(409)
    try:
        flavor = {
            'id': flavors[-1]['id'] + 1,
            'name': request.json['name'],
            'stock': request.json['stock']
        }
    except KeyError:
        abort(400)
    flavors.append(flavor)
    dat = jsonify({'flavor': convert_id_to_uri(flavor)})
    return create_response(dat, header_values)

# modify a flavor


@app.route('/api/v1/flavors/<string:name>', methods=['PUT'])
def update_flavor(name):
    header_values = limit_requests()
    if header_values.get('429'):
        return render_template('429.html',
                               limit=header_values.get('limit'),
                               interval='minute',
                               reset=header_values.get('reset'))
    if not has_write_permission():
        abort(403)
    flavor = [f for f in flavors if f['name'].lower() == name.lower()]
    if len(flavor) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'name' in request.json and not isinstance(request.json['name'], unicode):
        abort(400)
    if 'stock' in request.json and not isinstance(request.json['stock'], int):
        abort(400)
    flavor[0]['name'] = request.json.get('name', flavor[0]['name'])
    flavor[0]['stock'] = request.json.get('stock', flavor[0]['stock'])
    dat = jsonify({'flavor': convert_id_to_uri(flavor[0])})
    return create_response(dat, header_values)

# delete a flavor


@app.route('/api/v1/flavors/<string:name>', methods=['DELETE'])
def delete_flavor(name):
    header_values = limit_requests()
    if header_values.get('429'):
        return render_template('429.html',
                               limit=header_values.get('limit'),
                               interval='minute',
                               reset=header_values.get('reset'))
    if not has_write_permission():
        abort(403)
    flavor = [f for f in flavors if f['name'].lower() == name.lower()]
    if len(flavor) == 0:
        abort(404)
    flavors.remove(flavor[0])
    dat = jsonify({'deleted': True})
    return create_response(dat, header_values)
