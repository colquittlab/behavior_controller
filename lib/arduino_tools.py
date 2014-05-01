from subprocess import call, Popen
import os


def build_and_upload(arduino_port):
	o_cwd = os.getcwd()
	print "o_cdw: %s" % o_cwd

	ino_project_dir = o_cwd + '/arduino_code/ino_project'
	arduino_ide_dir = o_cwd + '/arduino_ide/'
	os.chdir(ino_project_dir)
	code = call(['ino', 'clean'])
	code = call(['ino', 'build', '-d' + arduino_ide_dir])
	code = call(['ino', 'upload', '-d' + arduino_ide_dir, '-p' + arduino_port]) 
	os.chdir(o_cwd)

if __name__=='__main__':
	build_and_upload('/dev/arduino_1')