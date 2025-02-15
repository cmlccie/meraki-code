"""
Cisco Meraki Captive Portal simulator

Default port: 5003

Matt DeNapoli

2018

https://developer.cisco.com/site/Meraki
"""

# Libraries
from flask import Flask, request, render_template, redirect, url_for, Response
import random
from datetime import datetime
import time
import requests
import webview
import netifaces as nif
import threading
import json

app = Flask(__name__)

# Globals
global captive_portal_url
captive_portal_url = ""
global user_continue_url
user_continue_url = ""
global window
window = ""
global splash_logins
splash_logins = []

@app.route("/organizations", methods=["GET"])
def get_org_id():
    resp = Response(response=json.dumps([
    {
        "id": "1234567",
        "name": "Simulated Organization"
    }]), headers={"Content-type":"application/json"} )
    return resp

@app.route("/organizations/1234567/networks", methods=["GET"])
def get_network_id():
    resp = Response(response=json.dumps([
    {
        "id": "L_12345678910",
        "organizationId": "1234567",
        "name": "Simulated Network",
        "timeZone": "America/New_York",
        "tags": "",
        "productTypes": [
            "appliance",
            "switch",
            "wireless"
        ],
        "type": "combined",
        "disableMyMerakiCom": False,
        "disableRemoteStatusPage": True
    }
    ]), headers={"Content-type":"application/json"} )
    return resp

@app.route("/networks/L_12345678910/ssids/0", methods=["PUT"])
def put_ssid():
    resp = Response(response=json.dumps(request.json), headers={"Content-type":"application/json"} )
    return resp

@app.route("/networks/L_12345678910/ssids/0/splashSettings", methods=["PUT"])
def put_splash():
    resp = Response(response=json.dumps(request.json), headers={"Content-type":"application/json"} )
    return resp

@app.route("/networks/L_12345678910/splashLoginAttempts", methods=["GET"])
def get_splash_logins():
    global splash_logins

    resp = Response(response=json.dumps(splash_logins), headers={"Content-type":"application/json"} )
    return resp

@app.route("/go", methods=["GET"])
def get_go():
    return render_template("index.html", **locals())

# Kick off simulator and create baseline dataset
@app.route("/connecttowifi", methods=["POST"])
def connect_to_wifi():
    global captive_portal_url
    global user_continue_url
    global splash_logins

    captive_portal_url = request.form["captive_portal_url"]
    base_grant_url = request.host_url + "splash/grant"
    user_continue_url = request.form["user_continue_url"]
    node_mac = generate_fake_mac()
    client_ip = request.remote_addr
    client_mac = generate_fake_mac()
    splashclick_time = datetime.now()
    splashclick_time = datetime.timestamp(splashclick_time)
    full_url = captive_portal_url + \
    "?base_grant_url=" + base_grant_url + \
    "&user_continue_url=" + user_continue_url + \
    "&node_mac=" + node_mac + \
    "&client_ip=" + client_ip + \
    "&client_mac=" + client_mac
    window.load_url(full_url)

    splash_logins.append({
            "name": "Simulated Client",
            "login": "simulatedclient@meraki.com",
            "ssid": "Simulated SSID",
            "loginAt": splashclick_time,
            "gatewayDeviceMac": node_mac,
            "clientMac": client_mac,
            "clientId": client_ip,
            "authorization": "success"
        })

    return render_template("connected.html", full_url=full_url)

@app.route("/splash/grant", methods=["GET"])
def continue_to_url():
    return redirect(request.args.get("continue_url"), code=302)

def generate_fake_mac():
    fake_mac = ""
    for mac_part in range(6):
        fake_mac += "".join(
            random.choice("0123456789abcdef") for i in range(2)
        )
        if mac_part < 5:
            fake_mac += ":"

    return fake_mac

@app.route("/setupserver", methods=["GET"])
def setupserver():
    return render_template("setupserver.html", serversetupurl=request.host_url
    + "go")

def start_server():
    app.run(host="0.0.0.0", threaded=True, port=5003, debug=False)

if __name__ == "__main__":
    t = threading.Thread(target = start_server)
    t.dameon = True
    t.start()

    window = webview.create_window("Captive Portal", "http://localhost:5003/setupserver",
    js_api=None, width=800, height=600, resizable=True, fullscreen=False,
    min_size=(200, 100), confirm_close=False,
    background_color='#FFF', text_select=True)
    webview.start()
