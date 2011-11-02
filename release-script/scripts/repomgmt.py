# This scipt is used to help release manager to automate the
# the release process by aiding in creation of tags or branches 
# and release notes all read from the properties configuration 
# file (repo.conf).
#
# Author: Nataraj M Basappa (nataraj.basappa@sceneric.com)
# Creation Date: 24th December 2010
# Modified Date: 05th January 2011

import sys, os 
import getopt, getpass
import pysvn 
from pysvn import opt_revision_kind
from configobj import ConfigObj as confobj

class RepoMgmt:

	def __init__(self, cfile, branch, username):
		# Constants
		self.username = username
		self.password = None		
		self.log = None		
		self.is_branch = branch		
		self.client = pysvn.Client()	

		self.cobj = confobj(cfile)
		self.project = self.cobj['Project']
		self.release = self.cobj['Release']
		self.branch = self.cobj['Branch']

	def main(self):
		if self.is_branch:
			self.create_branch()
		else:
			self.create_tag()

	def svn_setup(self):
		self.client.set_default_username(self.username)
		self.client.set_default_password(self.password)
		self.client.callback_get_log_message = self.svn_log_message

	def svn_create(self, src, dest):
		self.client.copy(src, dest, src_revision=pysvn.Revision(opt_revision_kind.head))

	def svn_delete(self, src):
		try:
			self.client.remove(src)
		except pysvn.ClientError, e:
			if str(e) == "URL '"+ src +"' does not exist":
				return
			else:
				print str(e)
				print "Failed to delete build tag\n"

	def svn_log_message(self):
		return True, self.log	

	def svn_notify(self, event_dict):
		return

	def create_tag(self):
		if self.release['from'].lower() == 'trunk':
			src = self.project['root']+'/'+self.release['from'].lower()
		else:
			src = self.project['root']+'/branches/'+self.release['from'].lower()

		self.log = 'Creating tag '+self.release['name']
		dest = self.project['root']+'/tags/'+self.release['name']

		#print src+'\n'+dest+'\n'+self.log
		self.create('tag', src, dest)

	def create_branch(self):
		if self.branch['from'].lower() == 'trunk':
			src = self.project['root']+'/'+self.branch['from']
		else:
			src = self.project['root']+'/branches/'+self.branch['from']

		self.log = 'Creating branch '+self.branch['name']
		dest = self.project['root']+'/branches/'+self.branch['name']
		
		#print src+'\n'+dest+'\n'+self.log
		self.create('branch', src, dest)

	def create(self, action, src, dest):

		is_buildTag = False
		if not self.is_branch:
			if len(self.release['build']) > 0:
				build_dest = self.project['root']+'/tags/'+self.release['build']
				is_buildTag = True		

		output = sys.stdout
		output.write(	
		"**************************************************************************\n"                                   
		"Project: %s\n"
		"**************************************************************************\n"                                   
		"Please verify following details before continuing\n"
		"\n"
		"Creating %s: %s\n"
		"From: %s\n"
		"Log: %s\n"
		"SVN user: %s\n"
		% (self.project['name'], action, dest, src, self.log, self.username))	
		if is_buildTag:
			output.write("Build tag: %s\n"
				     "\n" %(build_dest))
		else:
			print # print empty line
		choice = raw_input("Press 'y' to proceed anything else to exit: ")

		if choice!='y':
			sys.exit(0)

		counter = 0	
		while True:
			self.password = getpass.getpass("SVN password for "+self.username+": ")
			print"\nplease wait..."
			try:			
				self.svn_setup()
				self.svn_create(src,dest)
				if is_buildTag:	
					# Resetting log
					self.log = 'Removing old build tag'
					self.svn_setup()					
					self.svn_delete(build_dest)					
					self.log = 'Creating build tag '+self.release['name']
					self.svn_setup()
					self.svn_create(src,build_dest)
					
				output.write(
				"Done creating %s.\n" %(action))
				break
			except pysvn.ClientError, e:
				if counter < 2 and str(e) == 'callback_get_login required':
					print '\nIncorrect SVN password'
					counter = counter + 1		
				elif str(e).find('already exists') != -1:
					print '\n%s %s already exists update your conf file before running again' % (action, self.branch['name'] if self.is_branch else self.release['name'])
					break
				else:
					print '\nToo many attempts quitting!\n'
					break
def usage(exit):
	if exit:
		output = sys.stderr
	else:
		output = sys.stdout

	output.write(
	"Usage: %s [OPTION]... username...\n"
	"Creates a tag or branch using the username supplied, reads the configuration from\n"
	"default configuration (repo.conf) file under current folder.\n"
	"\n"
	"-c, --conf	Path to configuration file.\n"
	"-b, --branch	Create a branch.\n"
	"-h, --help	Displays this help and exit.\n"
	"\n"
	% (sys.argv[0]))

	sys.exit(exit)

if __name__ == '__main__':

	# Config file
	cfile = 'repo.conf'
	branch = False

	# Check command options
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hcb', ['help','conf','branch'])
	except getopt.GetoptError, err:
        	print str(err) # will print something like "option -z not recognized"
        	usage(2)
    
    	for opt, value in opts:
		if opt in ('-h', '--help'):
            		usage(0)
		elif opt in ('-c','--conf'):
			cfile = value
		elif opt in ('-b','--branch'):
			branch = True	
        	else:
            		assert False, "unhandled option"
	
	# Check command arguments
	if len(args) < 1:
		usage(2)
	else:
		repoMgmt = RepoMgmt(cfile, branch, args[0])
		repoMgmt.main()
