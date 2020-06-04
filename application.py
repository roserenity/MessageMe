import os, socketio, json, flask

from os import path
from flask import Flask, render_template, url_for, redirect
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
socketio = SocketIO(app)

def search_to_json(file_name, object_name, key, find):
    with open(file_name) as json_file:
        data = json.load(json_file)
            
        for user in data[object_name]:
            if user[key] == find:
                #if found
                ret_val = 0
                socketio.emit('ret_avail', ret_val)
                return ret_val
       
        return data

def get_json(file_name):
    with open(file_name) as json_file:
        data = json.load(json_file)
    return data

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/message-me")
def home():
    return render_template('home.html')

@app.route("/message-me/<channel>")
def inchannel(channel):
    return render_template('channel.html', channel_name=channel)

@socketio.on('check_un')
def check_un_availability(user_json, methods=['GET', 'POST']):
    data={}
    if path.exists('displaynames.json') and os.stat('displaynames.json').st_size!=0:
        data = search_to_json('displaynames.json', 'users', 'un', user_json['un'])
        if data != 0:
            print(data)
            with open('displaynames.json', 'w') as json_file:
                data['users'].append({
                    'un': str(user_json['un']),
                    'status': 'offline'
                })
                json.dump(data, json_file)
                socketio.emit('ret_avail', 1)
    else:
        #if messageme.txt is empty
        with open('displaynames.json', 'w') as json_file:
            data = {}
            data['users']=[]
            data['users'].append({
                'un': str(user_json['un']),
                'status': 'offline'
            })
            json.dump(data, json_file)
            socketio.emit('ret_avail', 1)

@socketio.on('check_cn')
def check_cn_availability(channel_json, methods=['GET', 'POST']):
    data={}
    if path.exists('channels.json') and os.stat('channels.json').st_size!=0:
        data = search_to_json('channels.json', 'channel', 'cn', channel_json['cn'])
        if data != 0:
            print(data)
            with open('channels.json', 'w') as json_file:
                data['channel'].append({
                    'cn': str(channel_json['cn']),
                    'owner': str(channel_json['owner'])
                })
                json.dump(data, json_file)
                socketio.emit('ret_cn_avail', 1)
                socketio.emit('new_channel_json', data)
    else:
        #if messageme.txt is empty
        with open('channels.json', 'w') as json_file:
            data = {}
            data['channel']=[]
            data['channel'].append({
                'cn': str(channel_json['cn']),
                'owner': str(channel_json['owner'])
            })
            json.dump(data, json_file)
            socketio.emit('ret_cn_avail', 1)
            socketio.emit('new_channel_json', data)

@socketio.on('get_cn')
def get_cn():
    data = get_json('channels.json')
    socketio.emit('new_channel_json', data)

@socketio.on('get_message')
def get_message(channel_name):
    data = get_json('json/'+channel_name+'.json')
    socketio.emit('display_message', (data, channel_name))

@socketio.on('set_message')
def set_message(message_json):
    data={}
    channel_name = 'json/'+message_json['channel']+'.json'
    if path.exists(channel_name) and os.stat(channel_name).st_size!=0:
        with open(channel_name) as json_file:
            data = json.load(json_file)
        with open(channel_name, 'w') as json_file:
            print('length: ' + str(len(data['messages'])))
            if(len(data['messages']) == 100):
                data['messages'].pop(0)
            data['messages'].append({
                'message': message_json['message'],
                'sender': message_json['sender'],
                'date' : message_json['date'],
                'time' : message_json['time'] 
            })
            json.dump(data, json_file)
            socketio.emit('new_message_json', (data, message_json['channel']))
    else:
        with open(channel_name, 'w') as json_file:
            data = {}
            data['messages']=[]
            data['messages'].append({
                'message': message_json['message'],
                'sender': message_json['sender'],
                'date' : message_json['date'],
                'time' : message_json['time'] 
            })
            json.dump(data, json_file)
            socketio.emit('new_message_json', (data, message_json['channel']))

@socketio.on('get_owner')
def get_owner(channel):
    owner = ''
    data = get_json('channels.json')
    for i in data['channel']:
        if(i['cn'] == channel):
            owner = i['owner']
    socketio.emit('set_delete_button', owner)

@socketio.on('delete_channel')
def delete_channel(channel):
    os.remove('json/'+channel['channel']+'.json')
    data_copy = {}
    data_copy['channel']=[]
    data = get_json('channels.json')
    for i in data['channel']:
        if i['cn'] != channel['channel']:
            data_copy['channel'].append(i)
    with open('channels.json', 'w') as json_file:
            json.dump(data_copy, json_file)
    socketio.emit('delete_channel_message', channel['channel'])
    socketio.emit('delete_channel_ret')