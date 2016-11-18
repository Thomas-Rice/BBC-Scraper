import urllib2
from urllib2 import urlopen
from bs4 import BeautifulSoup, NavigableString
import re
import pymysql
import os
import unittest
import sys
# import cookielib
# from cookielib import CookieJar


# # Change the header to make it look like you are a user instead of a python robot.
# cj = CookieJar()
# opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
# opener.addheaders = [('User-agent', 'Mozilla/5.0')]

pages = set()
title_list = set()

try:
	conn = pymysql.connect(host='127.0.0.1', unix_socket='/tmp/mysql.sock',
						user='root', passwd='root', db='mysql')

	cur = conn.cursor()
	cur.execute("USE scraping")
except:
	print 'Cannot Connect To Server'
	pass




def get_recipie_data():
	html = urlopen("http://www.bbc.co.uk/food/recipes/deepfriedfishinbeerb_67776")
	# html = urlopen('http://www.bbc.co.uk/food/recipes/roastlegoflambwithga_90252')
	bsObj = BeautifulSoup(html.read(), "html.parser")



def getLinks(pageUrl):
	global pages 
	try:
		url = str(pageUrl)
		if not url.startswith('/'):
			url = ('/' + url)

		# print "http://www.bbc.co.uk" + url
		html = urlopen("http://www.bbc.co.uk" + url)
		bsObj = BeautifulSoup(html.read(), "html.parser")
		# Return the object
		return bsObj
	except RuntimeError as e:

		print '''****************************** ERROR Start ***************************************'''
		print 'Recursion Error!!'
		print '''****************************** ERROR End ***************************************'''
	except Exception as e:
		print '''****************************** ERROR Start ***************************************'''
		print 'We have failed at opening the page for this reason' , e
		print 'The page we are trying to open is:', "http://www.bbc.co.uk" + pageUrl
		print '''****************************** ERROR End ***************************************'''


def steal_And_Insert_Data(bsObject):
	bsObj = bsObject
	try:
		Title, iterator = title(bsObj)
		#Because we have to return something to the iterator variable, the 1 signals that we should skip the operations below
		if iterator != 1:
			store_image(bsObj, Title, iterator)
			metadata(bsObj, iterator)
			methods(bsObj, iterator)
			ingredients(bsObj, iterator)

	#Break out of the loop if we cannot get a title
	except AttributeError as i:
		i = str(i)
		if 'NoneType' in i:
			print 'Cannot find a recipie title therefore skipping'
		else:
			print 'Attr error in title that is not'
			print i
		pass
	except Exception as e:
		print '''****************************** ERROR Start ***************************************'''
		print 'steal and insert error'
		print e
		print '''****************************** ERROR End ***************************************'''
		pass


def recurse_through_links(pageHref):
	global pages
	link_object = getLinks(pageHref)
	steal_And_Insert_Data(link_object)
	try:
		for link in link_object.findAll("a", href=re.compile("^(/food/)")):
			# print link
			if 'href' in link.attrs:
				href = (link.attrs['href'])
				if href not in pages:
					# We have encountered a new page
					print 'href is' ,href
					pages.add(href)
					print "\n\n\n"
					recurse_through_links(href)
	except:
		print 'Skipping the recurse_through_links loop due it cannot do findall on the object'
		pass

def title(bsObj):
	global title_list
	'''****************************** Title ***************************************'''
	iterator = None 
	title_obj = bsObj.find('h1',{"class": "content-title__text"})
	Title = title_obj.get_text().encode("utf-8")
	if isinstance(Title, basestring) and Title not in title_list:
		# print 'title is...' , Title
		title_list.add(Title)
		iterator = input_title_to_database(Title)
	else:
		print 'We have already got this recipie so skipping'

	#This is to make sure that if we do not get a title then we return a 1 to signal that the other operations should be skipped.
	if iterator == None:
		iterator = 1

	return Title, iterator


def metadata(bsObj, iterator):
	'''****************************** Metadata ***************************************'''
	tmp = ['','']
	metadata = bsObj.findAll('div', {"class" : "recipe-metadata-wrap"})
	for section in metadata:
		clean_data = section.findAll(True)
		for item in clean_data:
			if item.attrs['class'][0] == 'recipe-metadata__heading':
				text = item.get_text().encode("utf-8")
				tmp[0] = text

			if item.attrs['class'][0] == 'recipe-metadata__prep-time':
				# print item.get_text()
				text = item.get_text().encode("utf-8")
				tmp[1] = text

			if item.attrs['class'][0] == 'recipe-metadata__cook-time':
				text = item.get_text().encode("utf-8")
				# print item.get_text()
				tmp[1] = text

			if item.attrs['class'][0] == 'recipe-metadata__serving':
				text = item.get_text().encode("utf-8")
				# print item.get_text()
				tmp[1] = text

		input_metadata_to_database(tmp[0], tmp[1], iterator)

def methods(bsObj, iterator):
	'''****************************** Methods ***************************************'''
	
	method = bsObj.findAll("p", {"class": "recipe-method__list-item-text"})

	'''
		0 = Heading
		1 = Sub heading
		2 = Method
	'''
	# if Title not in title_list:
	for step in method:
		# print step.get_text()
		for i in step:
			text = i.encode("utf-8")
		# print m
			input_method_to_database(text, iterator, 1)
	# print 'Inserting into methods'

