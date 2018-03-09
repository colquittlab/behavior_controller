from subprocess import call, Popen
import os
import time

#<<<<<<< HEAD
#<<<<<<< HEAD
#def build_and_upload(arduino_port):
#=======

# Possibly add in arduino_model to config file
#def build_and_upload(arduino_port):
def build_and_upload(arduino_port, arduino_model):
        arduino_model = 'nano328'
#>>>>>>> jack
#=======

def build_and_upload(arduino_port, arduino_model = "nano328"):
#>>>>>>> 41fc98045440759a7b56910c5370cb502c79c71f
	o_cwd = os.getcwd()
	ino_project_dir = o_cwd + '/arduino_code/ino_project'
	arduino_ide_dir = o_cwd + '/arduino_ide/'
	os.chdir(ino_project_dir)
	code = call(['ino', 'clean'])
#<<<<<<< HEAD
        code = call(['ino', 'build', '-d' + arduino_ide_dir, '-m' + arduino_model])
        code = call(['ino', 'upload', '-d' + arduino_ide_dir, '-p' + arduino_port, '-m' + arduino_model])
#=======
	#code = call(['ino', 'build', '-d' + arduino_ide_dir, '-m', arduino_model])
	#code = call(['ino', 'upload', '-d' + arduino_ide_dir, '-p' + arduino_port, '-m', arduino_model]) 
#>>>>>>> 41fc98045440759a7b56910c5370cb502c79c71f
	# code = call(['ino', 'serial', '-p'+arduino_port, '-b 19200'])
	os.chdir(o_cwd)
	time.sleep(4)


if __name__=='__main__':
        build_and_upload('/dev/arduino_1')

