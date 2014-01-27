from flask import Flask, jsonify, render_template, request
from random import randint
# from multiprocessing import Manager, Process
import threading
import behavior_gui as behavior

app = Flask(__name__)

controller = None
box = None

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
            'n_trials': controller.n_trials,
            'n_reward': 0    
        }

    
    return jsonify(output)

@app.route("/go",methods=['GET','POST'])
def go():
    global controller
    global box
    # # initialize controller
    if controller == None:
        controller = behavior.BehaviorController()
        controller.stimset_names.append('syl_discrim_v1_stimset_a')
        controller.stimset_names.append('syl_discrim_v1_stimset_b_6')
        controller.load_stimsets()
        box = behavior.BehaviorBox()
        
        t = threading.Thread(target = behavior.run_box, args = (controller, box))
        t.start()
    # behavior_gui.run_box()
    return jsonify({1: 0})

@app.route("/stop",methods=['GET','POST'])
def stop():
    global controller
    global box
    # # initialize controller
    if controller != None:
        controller.task_state = "stop"
    # behavior_gui.run_box()
    return jsonify({1: 0})


if __name__ == "__main__":
    app.debug = True
    app.run()
