import json
from scipy import io as sio
import numpy as np
from numpy import array


def _decode_list(data):
	rv = []
	for item in data:
	    if isinstance(item, unicode):
	        item = item.encode('utf-8')
	    elif isinstance(item, list):
	        item = _decode_list(item)
	    elif isinstance(item, dict):
	        item = _decode_dict(item)
	    rv.append(item)
	return rv

def _decode_dict(data):
	rv = {}
	for key, value in data.iteritems():
	    if isinstance(key, unicode):
	        key = key.encode('utf-8')
	    if isinstance(value, unicode):
	        value = value.encode('utf-8')
	    elif isinstance(value, list):
	        value = _decode_list(value)
	    elif isinstance(value, dict):
	        value = _decode_dict(value)
	    rv[key] = value
	return rv

def load_trials_and_save_mat(fname):
	fid = open(fname)
	trials = []
	for line in fid:
		trials.append(json.loads(line, object_hook = _decode_dict))
	data = {'trials': np.array(trials)}
	sio.savemat('test.mat', data)


if __name__ == '__main__':
	fname = "/Users/jknowles/data/doupe_lab/behavior/orange4white29_20140214_0.trial"
	import cProfile, runsnakerun
	data = cProfile.runctx('load_trials_and_save_mat(fname)', globals(), locals())#, filename='/Users/jknowles/data/temp/profile.test')
	
	import ipdb; ipdb.set_trace()

