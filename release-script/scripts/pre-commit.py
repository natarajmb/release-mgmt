#!/usr/bin/python
# This scipt is used for as an pre commit checker for svn commits
# it identifies the log message and rejects the transaction if it 
# doen't meet the required criteria defined in a configration file
#
# Author: Nataraj M Basappa (nataraj.basappa@sceneric.com)
# Creation Date: 12th Feburary 2011
# Modified Date: 14th March 2011

import sys, getopt
import pysvn, re
from configobj import ConfigObj as confobj

# Script variables
cobj = confobj('pre-commit.conf')

def main(path_to_repo, transaction_name):
	transaction = pysvn.Transaction(path_to_repo, transaction_name)
	log_msg = transaction.revpropget('svn:log')
	log_conf = cobj['Log']
	paths = log_conf['path']	
	prefixs = log_conf['prefix']
	empty_body = log_conf['empty_body']

	# NOT NEEDED
	# Clubing project with root path
	# path_to_project = [] 
	# for temp in project_paths: 
	#	path_to_project.append(repo_root+"/"+temp)

	# Creating map with project and code prefix
	projects_prefix = dict(zip(paths,prefixs))

	# Creating map with project and empty comment allowed
	projects_empty_comment = dict(zip(paths,empty_body))

	#sys.stderr.write("Prefix : %s\n" % (projects_prefix))
	#sys.stderr.write("Empty : %s\n" % (projects_empty_comment))		

	changes = transaction.changed()
	for path in changes:
		project = path[:path.index("/")]
		prefix = projects_prefix[project]
		empty_allowed = projects_empty_comment[project]
		if prefix != None:
			pattern = re.compile(prefix,re.IGNORECASE) 
			#sys.stderr.write("\nSource - %s ; Prefix - %s" %(log_msg.split(':',1)[0],prefix))
			match = pattern.match(log_msg.split(':',1)[0])
			if match == None:
				sys.stderr.write("Commit message should match the prefix %s\n" %(prefix))
				sys.exit(1)		
		
		if empty_allowed == None or empty_allowed.lower() == "no":
			#sys.stderr.write("\nSource - %s ; Empty - %s" %(log_msg.split(':',1)[1],empty_allowed))
			pattern = re.compile("\s*(\w+)",re.IGNORECASE) 
			if prefix == None:
				match = pattern.match(log_msg)
			else:			
				match = pattern.match(log_msg.split(':',1)[1])

			if match == None:
				sys.stderr.write("Commit message can't be emtpy\n")
				sys.exit(1)		
	sys.exit(0)	

if __name__ == '__main__':
	# This script is called by svn with two arguments
	# 1. path to repository 
        # 2. transction name 
	opts, args = getopt.getopt(sys.argv[1:], '')
	main(args[0],args[1])
