from django.http import HttpResponse
from django.template import Context
from django.template.loader import get_template
from django.shortcuts import render
from django.template import RequestContext
from django.shortcuts import render_to_response
import subprocess
import json
from pprint import pprint

from bs4 import BeautifulSoup
import requests
import sys
import re
import urllib2

def search(request):
    	query = request.GET['search']
    	query1 = query.replace(" ", "+")
    	all_prods = list()
    	brands = list()

	f = open("flipkart_raw_data", "w")
	process = subprocess.call(['curl',  '-H', 'Fk-Affiliate-Id:shariffaz', '-H', 'Fk-Affiliate-Token:c569d5da22704c278e90af8226c42174', 'https://affiliate-api.flipkart.net/affiliate/search/json?query=' + query1 + '&resultCount=10'], stdout=f)

	with open('flipkart_raw_data') as data_file:
		data = json.load(data_file)

	for value in data["productInfoList"]:

		prod = dict()

		prodcat = value['productBaseInfo']['productIdentifier']['categoryPaths']['categoryPath'][0][0]['title']
		proddesc = value['productBaseInfo']['productAttributes']['productDescription'];
		prodid = value['productBaseInfo']['productIdentifier']['productId']
		prodtitle = value['productBaseInfo']['productAttributes']['title']
		prodimgurl = value['productBaseInfo']['productAttributes']['imageUrls']['unknown']
		prodmrp = value['productBaseInfo']['productAttributes']['maximumRetailPrice']['amount']
		prodsp = value['productBaseInfo']['productAttributes']['sellingPrice']['amount']
		produrl = value['productBaseInfo']['productAttributes']['productUrl']
		prodbrand = value['productBaseInfo']['productAttributes']['productBrand']

		prod['category'] = prodcat
		prod['id'] = prodid
		prod['proddesc'] = proddesc
		prod['title'] = prodtitle
		prod['imgurl'] = prodimgurl
		prod['mrp'] = prodmrp
		prod['sp'] = prodsp
		prod['url'] = produrl
		prod['brand'] = prodbrand

		all_prods.append(prod.copy())
		request.session['all_flipkart_session'] = all_prods
		sorted_search_prods = all_prods

		if prodbrand not in brands:
			brands.append(prodbrand)
		request.session['brands'] = brands

		seq = [x['sp'] for x in sorted_search_prods]
		min_price = min(seq)
		max_price = max(seq)
		request.session['max_price'] = max_price
		request.session['min_price'] = min_price

	# return render_to_response('search.html', {'query': query}, context_instance=RequestContext(request))
	return render_to_response('search.html', {'allprods': sorted_search_prods, 'brands': brands, 'min_price': min_price, 'max_price': max_price}, context_instance=RequestContext(request))

