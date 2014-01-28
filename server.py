from flask import Flask, jsonify, render_template, request
from random import randint
import json
# from multiprocessing import Manager, Process
import threading
import behavior_gui as behavior

app = Flask(__name__)

controller = None
box = None
thread = None

@app.route("/")
def runner():
    return render_template('index.html')

def rand():
    return randint(2, 100)
@app.route("/data", methods=['GET', 'POST'])
def data():
    global controller
    # if request.method == 'POST':
    #     print request.for
    output = {'n_trials': 0, 'n_reward': 0}
    if controller is not None:
        output = { 
            'box_state': controller.box_state,
            'n_trials': controller.n_trials,
            'n_reward': 0    
        }
    return jsonify(output)

@app.route("/list_sound_cards", methods = ["GET", "POST"])
def list_sound_cards():
    result = box.return_list_of_sound_cards()
    return json.dumps(result)

@app.route("/list_serial_ports", methods = ["GET", "POST"])
def list_serial_ports():
    result = behavior.return_list_of_usb_serial_ports()
    return json.dumps(result)

@app.route("/list_modes", methods = ["GET", "POST"])
def list_modes():
    return json.dumps(behavior.mode_definitions)

@app.route("/set_sound_card", methods = ["GET", "POST"])
def set_sound_card():
    pass

@app.route("/set_serial_port")
def set_serial_port():
    pass

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


    ##### temporary code to configure birdname, stimsets, ext
    controller_ready = controller.ready_to_run()
    if not controller_ready[0]:
        controller.set_bird_name('test')
        controller.mode = 'discrimination'
        controller.stimset_names = []
        controller.stimset_names.append('syl_discrim_v1_stimset_a')
        controller.stimset_names.append('syl_discrim_v1_stimset_b_2')
        controller.load_stimsets()

    box_ready = box.ready_to_run()
    if not box_ready[0]:
        box.select_sound_card()
        box.select_serial_port()


    # check ready state
    controller_ready = controller.ready_to_run()
    if not controller_ready[0]:
        import ipdb; ipdb.set_trace()
        return json.dumps(['failure', 'controller: %s ' % controller_ready[1]]), 400#])
    box_ready = box.ready_to_run()
    if not box_ready[0]:
        return json.dumps(['failure', 'box: %s ' % box_ready[1]]), 400

    # send thread
    thread = threading.Thread(target = behavior.run_box, args = (controller, box))
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
        controller.box_state = "stop"
        thread.join()
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
    controller = behavior.BehaviorController()
    box = behavior.BehaviorBox()  
    app.debug = True
    app.run()
