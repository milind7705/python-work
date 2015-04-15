__version__ = '1.2'

import datetime
import getopt
import getpass
import re
import sys

from BeautifulSoup import BeautifulSoup
import mechanize

### 
file_output = './igdforum_' + str(datetime.date.today())

### 
mode_posts_all = False 
mode_owners_exclude = False  # limit posts to ones related to this user

### handle options
try:
	opts, args = getopt.getopt(sys.argv[1:], "ao", ['all', 'owners'])
except getopt.GetoptError:
	sys.exit(2)
for o, a in opts:
	if o in ('-a', '--all'):
		mode_posts_all = True
		file_output = file_output + '_allposts'
	elif o in ('-o', '--owners'):
		mode_owners_exclude = True
		owners_exclude = args
		file_output = file_output + '_' + str('-'.join(owners_exclude))

class Post:
	'a Post class will populate itself with forum info once instanciated with an URI'
	def __init__(self, uri):
		self.title = ''
		self.pinned = ''
		self.status = ''
		self.code = ''
		self.date_open = ''
		self.date_updated = ''
		self.customer = ''
		self.owners = []
		self.uri = 'https://www.ibm.com/developerworks/mydeveloperworks/groups/service/forum/' + uri
		
		# retrieve post html
		br.open(self.uri)
		html = BeautifulSoup(br.response().read())
		
		# extract title
		try:
			self.title = html.find('span', attrs={'class':'forumPostTitle'}).contents[0].encode('utf-8')
		except:
			self.title = 'missing'
			
		# extract pinned status
		if html.find('span', attrs={'class':'forumPinIndicator '}) == None:
			self.pinned = False
		else:
			self.pinned = True
		
		# extract status
		try:
			self.status = re.search('.*\[OPEN\]|.*\[PENDING\]|.*\[ANSWERED\]|.*\[REOPENED\]|.*\[CLOSED\]', self.title, re.IGNORECASE).group()
		except:
			self.status = 'missing'
			
		# extract IMPACT code
		if re.search('\[DTCCI\d*\]', self.title): # if IMPACT code is in post title
			self.code = re.search('\[DTCCI\d*\]', self.title).group()
		else:
			self.code = 'missing'
		
		# remove tags(i.e. [OPEN] [DTCCIxxxx]) from title
		re_title_tags = re.compile(r'\[.*?\]', re.IGNORECASE)
		self.title = re_title_tags.sub('\t', self.title).strip()
		
		# extract open date and last update date
		dates = html.findAll('span', attrs={'class':'formatDate lotusHidden'})    # grab all dates
		self.date_open = dates[0].contents[0].strip()[0:16].replace('T', ' ')     # first date is the date the post was made
		self.date_updated = dates[-1].contents[0].strip()[0:16].replace('T', ' ') # last date is the date the last update was made
		
		# extract customer and owner names
		for name in html.findAll('span', attrs={'class':'fn person lotusPerson'}): # go through all forum user names
			self.owners = self.owners + name.contents                              # and add to a list
		self.customer = self.owners[0]                                             # customer is first name in owner list
		while self.customer in self.owners: self.owners.remove(self.customer)      # remove customer name from owner list
		self.owners = list(set(self.owners))                                       # remove duplicates from owner list
		
	def display_details(self):
		print 'title   : ' + str(self.title)
		print 'status  : ' + str(self.status)
		print 'code    : ' + str(self.code)
		print 'opened  : ' + str(self.date_open)
		print 'updated : ' + str(self.date_updated)
		print 'customer: ' + str(self.customer)
		print 'owners  : ' + ', '.join(map(str, post.owners))
		print 'uri     : ' + str(self.uri)
		print 'pinned  : ' + str(self.pinned)
		print '----------'
		
class IO:
	''
	def export_html(self, posts_tagged, posts_untagged, file_output):
		file = open(file_output + '.html', 'w')
		
		# write header
		file.write('''
<?xml version="1.0" encoding="utf-8"?><!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
<title>IBM SmartCloud Enterprise Forum Summary</title>
<style type="text/css">
body {
	margin: 1em;
	padding: 0;
	line-height: 1.6em;
	font-family: "Lucida Sans Unicode", "Lucida Grande", Sans-Serif;
	font-size: 1em;
	color: #039;
} h2 {
	padding: 0;
}
#hor-minimalist-b {
	font-family: "Lucida Sans Unicode", "Lucida Grande", Sans-Serif;
	font-size: 12px;
	background: #fff;
	margin: 45px;
	width: 95%;
	border-collapse: collapse;
	text-align: left;
} #hor-minimalist-b th {
	font-size: 14px;
	font-weight: normal;
	color: #039;
	padding: 10px 8px;
	border-bottom: 2px solid #6678b1;
} #hor-minimalist-b td {
	border-bottom: 1px solid #ccc;
	color: #669;
	padding: 6px 8px;
} #hor-minimalist-b tbody tr:hover td {
	color: #009;
}
</style>
</head>
<body>
<div>
<h1>IBM SmartCloud Enterprise Forum Summary</h1>
<hr/>
<h2>unhandled</h2>
<table id="hor-minimalist-b">
<tr><th>title</th><th>status</th><th>code</th><th>date opened</th><th>date updated</th><th>customer</th><th>owners</th></tr>
		''')
			
		# write content(untagged)
		for post in posts_untagged:
			file.write('<tr><td><a href="' + str(post.uri) + '">' + str(post.title) + '</a></td><td>' + str(post.status) + '</td><td>' + str(post.code) + '</td><td>' + str(post.date_open) + '</td><td>' + str(post.date_updated) + '</td><td>' + str(post.customer) + '</td><td>' + ', '.join(map(str, post.owners)) + '</td></tr>')
		
		file.write('''
</table>
<hr/>
<h2>handling</h2>
<table id="hor-minimalist-b">
<tr><th>title</th><th>status</th><th>code</th><th>date opened</th><th>date updated</th><th>customer</th><th>owners</th></tr>
		''')
		# write content(tagged)
		for post in posts_tagged:
			file.write('<tr><td><a href="' + str(post.uri) + '">' + str(post.title) + '</a></td><td>' + str(post.status) + '</td><td>' + str(post.code) + '</td><td>' + str(post.date_open) + '</td><td>' + str(post.date_updated) + '</td><td>' + str(post.customer) + '</td><td>' + ', '.join(map(str, post.owners)) + '</td></tr>')
			
		# write footer
		file.write('''
</table>
</div>
</body>
</html>
		''')
		file.close()
		
	def export_csv(self, posts_tagged, postsun_tagged, file_output):
		file = open(file_output + '.csv', 'w')
		
		# write header(untagged)
		file.write('title,status,code,opened,updated,customer,owners,uri\n')
		# write content
		for post in posts_untagged:
			file.write(str(post.title) + ',' + str(post.status) + ',' + str(post.code) + ',' + str(post.date_open) + ',' + str(post.date_updated) + ',' + str(post.customer) + ',' + '/'.join(map(str, post.owners)) + ',' + str(post.uri) + '\n')
		
		# write header(tagged)
		file.write('title,status,code,opened,updated,customer,owners,uri\n')
		# write content
		for post in posts_tagged:
			file.write(str(post.title) + ',' + str(post.status) + ',' + str(post.code) + ',' + str(post.date_open) + ',' + str(post.date_updated) + ',' + str(post.customer) + ',' + '/'.join(map(str, post.owners)) + ',' + str(post.uri) + '\n')
		