def compare(request, prodid):

	all_sites_final = list()

	#flipkart array
	flipkart_prod = dict()
	all_flipkart_prods = request.session['all_flipkart_session']
	for i in all_flipkart_prods:
		if i['id'] == prodid:
			flipkart_prod['server'] = "FLIPKART"
			flipkart_prod['title'] = i['title']
			flipkart_prod['price'] = i['sp']
			flipkart_prod['imgurl'] = i['imgurl']
			flipkart_prod['url'] = i['url']
			flipkart_prod['rating'] = "NA"
			request.session['proddesc'] = i['proddesc']
			request.session['prodtitle'] = i['title']
			request.session['prodimage'] = i['imgurl']
			break

	all_sites_final.append(flipkart_prod)

	temptitle = flipkart_prod['title']
	title = temptitle.replace(" ","+")
	price = flipkart_prod['price']
	flipkart_price = int(price)

	# request.session['proddesc'] = proddesc
	# request.session['prodtitle'] = prodtitle
	# request.session['prodimage'] = prodimgurl


	#amazon array
	amazon_minimum = 100000000
	url = "http://www.amazon.in/s/ref=nb_sb_noss_2/278-5943722-6241930?url=search-alias%3Daps&field-keywords=" + title
	page = urllib2.urlopen(url)
	soupe = BeautifulSoup(page, "html.parser")
	amazon_all_links = soupe.find_all("li", class_="s-result-item celwidget")

	final_amazon_prod = dict()

	for i in amazon_all_links:
		amazon_prod = dict()
		try:
			title = i.select('h2.a-text-normal')[0].string
		except:
			title = "NA"
		try:
			price = i.select('div.a-row div.a-span7 div.a-spacing-none a.a-text-normal span')[0].text.encode("utf-8")
		except:
			price = "NA"
		try:
			link = i.select('div.a-col-right div.a-spacing-small a.a-text-normal')[0].get("href")
		except:
			link = "NA"
		try:
			imgurl = i.select('div.a-row div.a-text-center a.a-text-normal img')[0].get("src")
		except:
			imgurl = "NA"
		try:
			rating = i.select('a.a-popover-trigger span.a-icon-alt')[0].text
			if rating.endswith(" out of 5 stars"):
				rating = rating[:-15]
		except:
			rating = "NA"

		amazon_prod['server'] = "AMAZON"
		amazon_prod['title'] = title
		amazon_prod['imgurl'] = imgurl
		amazon_prod['price'] = price
		amazon_prod['url'] = link
		amazon_prod['rating'] = rating

		try:
			amazon_price = price.decode('utf8')
			amazon_price = amazon_price.replace(",","")
			amazon_price = amazon_price.strip()
			amazon_price = int(float(amazon_price))
			if(abs(amazon_price - flipkart_price) < amazon_minimum):
				final_amazon_prod['server'] = "AMAZON"
				final_amazon_prod['title'] = title
				final_amazon_prod['imgurl'] = imgurl
				final_amazon_prod['price'] = price
				final_amazon_prod['url'] = link
				final_amazon_prod['rating'] = rating + " / 5"
				amazon_minimum = abs(amazon_price - flipkart_price)
		except:
			qqq = 1

	all_sites_final.append(final_amazon_prod)

	#snapdeal array
	snapdeal_minimum = 100000000
	title = temptitle.replace(" ","%20")
	url = "http://www.snapdeal.com/search?keyword=" + title + "&noOfResults=48&sort=rlvncy"
	page = urllib2.urlopen(url)
	soupe = BeautifulSoup(page, "html.parser")
	all_links = soupe.find_all("div", class_="col-xs-6 product-tuple-listing js-tuple ")

	final_snapdeal_prod = dict()

	for i in all_links:
		snapdeal_prod = dict()
		try:
			title = i.select('p.product-title')[0].string
		except:
			title = "NA"
		try:
			mrp = i.select('span.product-desc-price.strike')[0].string
		except:
			mrp = "NA"
		try:
			sp = i.select('span.product-price')[0].string
		except:
			sp = "NA"
		try:
			link = i.select('div.product-tuple-image a')[0].get("href")
		except:
			link = "NA"
		try:
			imgurl = i.select('div.product-tuple-image img')[0].get("src")
			if imgurl == None:
				imgurl = i.select('div.product-tuple-image img')[0].get("lazysrc")
		except:
			imgurl = "NA"
		try:
			rating = i.select('div.filled-stars')[0].get("style")[6:8]
		except:
			rating = "NA"

		snapdeal_prod['server'] = "SNAPDEAL"
		snapdeal_prod['title'] = title
		snapdeal_prod['imgurl'] = imgurl
		snapdeal_prod['price'] = sp
		snapdeal_prod['url'] = link
		snapdeal_prod['rating'] = rating

		try:
			snapdeal_price = sp[4:]
			snapdeal_price = snapdeal_price.replace(",","")
			snapdeal_price = snapdeal_price.strip()
			snapdeal_price = int(float(snapdeal_price))
			if(abs(snapdeal_price - flipkart_price) < snapdeal_minimum):
				final_snapdeal_prod['server'] = "SNAPDEAL"
				final_snapdeal_prod['title'] = title
				final_snapdeal_prod['imgurl'] = imgurl
				final_snapdeal_prod['price'] = sp
				final_snapdeal_prod['url'] = link
				final_snapdeal_prod['rating'] = rating + " / 100"
				snapdeal_minimum = abs(snapdeal_price - flipkart_price)
			# all_sites_final.append(snapdeal_prod)
		except:
			qqq = 1

	all_sites_final.append(final_snapdeal_prod)

	#ebay array

	ebay_minimum = 100000000
	title = temptitle.replace(" ","+")
	url = "http://www.ebay.in/sch/i.html?_nkw=" + title
	page = urllib2.urlopen(url)
	soupe = BeautifulSoup(page, "html.parser")
	all_links = soupe.find_all("li", class_="sresult lvresult clearfix li")

	final_ebay_prod = dict()

	for i in all_links:
		ebay_prod = dict()
	    	try:
	        		title = i.select('h3.lvtitle a.vip')[0].text.encode("utf-8").strip()
	    	except:
	        		title = "NA"
	    	try:
	        		mrp = i.select('li.lvprice span.bold')[0].text.encode("utf-8").strip()
	    	except:
	        		mrp = "NA"
	    	try:
	        		link = i.select('h3.lvtitle a.vip')[0].get("href")
	    	except:
	        		link = "NA"
	    	try:
	        		imgurl = i.select('img.img')[0].get("src")
	    	except:
	        		imgurl = "NA"

		ebay_prod['title'] = title
		ebay_prod['imgurl'] = imgurl
		ebay_prod['price'] = mrp
		ebay_prod['url'] = link
		ebay_prod['rating'] = "NA"

		try:
			ebay_price = mrp[4:]
			ebay_price = ebay_price.replace(",","")
			ebay_price = ebay_price.strip()
			ebay_price = int(float(ebay_price))
			if(abs(ebay_price - flipkart_price) < ebay_minimum):
				final_ebay_prod['server'] = "EBAY"
				final_ebay_prod['title'] = title
				final_ebay_prod['imgurl'] = imgurl
				final_ebay_prod['price'] = mrp
				final_ebay_prod['url'] = link
				final_ebay_prod['rating'] = "NA"
				ebay_minimum = abs(ebay_price - flipkart_price)
		except:
			qqq = 1

	all_sites_final.append(final_ebay_prod)

	proddesc = request.session['proddesc']
	prodtitle = request.session['prodtitle']
	prodimgurl = request.session['prodimage']

	request.session['final_compared'] = all_sites_final

	return render_to_response('compare.html', {'allprods': all_sites_final, 'title': prodtitle, 'desc': proddesc, 'imageurl': prodimgurl}, context_instance=RequestContext(request))
	# return render_to_response('compare.html', {'price': snapdeal_price}, context_instance=RequestContext(request))