def store_image(bsObj, title, link):
	#Get image
	image = bsObj.findAll("div", { "class" : "recipe-media" })
	for tag in image:
		# Get Image
		try:
			img = str(tag.find('img')['src'])
			#Make folder to store it in. 
			appendix = str(link) + '_' + title
			directory = '/Users/Tom/Desktop/Python/BBC_Recipies_Scraping/Images/' + appendix
			os.mkdir(directory)
			os.chdir(directory)
			imagefile = open(appendix + '.jpeg', 'wb')
			imagefile.write(urllib2.urlopen(img).read())
			imagefile.close()
			return directory
		except Exception as e:
			print '''****************************** ERROR Start ***************************************'''
			print e
			print 'No Image Found'
			print '''****************************** ERROR End ***************************************'''
			pass

def ingredients(bsObj, iterator):
	'''****************************** Ingredients ***************************************'''
	ingredients = bsObj.findAll('div', {"class" : "recipe-ingredients-wrapper"})
	for item in ingredients:
		clean_Ingredients = item.findAll(True)

		'''
			0 = Heading
			1 = Sub heading
			2 = Ingredient
		'''
		for info in clean_Ingredients:	
			if info.attrs['class'][0] == 'recipe-ingredients__list-item':
				text = info.get_text().encode("utf-8")
				input_ingredients_to_database(text, iterator, 2)

			elif info.attrs['class'][0] == 'recipe-ingredients__heading' :
				text = info.get_text().encode("utf-8")
				input_ingredients_to_database(text, iterator, 0)

			elif info.attrs['class'][0] == 'recipe-ingredients__sub-heading':
				text = info.get_text().encode("utf-8")
				input_ingredients_to_database(text, iterator, 1)

		# print 'Inserting into ingredients'
	return text


def input_title_to_database(one):
	cur.execute("INSERT into titles (title) VALUES (\"{}\")".format(one))
	iterator = cur.lastrowid
	cur.connection.commit()
	# print 'Inserting {} into titles'.format(one)
	return iterator

def input_method_to_database(method, link, heading_type):
	# print "INSERT into methods (method,link, heading_type) VALUES ('{}', '{}', '{}')".format(method,link, heading_type)
	cur.execute("INSERT into methods (method,link, heading_type) VALUES (\"{}\", \"{}\", \"{}\")".format(method,link, heading_type))
	# print 'Inserting {} , {}, {} into methods'.format(method,link, heading_type)
	cur.connection.commit()


def input_ingredients_to_database(ingredient, link, heading_type):
	# print "INSERT into ingredients (ingredient,link, heading_type) VALUES ('{}', '{}', '{}')".format(ingredient,link, heading_type)
	cur.execute("INSERT into ingredients (ingredient,link, heading_type) VALUES (\"{}\", \"{}\", \"{}\")".format(ingredient,link, heading_type))
	# print 'Inserting {} , {}, {} into ingredients'.format(ingredient,link, heading_type)
	cur.connection.commit()

def input_metadata_to_database(metadata_heading, metadata_info, link):
	# print "INSERT into metadata (metadata_heading, metadata_info, link) VALUES (\"{}\", \"{}\", \"{}\")".format(metadata_heading, metadata_info, link)
	cur.execute("INSERT into metadata (metadata_heading, metadata_info, link) VALUES (\"{}\", \"{}\", \"{}\")".format(metadata_heading, metadata_info, link))
	# print 'Inserting {} , {}, {} into metadata'.format(metadata_heading, metadata_info, link)
	cur.connection.commit()

def get_titles_from_database():
	global title_list
	cur.execute("SELECT * FROM titles ") 
	for title in cur.fetchall():
		title_list.add(title[1])
	cur.connection.commit()


'''********************************************************************** DB Utilities ******************************************************************************************'''



def print_tables():
	cur.execute("SELECT * FROM titles ") 
	print 'Titles'
	for title in cur.fetchall():
		print title
	cur.execute("SELECT * FROM methods ") 
	print 'Methods'
	for method in cur.fetchall():
		print method
	cur.execute("SELECT * FROM ingredients ") 
	print 'Ingredients'
	for ingredient in cur.fetchall():
		print ingredient
	cur.execute("SELECT * FROM metadata ") 
	print 'Metadata'
	for data in cur.fetchall():
		print data
	cur.connection.commit()

def clear_tables():
	cur.execute("DELETE FROM titles ")
	cur.execute("ALTER TABLE titles AUTO_INCREMENT = 1 ")
	cur.execute("DELETE FROM methods ") 
	cur.execute("ALTER TABLE methods AUTO_INCREMENT = 1 ")
	cur.execute("DELETE FROM ingredients ") 
	cur.execute("ALTER TABLE ingredients AUTO_INCREMENT = 1 ")
	cur.execute("DELETE FROM metadata ") 
	cur.execute("ALTER TABLE metadata AUTO_INCREMENT = 1 ")
	cur.connection.commit()






'''********************************************************************** Commands To Run ******************************************************************************************'''
sys.setrecursionlimit(1000000000)
get_titles_from_database()
recurse_through_links("/food/recipes/search?page=22&keywords=black")
# clear_tables()
# print_tables()
# get_recipie_data()





''' ********************************** Close Servers *********************** ''' 
cur.close()
conn.close()


''' **********************************  Unit Tests *********************** ''' 

class unit_tests(unittest.TestCase):
	def __init__(self):
		html = urlopen("file:///Users/Tom/Desktop/BBC%20Food%20-%20Recipes%20-%20Fish%20and%20chips.html")
		self.bsObj = BeautifulSoup(html.read(), "html.parser")

	def test_store_image(self):
		directory = store_image(self.bsObj, 'Test_Image_Folder', 11111)
		self.assertTrue(os.path.exists(directory))

	def test_ingredients(self):
		ingredients = ingredients(self.bsObj, 1)
		self.assertTrue()

# if __name__ == '__main__':
# 	UT = unit_tests()
# 	UT.test_store_image()






