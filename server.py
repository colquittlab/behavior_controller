from flask import Flask, jsonify, render_template, request
from random import randint
import json
from multiprocessing import Manager, Process
import threading
import time

import serial_tools as st
import soundout_tools as so
import behavior_controller as behavior

app = Flask(__name__)

# container for all data pertaining to each box
box_dict = {}
def initiate_box(box_name=None):
    global box_dict
    if box_name==None:
        box_name = "box_%d" % (len(box_dict) + 1)
    box_dict[box_name] = {}
    box_dict[box_name]['controller'] = behavior.BehaviorController()
    box_dict[box_name]['box'] = behavior.BehaviorBox()  
    box_dict[box_name]['thread'] = None
    pass

## webapp starts here
@app.route("/")
def runner():
    return render_template('index.html')

@app.route("/data", methods=['GET', 'POST'])
def data():
    global box_dict
    # box_id = response.values['sound']
    # if request.method == 'POST':
    #     print request.for
    output = {'n_trials': 0, 'n_reward': 0}

    return jsonify(output)

@app.route("/new_box", methods=['GET', 'POST'])
def make_new_box():
    initiate_box()
    return 'sucess',200

@app.route("/list_boxes",methods=['GET', 'POST'])
def list_boxes():
    global box_dict
    result = {}
    result['list']=box_dict.keys()
    result['list'].sort(key=lambda item: int(item.split('_')[1]))
    return json.dumps(result),200

@app.route("/list_sound_cards", methods = ["GET", "POST"])
def list_sound_cards():
    result = {}
    result['list'] = box.return_list_of_sound_cards()
    if box.sc_idx is None:
        result['current'] = None
    else: 
        if box.sc_idx < len(result['list']):
            result['current'] = result['list'][box.sc_idx]
        else:
            box.sc_idx = None
            result['current'] = None
    return json.dumps(result)

@app.route("/list_serial_ports", methods = ["GET", "POST"])
def list_serial_ports():
    result = {}
    result['list'] = st.return_list_of_usb_serial_ports()
    # if box.serial_port == 
    return json.dumps(result)

@app.route("/list_modes", methods = ["GET", "POST"])
def list_modes():
    result = {}
    result['list'] = behavior.mode_definitions
    return json.dumps(result), 200

@app.route("/set_sound_card", methods = ["GET", "POST"])
def set_sound_card():
    if 'soundcard_select' in request.values.keys():
        sound_card = request.values['soundcard_select']
    else: return json.dumps('No soundcard provided'), 400

    global box
    cardlist = box.return_list_of_sound_cards()
    # filter card list
    if sound_card in cardlist:
        box.select_sound_card(sound_card)
    else:
        return 'failure: card not in list', 400
    return json.dumps('sound card set to %s' % sound_card), 200

@app.route("/set_serial_port", methods = ["GET", "POST"])
def set_serial_port():
    if 'serialport_select' in request.values.keys():
        serial_port = request.values['serialport_select']
    else: return json.dumps('No soundcard provided'), 400
    serial_port = serial_port.split(',')[0]
    result = box.select_serial_port(serial_port)
    if result:
        return 'sucesss: connected to %s'%serial_port, 200
    else:
        return 'failure: could not connect to %s'%serial_port, 400 

@app.route("/beep", methods = ["GET", "POST"])
def beep():
    global box
    box.beep()
    return 'beep', 200

@app.route("/raise_feeder", methods = ["GET", "POST"])
def raise_feeder():
    global box
    box.feeder_on()
    time.sleep(1)
    box.feeder_off()
    return 'feed test', 200

@app.route("/go",methods=['GET','POST'])
def go():
    global controller
    global box
    global thread
    
    # check that controllers are initialized 
    if controller == None:
        return json.dumps(('failure', 'controller not initialized')), 400
    if box == None: 
        return  json.dumps(('failure', 'box not initialized')), 400
    if controller.box_state == "go":
        return json.dumps(['failure', 'already_running']), 400

    import ipdb; ipdb.set_trace()
    ##### temporary code to configure birdname, stimsets, ext
    controller_ready = controller.ready_to_run()
    if not controller_ready[0]:
        controller.set_bird_name('test')
        controller.mode = 'discrimination'
        controller.stimset_names = []
        controller.stimset_names.append('boc_syl_discrim_v1_stimset_a')
        controller.stimset_names.append('boc_syl_discrim_v1_stimset_b_2')
        controller.load_stimsets()

    box_ready = box.ready_to_run()
    if not box_ready[0]:
        box.select_sound_card()
        box.select_serial_port()

    # check ready state
    controller_ready = controller.ready_to_run()
    if not controller_ready[0]:
        return json.dumps(['failure', 'controller: %s ' % controller_ready[1]]), 400#])
    box_ready = box.ready_to_run()
    if not box_ready[0]:
        return json.dumps(['failure', 'box: %s ' % box_ready[1]]), 400

    # send thread
    # thread = threading.Thread(target = behavior.run_box, args = (controller, box))
    # thread.start()
    thread = Process(target = behavior.run_box, args = (controller, box))
    thread.start()

    # behavior_gui.run_box()
    return json.dumps(['sucess','running']), 200

@app.route("/stop",methods=['GET','POST'])
def stop():
    global controller
    global box
    global thread
    # # initialize controller
    if controller != None and thread != None:
        # controller.box_state = "stop"
        # thread.join()
        # update redis var state='stop'
        pass
    # behavior_gui.run_box()
    return json.dumps(('sucsess'))

@app.route("/reset",methods=['GET','POST'])
def reset():
    global controller
    global box
    global thread

    if controller != None and thread != None:
        controller.box_state = 'stop'
        thread.join()

    controller = behavior.BehaviorController()
    box = behavior.BehaviorBox()
    # # initialize controller
    # behavior_gui.run_box()
    return json.dumps(('sucsess'))



if __name__ == "__main__":
    initiate_box()
    thread = None
    app.debug = True
    app.run()