def sort(request, method):

	all_search_prods = request.session['all_flipkart_session']
	brands = request.session['brands']
	max_price = request.session['max_price']
	min_price = request.session['min_price']

	if method == "relevance":
		sorted_search_prods = all_search_prods
		return render_to_response('sort.html', {'allprods': sorted_search_prods, 'brands': brands, 'min_price': min_price, 'max_price': max_price, 'method': 'relevance'}, context_instance=RequestContext(request))
	if method == "lowtohigh":
		sorted_search_prods = sorted(all_search_prods, key=lambda k: k['sp'])
		return render_to_response('sort.html', {'allprods': sorted_search_prods, 'brands': brands, 'min_price': min_price, 'max_price': max_price, 'method': 'lowtohigh'}, context_instance=RequestContext(request))
	if method == "hightolow":
		sorted_search_prods = sorted(all_search_prods, key=lambda k: k['sp'], reverse=True)
		return render_to_response('sort.html', {'allprods': sorted_search_prods, 'brands': brands, 'min_price': min_price, 'max_price': max_price, 'method': 'hightolow'}, context_instance=RequestContext(request))

	# return render_to_response('sort.html', {'allprods': sorted_search_prods, 'brands': brands, 'min_price': min_price, 'max_price': max_price}, context_instance=RequestContext(request))

def filterr(request):

	all_search_prods = request.session['all_flipkart_session']
	all_selected_brands = list()
	filtered_prods = list()
	max_price = request.session['max_price']
	min_price = request.session['min_price']

	brands = request.session['brands']
	for i in brands:
		try:
			if request.GET[i]:
				all_selected_brands.append(i)
		except:
			rrr = 1

	max_price_filtered = request.GET['hidden-price']
	request.session['max_price_filtered'] = max_price_filtered

	for i in all_search_prods:
		if i['brand'] in all_selected_brands:
			if i['sp'] <= int(float(max_price_filtered)):
				filtered_prods.append(i)

	request.session['filtered_prods'] = filtered_prods
	request.session['all_selected_brands'] = all_selected_brands

	return render_to_response('filter.html', {'allprods': filtered_prods, 'brands': brands, 'selected_brands': all_selected_brands, 'filtered_price': max_price_filtered, 'min_price': min_price, 'max_price': max_price}, context_instance=RequestContext(request))