# main
if __name__ == "__main__":
	posts_tagged = []
	posts_untagged = []
	
	# 
	print 'IBM SmartCloud Enterprise Forum Summary Generator'
	
	# 
	if mode_posts_all:
		print 'extracting all posts(excluding pinned posts)'
	else:
		print 'extracting all non-[CLOSED] posts(excluding pinned posts)'
	
	if mode_owners_exclude:
		print 'limiting to posts owned by: ' + str(owners_exclude)
	
	# browser
	br = mechanize.Browser()
	br.set_handle_equiv(True)
	br.set_handle_gzip(False)
	br.set_handle_redirect(True)
	br.set_handle_referer(True)
	br.set_handle_robots(False)
	br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1) # Follows refresh 0 but not hangs on refresh > 0
	br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
	#br.set_debug_http(True)
	#br.set_debug_redirects(True)
	#br.set_debug_responses(True)
	
	# The site we will navigate into, handling it's session
	print 'connecting...'
	br.open('https://www.ibm.com/developerworks/dwwi/jsp/WSLogin.jsp') # Main login page
	
	# login
	print 'logging in...'
	login_form = br.select_form(nr=3) # select the 4th form	
	user = raw_input("id: ")
	passw = getpass.getpass("pass: ")
	br.form['j_username'] = user
	br.form['j_password'] = passw
	#br.form['j_username'] = ''
	#br.form['j_password'] = ''
	br.submit() # login
	
	# link traversal to get to the main forum
	br.open('https://www.ibm.com/developerworks/mydeveloperworks/')
	br.open('https://www.ibm.com/developerworks/mydeveloperworks/groups/service/forum/topics?communityUuid=1dba2e59-05da-4b9a-84e4-2444a6cac251')
	br.open('https://www.ibm.com/developerworks/mydeveloperworks/groups/service/forum/topics?communityUuid=1dba2e59-05da-4b9a-84e4-2444a6cac251&ps=1000')
	
	###
	html = BeautifulSoup(br.response().read())
	
	# 
	if mode_posts_all:
		re_post_types = re.compile('.*')
	else:
		re_post_types = re.compile('.*\[OPEN\]|.*\[PENDING\]|.*\[ANSWERED\]|.*\[REOPENED\]', re.IGNORECASE)
		re_post_types_closed = re.compile('.*\[CLOSED\]', re.IGNORECASE)
		
	re_post_uri = re.compile(r'(href="(.*?)")', re.IGNORECASE)
	for post_user in html.findAll('h4'):                                   # look for all post titles
		post_link = str(post_user.findNext('a'))                           # extract link info in <a></a> format from post
		if re_post_types.match(post_link):                                 # if post is [OPEN]
			post = Post(BeautifulSoup(post_link).find('a')['href'])        # extract post link
			
			if post.pinned == False:                                       # 
				if mode_owners_exclude == True:
					if len(set(owners_exclude).intersection(post.owners)) > 0:
						post.display_details()
						posts_tagged.append(post)                              # add to tagged posts list
				else:
					post.display_details()
					posts_tagged.append(post)                              # add to tagged posts list
		
		else:                                                              # if post is not [OPEN]
			if not re_post_types_closed.match(post_link):                  # and if not [CLOSED]
				post = Post(BeautifulSoup(post_link).find('a')['href'])    # extract post link
				
				if post.pinned == False:                                       # 
					if mode_owners_exclude == True:
						if len(set(owners_exclude).intersection(post.owners)) > 0:
							post.display_details()
							posts_untagged.append(post)                              # add to untagged posts list
					else:
						post.display_details()
						posts_untagged.append(post)                              # add to untagged posts list
				
	### export to file
	io = IO()
	print 'writing to  ' + file_output + '.html...',
	io.export_html(posts_tagged, posts_untagged, file_output)
	print ' done'
	print 'writing to ' + file_output + '.csv...',
	io.export_csv(posts_tagged, posts_untagged, file_output)
	print ' done'
	