def sort_filtered(request, method):

	all_search_prods = request.session['filtered_prods']
	brands = request.session['brands']
	all_selected_brands = request.session['all_selected_brands']
	max_price = request.session['max_price']
	min_price = request.session['min_price']
	max_price_filtered = request.session['max_price_filtered']

	if method == "relevance":
		sorted_search_prods = all_search_prods
		return render_to_response('sort_filtered.html', {'allprods': sorted_search_prods, 'brands': brands, 'all_selected_brands': all_selected_brands, 'filtered_price': max_price_filtered, 'min_price': min_price, 'max_price': max_price, 'method': 'relevance'}, context_instance=RequestContext(request))
	if method == "lowtohigh":
		sorted_search_prods = sorted(all_search_prods, key=lambda k: k['sp'])
		return render_to_response('sort_filtered.html', {'allprods': sorted_search_prods, 'brands': brands, 'all_selected_brands': all_selected_brands, 'filtered_price': max_price_filtered, 'min_price': min_price, 'max_price': max_price, 'method': 'lowtohigh'}, context_instance=RequestContext(request))
	if method == "hightolow":
		sorted_search_prods = sorted(all_search_prods, key=lambda k: k['sp'], reverse=True)
		return render_to_response('sort_filtered.html', {'allprods': sorted_search_prods, 'brands': brands, 'all_selected_brands': all_selected_brands, 'filtered_price': max_price_filtered,'min_price': min_price, 'max_price': max_price, 'method': 'hightolow'}, context_instance=RequestContext(request))

def deals(request):

	f = open("deals_data", "w")
	process = subprocess.call(['curl',  '-H', 'Fk-Affiliate-Id:shariffaz', '-H', 'Fk-Affiliate-Token:c569d5da22704c278e90af8226c42174', 'https://affiliate-api.flipkart.net/affiliate/offers/v1/dotd/json'], stdout=f)

	with open('deals_data') as data_file:
		data = json.load(data_file)

	all_deals = list()

	for value in data["dotdList"]:
		deal = dict()
		deal['title'] = value['title'] + " on " + value['description'];
		deal['produrl'] = value['url'];
		deal['imgurl'] = value['imageUrls'][0]['url'];
		all_deals.append(deal.copy())

	return render_to_response('deals.html', {'all_deals' : all_deals}, context_instance=RequestContext(request))

def flip_delivery(request):
	all_sites_final = request.session['final_compared']
	flipkart_link = all_sites_final[0]['url']

	page = urllib2.urlopen(flipkart_link)
	soupe = BeautifulSoup(page, "html.parser")
	del_date = soupe.find_all("ul", class_="fk-ul-disc")

	return HttpResponse(del_date[3].select("li")[0].string)

def amazon_delivery(request):
	# all_sites_final = request.session['final_compared']
	# amazon_link = all_sites_final[1]['url']

	# page = urllib2.urlopen(amazon_link)
	# soupe = BeautifulSoup(page, "html.parser")
	# del_date = soupe.find_all("span",id_="ddmShippingMessage")
	return HttpResponse("NA")

def snapdeal_delivery(request):
	all_sites_final = request.session['final_compared']
	snapdeal_link = all_sites_final[2]['url']

	page = urllib2.urlopen(snapdeal_link)
	soupe = BeautifulSoup(page, "html.parser")
	del_date = soupe.find_all("div", class_="check-avail-pin-info")

	for i in del_date:
		return HttpResponse(i.select("p")[0].text)

def ebay_delivery(request):
	# page = urllib2.urlopen(ebay_link)
	# soupe = BeautifulSoup(page, "html.parser")
	# del_date = soupe.find_all("span", class_="estimated-date")

	return HttpResponse("NA")
