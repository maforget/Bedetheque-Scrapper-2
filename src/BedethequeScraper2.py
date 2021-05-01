# -*- coding: utf-8 -*-
#@Name Bedetheque Scraper 2
#@Key Bedetheque2
#@Hook	Books, Editor
#@Image BD2.png
#@Description Search on wwww.bedetheque.com informations about the selected eComics
#
# Bedetheque Scraper 2 - Avril 2021- v 5.4 -> by kiwi13 & maforget
#
# Original work by Franck (c) - revised by Mizio66 (c)
#
# Thanks to atagal, Bert and Bruno for the thorough testing !
#
# You are free to modify, enhance (possibly) and distribute this file, but only if mentioning the (c) part
#
# (C)'2011 Franck (C)'2007-2017 cYo Soft & (C)'2008 DouglasBubbletrousers & (C)'2008 wadegiles & (C)'2010 cbanack & (C)'2017 Mizio66 & (C)'2021 kiwi13 & maforget
#

from __future__ import unicode_literals

import clr, sys, re, os, System
import operator

from datetime import datetime, timedelta
from time import strftime, clock

from urllib import *
from urllib2 import *
from HTMLParser import HTMLParser

clr.AddReference('System')
clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import * 

from System.IO import FileInfo, File
from System.Diagnostics.Process import Start
from System.Net import HttpWebRequest, Cookie, DecompressionMethods
from System.Threading import Thread, ThreadStart

clr.AddReference('System.Drawing')
from System.Drawing import *

from System.Text import StringBuilder

from cYo.Projects.ComicRack.Engine import *

clr.AddReference('System.Xml')
from System.Xml import *
BasicXml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><configuration></configuration>"

CookieContainer = System.Net.CookieContainer()

VERSION = "5.6"

SHOWRENLOG = False
SHOWDBGLOG = False
DBGONOFF = False
DBGLOGMAX = 10000
RENLOGMAX = 10000
LANGENFR = "FR"
TBTags = ""
CBCover = True
CBStatus = True
CBGenre = True
CBNotes = True
CBWeb = True
CBCount = True
CBSynopsys = True
CBImprint = True
CBLetterer = True
CBPrinted = True
CBRating = True
CBISBN = True
CBLanguage = True
CBEditor = True
CBFormat = True
CBColorist = True
CBPenciller = True
CBWriter = True
CBTitle = True
CBSeries = True
CBDefault = False
CBRescrape = False
CBStop = "2"
PopUpEditionForm = False
ARTICLES = "Le,La,Les,L',The"
FORMATARTICLES = True
SUBPATT = " - - "
COUNTOF = True
COUNTFINIE = True
TITLEIT = True
CBCouverture = True
TIMEOUT = "1000"
TIMEOUTS = "7"
TIMEPOPUP = "30"
PadNumber = "0"

########################################
# Nombres auteurs
LAST_FIRST_NAMES_PATTERN = r'(?P<name>[^,]*?), (?P<firstname>[^,]*?)$'
LAST_FIRST_NAMES = re.compile(LAST_FIRST_NAMES_PATTERN)

RAW_STR_PATTERN = r'(?P<deb><[^>]+>?)'
RAW_STR = re.compile(RAW_STR_PATTERN)
########################################

########################################
# Info Serie
SERIE_LIST_PATTERN = r'<a\shref=\"https\:\/\/www.bedetheque.com\/serie-(.*?)\">.*?libelle\">(.*?)\r'

SERIE_LIST_CHECK_PATTERN = r's.ries\strouv.{20,60}?La\srecherche.*?\srenvoie\splus\sde\s500\sdonn'
SERIE_LIST_CHECK = re.compile(SERIE_LIST_CHECK_PATTERN, re.IGNORECASE | re.DOTALL)

SERIE_URL_PATTERN = r'<a\shref=\"(.*?)\">\r\n.{50,60}<span\sclass=\"libelle\">%s</span>'

ALBUM_ID_PATTERN = r'id=\"%s\".*?album-%s(.*?)\.html'
ALBUM_INFO_PATTERN = r'<meta\sname=\"description\"\scontent="(.*?)\"'

SERIE_LANGUE_PATTERN = r'class=\"flag\"/>(.*?)</span>'
SERIE_LANGUE = re.compile(SERIE_LANGUE_PATTERN, re.IGNORECASE)

SERIE_GENRE_PATTERN = r'<span\sclass=\"style\">(.*?)<'
SERIE_GENRE = re.compile(SERIE_GENRE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_RESUME_PATTERN = r'<meta\sname=\"description\"\scontent=\"(.*?)"\s/>'
SERIE_RESUME = re.compile(SERIE_RESUME_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_STATUS_PATTERN = r'<h3>.*?<span><i\sclass=\"icon-info-sign\"></i>(.*?)</span>'
SERIE_STATUS = re.compile(SERIE_STATUS_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_NOTE_PATTERN = r'<p\sclass=\"static\">Note:\s<strong>\s(?P<note>[^<]*?)</strong>'
SERIE_NOTE = re.compile(SERIE_NOTE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_COUNT_PATTERN = r'class=\"icon-book\"></i>\s(\d+)'
SERIE_COUNT = re.compile(SERIE_COUNT_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_COUNT_REAL_PATTERN = r'liste-albums-side(.*?)WIDGET'
SERIE_COUNT_REAL = re.compile(SERIE_COUNT_REAL_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_COUNTOF_PATTERN = r'<label>(.*?)<span'
SERIE_COUNTOF = re.compile(SERIE_COUNTOF_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)					

SERIE_HEADER_PATTERN = r'<div(.+?)<h3>D.tail\sdes'
SERIE_HEADER = re.compile(SERIE_HEADER_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

SERIE_HEADER2_PATTERN = r'<h3(.+?)</p'
SERIE_HEADER2 = re.compile(SERIE_HEADER2_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

# Info Serie for Quickscrape

SERIE_QSERIE_PATTERN = r'>(.*?)</h'

# Info Album from Album
INFO_SERIENAMENUMBER_ALBUM_PATTERN = r'<span\sclass=\"type\">S.*?rie\s:\s</span>\s?(.*?)<.*?id=\"%s\">.*?<div\sclass=\"titre\">(?:(.*?)<.*?numa\">(.*?)</span>\.?\s?)?(.*?)<'

ALBUM_BDTHEQUE_NOTNUM_PATTERN = r'tails\">.*?<span\sclass=\"numa"></span>.*?<a name=\"(.*?)\"'			
ALBUM_BDTHEQUE_NOTNUM = re.compile(ALBUM_BDTHEQUE_NOTNUM_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_TITLE_PATTERN = r'itemprop=\"url\"\shref=\"%s\"\stitle=\"(.*?)\">'

ALBUM_EVAL_PATTERN = r'ratingValue\">(.*?)<'
ALBUM_EVAL = re.compile(ALBUM_EVAL_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	


ALBUM_SCENAR_MULTI_AUTHOR_PATTERN = r'<label>sc.*?nario\s:</label>.*?(?=\">)(.*?)<label>[^\&]' #Dessin'
ALBUM_SCENAR_MULTI_AUTHOR = re.compile(ALBUM_SCENAR_MULTI_AUTHOR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_SCENAR_MULTI_AUTHOR_NAMES_PATTERN = r'\">(.*?)</'
ALBUM_SCENAR_MULTI_AUTHOR_NAMES = re.compile(ALBUM_SCENAR_MULTI_AUTHOR_NAMES_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_STORYBOARD_MULTI_AUTHOR_PATTERN = r'label>storyboard\s:.*?itemprop.*?\">(.*?)<'
ALBUM_STORYBOARD_MULTI_AUTHOR = re.compile(ALBUM_STORYBOARD_MULTI_AUTHOR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_STORYBOARD_MULTI_AUTHOR_NAMES_PATTERN = r'<label>.*?\">(.*?)</a'
ALBUM_STORYBOARD_MULTI_AUTHOR_NAMES = re.compile(ALBUM_STORYBOARD_MULTI_AUTHOR_NAMES_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_SCENAR_PATTERN = r'<label>sc.*?nario\s:</label>.*?>(.*?)<'
ALBUM_SCENAR = re.compile(ALBUM_SCENAR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_DESSIN_MULTI_AUTHOR_PATTERN = r'<label>dessin\s:</label>.*?(?=\">)(.*?)<label>[^\&]'
ALBUM_DESSIN_MULTI_AUTHOR = re.compile(ALBUM_DESSIN_MULTI_AUTHOR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_DESSIN_MULTI_AUTHOR_NAMES_PATTERN = r'\">(.*?)</'
ALBUM_DESSIN_MULTI_AUTHOR_NAMES = re.compile(ALBUM_DESSIN_MULTI_AUTHOR_NAMES_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_DESSIN_PATTERN = r'<label>dessin\s:</label>.*?>(.*?)<'
ALBUM_DESSIN = re.compile(ALBUM_DESSIN_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_COLOR_MULTI_AUTHOR_PATTERN = r'<label>couleurs\s:</label>.*?(?=\">)(.*?)<label>[^\&]'
ALBUM_COLOR_MULTI_AUTHOR = re.compile(ALBUM_COLOR_MULTI_AUTHOR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_COLOR_MULTI_AUTHOR_NAMES_PATTERN = r'\">(.*?)</'
ALBUM_COLOR_MULTI_AUTHOR_NAMES = re.compile(ALBUM_COLOR_MULTI_AUTHOR_NAMES_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_COLOR_PATTERN = r'<label>Couleurs\s:</label>.*?>(.*?)<'
ALBUM_COLOR = re.compile(ALBUM_COLOR_PATTERN,  re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_COUVERT_MULTI_AUTHOR_PATTERN = r'<label>couverture\s:</label>.*?(?=\">)(.*?)<label>[^\&]'
ALBUM_COUVERT_MULTI_AUTHOR = re.compile(ALBUM_COUVERT_MULTI_AUTHOR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_COUVERT_MULTI_AUTHOR_NAMES_PATTERN = r'\">(.*?)</'
ALBUM_COUVERT_MULTI_AUTHOR_NAMES = re.compile(ALBUM_COUVERT_MULTI_AUTHOR_NAMES_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_COUVERT_PATTERN = r'<label>couverture\s:</label>.*?>(.*?)<'
ALBUM_COUVERT = re.compile(ALBUM_COUVERT_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_LETTRAGE_PATTERN = r'<label>Lettrage\s:\s?</label>.*?\">(.+?)</'
ALBUM_LETTRAGE = re.compile(ALBUM_LETTRAGE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_DEPOT_PATTERN = r'<label>D.pot L.gal\s:\s?</label>(?P<month>[\d|-]{0,2})[\/]?(?P<year>[\d]{2,4})?'
ALBUM_DEPOT = re.compile(ALBUM_DEPOT_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_ACHEVE_PATTERN = r'<label>Achev.*?\s:\s?</label>(?P<month>[\d|-]{0,2})[\/]?(?P<year>[\d]{2,4})?<'
ALBUM_ACHEVE = re.compile(ALBUM_ACHEVE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_EDITEUR_PATTERN = r'<label>Editeur\s:\s?</label>(.*?)</'
ALBUM_EDITEUR = re.compile(ALBUM_EDITEUR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_COLLECTION_PATTERN = r'<label>Collection\s:\s?</label>.*?\">(.*?)</'
ALBUM_COLLECTION = re.compile(ALBUM_COLLECTION_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_TAILLE_PATTERN = r'<label>Format\s:\s?</label>.*?(.+?)</'
ALBUM_TAILLE = re.compile(ALBUM_TAILLE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_ISBN_PATTERN = r"<label>ISBN\s:\s</label.*?>([\d-]*?)</"
ALBUM_ISBN = re.compile(ALBUM_ISBN_PATTERN, re.IGNORECASE | re.DOTALL)	

ALBUM_PLANCHES_PATTERN = r'<label>Planches\s:\s?</label>(\d*?)</'
ALBUM_PLANCHES = re.compile(ALBUM_PLANCHES_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_COVER_PATTERN = r'<meta\sproperty=\"og:title\".*?=\"https:(.*?)\"'
ALBUM_COVER = re.compile(ALBUM_COVER_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_RESUME_PATTERN = r'<meta\sname=\"description\"\scontent=\"(.*?)\"'
ALBUM_RESUME = re.compile(ALBUM_RESUME_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

ALBUM_INFOEDITION_PATTERN = r'<em>Info\s.*?dition\s:\s?</em>\s?(.*?)<'
ALBUM_INFOEDITION = re.compile(ALBUM_INFOEDITION_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	

#modif kiwi
#ALBUM_URL_PATTERN = r'<label>%s<span\sclass=\"numa.*?\.%s<.*?<a\shref=\"(.*?)"'
#ALBUM_URL_PATTERN = r'<label>%s<span\sclass=\"numa.*?\.<.*?<a\shref=\"(.*?)"'
ALBUM_URL_PATTERN = r'<label>%s<span\sclass=\"numa.*?\.<.*?<a\shref=\"(.*?)"\s.*?title=.+?\">(.+?)</'

ALBUM_SINGLE_URL_PATTERN = r'<label>%s<span\sclass=\"numa.*?\.%s<.*?<a\shref=\"(.*?)\#(.*?)\"'

#modif kiwi
#ALBUM_NON_NUM_URL_PATTERN = r'<label><span\sclass=\"numa\">%s</span>.*?\.<.*?<a\shref=\"(.*?)"'   
ALBUM_NON_NUM_URL_PATTERN = r'<label><span\sclass=\"numa\">%s</span>.*?\.<.*?<a\shref=\"(.*?)"\s.*?title=.+?\">(.+?)</'  

ALBUM_SINGLEALBUM_URLALL_PATTERN = r'<h3>(.*?)</h3>'
ALBUM_SINGLEALBUM_URLALL = re.compile(ALBUM_SINGLEALBUM_URLALL_PATTERN, re.DOTALL | re.IGNORECASE)

ALBUM_SINGLEALBUM_URL_PATTERN = r'href=\"(.*?)\"\stitle.*?\">.*?%s<span\sclass=\"numa\">%s<'

ALBUMDETAILS_URL_PATTERN = r'https:\/\/www.bedetheque.com\/album-%s-(.*?)\"'
ALBUMDETAILSSINGLE_URL_PATTERN = r'https:\/\/www.bedetheque.com\/album-(.*?)\"'

ALBUM_URL_PATTERN_NOTNUM = r'<div\sclass=\"album.*?href=\"(.*?)\"'
ALBUM_URL_NOTNUM = re.compile(ALBUM_URL_PATTERN_NOTNUM, re.MULTILINE | re.DOTALL | re.IGNORECASE)				

#ALBUM_QNUM_PATTERN = r'<title>(.*?)\-(.*?)\-?\s(.*?)</title>'
ALBUM_QNUM_PATTERN = r'og:title\"\scontent=\"(.*?)\-(.*?)\-?\s(.*?)\"\s*/>'
#ALBUM_QNUM = re.compile(ALBUM_QNUM_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)			
ALBUM_QNUM = re.compile(ALBUM_QNUM_PATTERN, re.IGNORECASE)		

ALBUM_QTITLE_PATTERN = r'titre.*?%s<span.*?name\">(.*?)<'
########################################


def BD_start(books):
	
	global AlbumNumNum, dlgNumber, dlgName, nRenamed, nIgnored, dlgAltNumber, bError, SHOWRENLOG, SHOWDBGLOG, DBGONOFF, DBGLOGMAX, RENLOGMAX, LANGENFR, aWord
	global TBTags, CBCover, CBStatus, CBGenre, CBNotes, CBWeb, CBCount, CBSynopsys,	CBImprint, CBLetterer, CBPrinted, CBRating, CBISBN, ARTICLES, SUBPATT, COUNTOF, COUNTFINIE, TITLEIT
	global CBLanguage, CBEditor, CBFormat, CBColorist, CBPenciller, CBWriter, CBTitle, CBSeries, CBCouverture, TIMEOUT, TIMEOUTS, TIMEPOPUP, CBDefault,CBRescrape, CBStop, PadNumber
		
	aWord = Translate()
	
	if not LoadSetting():
		return

	bdlogfile = ""
	debuglogfile = ""

	if not books:
		Result = MessageBox.Show(ComicRack.MainWindow, Trans(1),Trans(2), MessageBoxButtons.OK, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button1)
		return

	bdlogfile = (__file__[:-len('BedethequeScraper2.py')] + "BD2_Rename_Log.txt")
	if FileInfo(bdlogfile).Exists and FileInfo(bdlogfile).Length > RENLOGMAX:
		Result = MessageBox.Show(ComicRack.MainWindow, Trans(3), Trans(4), MessageBoxButtons.YesNo, MessageBoxIcon.Question, MessageBoxDefaultButton.Button1)
		if Result == DialogResult.Yes:
			File.Delete(bdlogfile)

	debuglogfile = (__file__[:-len('BedethequeScraper2.py')] + "BD2_debug_log.txt")
	if FileInfo(debuglogfile).Exists and FileInfo(debuglogfile).Length > DBGLOGMAX:
		Result = MessageBox.Show(ComicRack.MainWindow, Trans(5), Trans(6), MessageBoxButtons.YesNo, MessageBoxIcon.Question, MessageBoxDefaultButton.Button1)
		if Result == DialogResult.Yes:
			File.Delete(debuglogfile)

	nRenamed = 0
	nIgnored = 0
	
	if CBRescrape:
		Result = MessageBox.Show(ComicRack.MainWindow, Trans(139), Trans(138), MessageBoxButtons.YesNo, MessageBoxIcon.Question, MessageBoxDefaultButton.Button1)
		if Result == DialogResult.No:
			return

	if books:		
		WorkerThread(books)
	
	else:
		if DBGONOFF:print Trans(15) +"\n"
		log_BD(Trans(15), "", 1)

def WorkerThread(books):

	global AlbumNumNum, dlgNumber, dlgName, dlgNameClean, nRenamed, nIgnored, dlgAltNumber, bError, SHOWRENLOG, SHOWDBGLOG, DBGONOFF, DBGLOGMAX, RENLOGMAX, LANGENFR, aWord
	global TBTags, CBCover, CBStatus, CBGenre, CBNotes, CBWeb, CBCount, CBSynopsys,	CBImprint, CBLetterer, CBPrinted, CBRating, CBISBN, CBCouverture, CBDefault, CBRescrape, CBStop
	global CBLanguage, CBEditor, CBFormat, CBColorist, CBPenciller, CBWriter, CBTitle, CBSeries, bStopit, ARTICLES, SUBPATT, COUNTOF, RenameSeries, PickSeries, PickSeriesLink, serie_rech_prev, Shadow1, Shadow2, COUNTFINIE, TITLEIT, TIMEOUT, TIMEOUTS, TIMEPOPUP, PadNumber

	t = Thread(ThreadStart(thread_proc))

	bError = False
	
	Shadow1 = False
	Shadow2 = False
	
	TimeStart = clock()
	
	try:
				
		f = ProgressBarDialog(books.Count)
		f.Show(ComicRack.MainWindow)

		serieUrl = None
		nOrigBooks = books.Count

		log_BD(Trans(7) + str(nOrigBooks) +  Trans(8), "\n============ " + str(datetime.now().strftime("%A %d %B %Y %H:%M:%S")) + " ===========", 0)

		i = 0
		bStopit = False
		
		if DBGONOFF:print chr(10) + "=" * 25 + "- Begin! -" + "=" * 25 + chr(10)

		nTIMEDOUT = 0
		
		nBooks = len(books)
#modif kiwi
		PickSeries = False
		serie_rech_prev = None

		for book in books:
						
			TimeBookStart = clock()
			if DBGONOFF:print "v" * 60
						
			if bStopit or (nTIMEDOUT == int(TIMEOUT)):
				break
			
			nTIMEDOUT += 1
			
			if book.Number:
				dlgNumber = book.Number
			else:
				dlgNumber = book.ShadowNumber
				Shadow2 = True

			if book.Series:				
				dlgName = titlize(book.Series)
			else:
				dlgName = book.ShadowSeries
				Shadow1 = True

			if book.AlternateNumber:
				dlgAltNumber = book.AlternateNumber
			else:
				dlgAltNumber = ""

			dlgNameClean = cleanARTICLES(dlgName)
			dlgName = formatARTICLES(dlgName)

#modif Pitoufos
			findCara = dlgName.find(SUBPATT)
			if findCara > 0 :
				lenDlgName = len(dlgName)
				totalchar = lenDlgName - findCara
				dlgName = dlgName[:-totalchar]

			mPos = re.search(r'([.|,|\\|\/|-])', dlgNumber)
			if not isnumeric(dlgNumber):
				albumNum = dlgNumber
				AlbumNumNum = False
			elif isnumeric(dlgNumber) and not re.search(r'[.|,|\\|\/|-]', dlgNumber):
				dlgNumber = str(int(dlgNumber))
				albumNum = str(int(dlgNumber))
				AlbumNumNum = True
			elif mPos:
				nPos = mPos.start(1)
				albumNum = dlgNumber[:nPos]
				dlgAltNumber = dlgNumber[nPos:]
				dlgNumber = albumNum
				AlbumNumNum = True

			f.Update("[" + str(i + 1) + "/" + str(len(books)) + "] : " + dlgName + " - " + dlgNumber + if_else(dlgAltNumber == '', '', ' AltNo.[' + dlgAltNumber + ']') + " - " + titlize(book.Title), 1, book)
			f.Refresh()
			Application.DoEvents()
			
			RetAlb = False
			if CBRescrape:
				if book.Web:					
					RetAlb = QuickScrapeBD2(books, book, book.Web)
				
			if not CBRescrape:
				if DBGONOFF:print Trans(9) + dlgName + "\tNo = [" + albumNum + "]" + if_else(dlgAltNumber == '', '', '\tAltNo. = [' + dlgAltNumber + ']')
				serieUrl = None
				if DBGONOFF:print Trans(10), dlgName
				
				RetAlb = False
				serieUrl = SetSerieId(book, dlgName, albumNum, nBooks)	
				
				if serieUrl:
					RetAlb = True
					LongSerie= serieUrl.lower().replace(".html", u'__10000.html')
					serieUrl = LongSerie			

					if AlbumNumNum:
						if DBGONOFF:print Trans(11), albumNum + "]", if_else(dlgAltNumber == '', '', ' - AltNo.: ' + dlgAltNumber)
					else:
						if DBGONOFF:print Trans(12) + albumNum + "]", if_else(dlgAltNumber == '', '', ' - AltNo. [' + dlgAltNumber + ']')

					RetAlb = SetAlbumInformation(book, serieUrl, dlgName, albumNum)
				
					if not RetAlb and not 'revue' in serieUrl:					
						# reading info on album when no album list is present (i.e. "Croisade (Seconde époque: Nomade)")
						RetAlb = parseAlbumInfo (book, serieUrl, albumNum)
						
			if RetAlb:
				nRenamed += 1				
				log_BD("[" + dlgName + "] " + dlgNumber + if_else(dlgAltNumber == '', '', ' AltNo.[' + dlgAltNumber + ']') + " - " + titlize(book.Title), Trans(13), 1)
			else:
				nIgnored += 1
				log_BD("[" + dlgName + "] " + dlgNumber + if_else(dlgAltNumber == '', '', ' AltNo. [' + dlgAltNumber + ']') + " - " + titlize(book.Title), Trans(14) + "\n", 1)

			i += 1
			
			TimeBookEnd = clock()
			nSec = int(TimeBookEnd - TimeBookStart)
			if DBGONOFF:print Trans(125), str(timedelta(seconds=nSec)) + chr(10)
			#if DBGONOFF:print Trans(125), "%.2g\"" % (TimeBookEnd - TimeBookStart)	+ chr(10)
			if DBGONOFF:print "^" * 60

			# timeout in seconds before next scrape
			if TIMEOUTS and nOrigBooks > nIgnored + nRenamed:
				cPause = Trans(140).replace("%%", str(TIMEOUTS))
				f.Update(cPause, 0, False)
				f.Refresh()								
				t.CurrentThread.Join(int(TIMEOUTS)*1000)
				#f.Update("[" + str(i + 1) + "/" + str(len(books)) + "] : " + dlgName + " - " + dlgNumber + if_else(dlgAltNumber == '', '', ' AltNo.[' + dlgAltNumber + ']') + " - " + titlize(book.Title), 0)
				#f.Refresh()	

	except:
		cError = debuglog()
		log_BD("   [" + dlgName + "] " + dlgNumber + " - " + titlize(book.Title), cError, 1)
		if f:
			f.Close()
			t.Abort()
		return

	finally:
		f.Update(Trans(16), 1, book)
		f.Refresh()
		#Application.DoEvents()
		f.Close()

		log_BD("\n" + Trans(17) + str(nRenamed) , "", 0)
		log_BD(Trans(18) + str(nIgnored), "", 0)
		log_BD("============= " + str(datetime.now().strftime("%A %d %B %Y %H:%M:%S")) + " =============", "\n\n", 0)
		if bError and SHOWDBGLOG:
			rdlg = MessageBox.Show(ComicRack.MainWindow, Trans(17) + str(nRenamed) + ", " + Trans(18) + str(nIgnored) + ", (" + Trans(108) + str(nOrigBooks) + ")\n\n" + Trans(19), Trans(20), MessageBoxButtons.YesNo, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button1)
			if rdlg == DialogResult.Yes:
				# open debug log automatically
				if FileInfo(__file__[:-len('BedethequeScraper2.py')] + "BD2_Debug_Log.txt"):
					Start(__file__[:-len('BedethequeScraper2.py')] + "BD2_Debug_Log.txt")
		elif SHOWRENLOG:
			rdlg = MessageBox.Show(ComicRack.MainWindow, Trans(17) + str(nRenamed) + ", " + Trans(18) + str(nIgnored) + ", (" + Trans(108) + str(nOrigBooks) + ")\n\n" + Trans(21), Trans(22), MessageBoxButtons.YesNo, MessageBoxIcon.Question, MessageBoxDefaultButton.Button1)
			if rdlg == DialogResult.Yes:
				# open rename log automatically
				if FileInfo(__file__[:-len('BedethequeScraper2.py')] + "BD2_Rename_Log.txt"):
					Start(__file__[:-len('BedethequeScraper2.py')] + "BD2_Rename_Log.txt")
		else:
			
			TimeEnd = clock()			
			#if DBGONOFF:print Trans(124), "%.2g\"" % (TimeEnd - TimeStart)
			nSec = int(TimeEnd - TimeStart)
			if DBGONOFF:print Trans(124), str(timedelta(seconds=nSec)) 
			if DBGONOFF:print "=" * 25 + "- End! -" + "=" * 25 + chr(10)
			rdlg = MessageBox.Show(ComicRack.MainWindow, Trans(17) + str(nRenamed) + ", " + Trans(18) + str(nIgnored) + " (" + Trans(108) + str(nOrigBooks) + ")" , Trans(22), MessageBoxButtons.OK, MessageBoxIcon.Exclamation, MessageBoxDefaultButton.Button1)			

		t.Abort()		

		return

def SetSerieId(book, serie, num, nBooksIn):

	global dlgName, dlgNameClean, dlgAltNumber, aWord, ListSeries, NewLink, NewSeries, RenameSeries, PickSeries, PickSeriesLink, serie_rech_prev, CBStop
	
	if serie:
#modif kiwi
		if re.match("[a-z]", remove_accents(serie[0]).lower()):
			letter = remove_accents(serie[0])
		else:
			letter = "0"
	else:
		return ""

	
	urlN = "/bandes_dessinees_" + letter + ".html"
	
	RenameSeries = False
	
	try:

		serieUrl = ''

		request = _read_url(urlN.encode('utf-8'), False)
		
		if request:

			#serie = serie.encode('utf-8')			
			
			RegCompile = re.compile(SERIE_URL_PATTERN % checkRegExp(serie.strip()),  re.IGNORECASE)
			nameRegex = RegCompile.search(request)
				
			if nameRegex:
				
				serieUrl = nameRegex.group(1)
				if not ".html" in serieUrl:serieUrl += ".html"

				if DBGONOFF:print Trans(23) + serieUrl

			else:

#modif kiwi
				serie_rech = remove_accents(serie.lower())
				if serie_rech == serie_rech_prev and PickSeries != False:
					serie_rech_prev = serie_rech
					RenameSeries = PickSeries
					return PickSeriesLink
				else:
					serie_rech_prev = serie_rech
					PickSeries = False
					
				ListSeries = list()
				if DBGONOFF:print "Nom de Série pour recherche = " + dlgNameClean				
				urlN = '/search/tout?RechTexte=' + url_fix(remove_accents(dlgNameClean.lower().strip())) +'&RechWhere=0'

				if DBGONOFF:print Trans(113), 'www.bedetheque.com' + urlN
				
				request = _read_url(urlN.encode('utf-8'), False)
								
				#SERIE_LIST_CHECK = re.compile(SERIE_LIST_CHECK_PATTERN, re.IGNORECASE | re.DOTALL)				
				if SERIE_LIST_CHECK.search(request):
					Result = MessageBox.Show(ComicRack.MainWindow, Trans(114) + '[' + titlize(book.Series) + '] !', Trans(2), MessageBoxButtons.OK, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button1)
					if DBGONOFF:print Trans(114) + '[' + titlize(book.Series) + '] !'
					return ''
				
				i = 1
				RegCompile = re.compile(SERIE_LIST_PATTERN, re.IGNORECASE | re.DOTALL )
				for seriepick in RegCompile.finditer(request):						
					ListSeries.append(["serie-" + seriepick.group(1), strip_tags(seriepick.group(2)).replace("</span>",""), str(i).zfill(3)])						
					i = i + 1											
					

				ListSeries.sort(key=operator.itemgetter(2))

				if len(ListSeries) == 1:
					if DBGONOFF:print Trans(24) + checkRegExp(serie) + "]" 
					if DBGONOFF:print Trans(111) + (ListSeries[0][1])
					log_BD("** [" + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com" + serieUrl + ")", Trans(25), 1)
					log_BD(Trans(111), "[" + ListSeries[0][1] + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com\\serie-" + ListSeries[0][0] + ")", 1)
					RenameSeries = ListSeries[0][1]					
					return ListSeries[0][0]

				elif len(ListSeries) > 1:	
					if (CBStop == True or CBStop == "2") or nBooksIn == 1:				
						lUnique = False
						for i in range(len(ListSeries)):						
 #modif kiwi
							if remove_accents(ListSeries[i][1].lower()) == remove_accents(dlgName.lower().strip()):
								lUnique = True
								nItem = i
							if remove_accents(ListSeries[i][1].lower()) == remove_accents(dlgName.lower().strip()) and re.search(r'\(.{4,}?\)', ListSeries[i][1].lower()):
								lUnique = False
						if lUnique:
							if DBGONOFF:print Trans(24) + checkRegExp(serie) + "]" 
							if DBGONOFF:print Trans(111) + (ListSeries[nItem][1])
							log_BD("** [" + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com" + serieUrl + ")", Trans(25), 1)
							log_BD(Trans(111), "[" + ListSeries[nItem][1] + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com\\serie-" + ListSeries[nItem][0] + ")", 1)
							RenameSeries = ListSeries[nItem][1]					
							return ListSeries[nItem][0]
						# Pick a series
						NewLink = ''
						NewSeries = ''									
						a = ListSeries
						pickAseries = SeriesForm(serie, ListSeries, FormType.SERIE)
						result = pickAseries.ShowDialog()
					
						if result == DialogResult.Cancel:
							if DBGONOFF:print Trans(24) + checkRegExp(serie) + "]"						
							log_BD("** [" + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com" + serieUrl + ")", Trans(25), 1)
							return	''					
						else:
							if DBGONOFF:print Trans(24) + checkRegExp(serie) + "]"						
							if DBGONOFF:print Trans(111) + (NewSeries)						
							log_BD("** [" + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com" + serieUrl + ")", Trans(25), 1)
							log_BD(Trans(111), "[" + NewSeries + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com\\" + NewLink + ")", 1)
							RenameSeries = NewSeries						
#modif kiwi
							PickSeries	= RenameSeries
							PickSeriesLink = NewLink                        
							return NewLink
					else:
						if DBGONOFF:print Trans(142) + checkRegExp(serie) + "]"						
						log_BD("** [" + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com" + serieUrl + ")", Trans(25), 1)
						return	''							
		
	except:

		cError = debuglog()
		log_BD("** Error [" + serie + "] " + num + " - " + titlize(book.Title), cError, 1)

	return serieUrl

#modif kiwi
def remove_accents(raw_text):
	raw_text = re.sub(u"[àáâãäåÀÁÂÄÅÃ]", 'a', raw_text)
	raw_text = re.sub(u"[èéêëÉÈÊË]", 'e', raw_text)
	raw_text = re.sub(u"[çÇ]", 'c', raw_text)
	raw_text = re.sub(u"[ìíîïÍÌÎÏ]", 'i', raw_text)
	raw_text = re.sub(u"[òóôõöÓÒÔÖÕ]", 'o', raw_text)
	raw_text = re.sub(u"[ùúûüÚÙÛÜ]", 'u', raw_text)
	raw_text = re.sub(u"[œŒ]", 'oe', raw_text)
	return raw_text

def SetAlbumInformation(book, serieUrl, serie, num):

	global dlgAltNumber, aWord, RenameSeries
	
	LINK_ALBUM = False

	albumUrl = parseSerieInfo(book, serieUrl, False)
	
	if albumUrl and not 'revue' in serieUrl:
		if DBGONOFF:print Trans(26), albumUrl
	else:
		if DBGONOFF:print Trans(26), Trans(25)

	if albumUrl and not 'revue' in serieUrl:
		if not parseAlbumInfo(book, albumUrl, num):
			return False
		return True

	elif 'revue' in serieUrl:
		return albumUrl

	else:
		if DBGONOFF:print Trans(27) + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo.' + dlgAltNumber) + "\n"
		log_BD("   [" + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo.' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com" + serieUrl + ")", Trans(28), 1)
		return False

def parseSerieInfo(book, serieUrl, lDirect):

	global AlbumNumNum, dlgNumber, dlgAltNumber, dlgName, aWord, RenameSeries, NewLink, NewSeries
	
	if DBGONOFF:print "=" * 60
	if DBGONOFF:print "parseSerieInfo", "a)", serieUrl, "b)", lDirect
	if DBGONOFF:print "=" * 60
	
	#SERIE_HEADER = re.compile(SERIE_HEADER_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	
	SERIE_QSERIE = re.compile(SERIE_QSERIE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)
	
	
	albumURL = ''
	
	#LongSerie= re.sub(u'^_10000\.html','\_\_10000.html',serieUrl.lower())
		
	try:
		request = _read_url(serieUrl, lDirect)
		#request = _read_url(LongSerie, lDirect)
	except:		
		cError = debuglog()
		log_BD("   " + serieUrl + " " + Trans(43), "", 1)
		return False


	SerieInfoRegex = SERIE_HEADER.search(request)
	if SerieInfoRegex:

		#Entete = SerieInfoRegex.group(1)
		Entete = request
		
		if RenameSeries:
			if CBSeries:
				book.Series = titlize(RenameSeries)
		
		#Series if Quickscrape and empty name
		qserie = ""
		if lDirect and not book.Series:
			nameRegex = SERIE_QSERIE.search(Entete)
			if nameRegex:
				qserie = checkWebChar(nameRegex.group(1).strip())			
				#qserie = checkWebChar(nameRegex.group(1).decode('utf-8'))		
				if CBSeries:	
					book.Series = titlize(qserie)
					if DBGONOFF:print Trans(9), qserie
			else:
				albumURL = False
				return

		#genre
		if CBGenre:
			nameRegex = SERIE_GENRE.search(Entete)
			if nameRegex:
				genre = checkWebChar(nameRegex.group(1).strip())
				#genre = checkWebChar(nameRegex.group('genre').decode('utf-8'))
			else:
				genre = ""
			if genre != "":
				book.Genre = genre
			elif genre == "" and 'revue' in serieUrl:
				book.Genre = "Revue"																
			if DBGONOFF:print Trans(51), book.Genre

		#Resume
		if CBSynopsys:								
			nameRegex = SERIE_RESUME.search(checkWebChar(Entete.replace("\r\n","")), 0)
			if nameRegex:
				resume = strip_tags(nameRegex.group(1)).strip()
				#resume = strip_tags(nameRegex.group('resume')).decode('utf-8').strip()
			else:
				resume = ""
			
			resume = re.sub(r'Tout sur la série.*?:\s?', "", resume, re.IGNORECASE)
			book.Summary = (checkWebChar(resume)).strip()
			cResume = if_else(resume, Trans(52), Trans(53))
			if DBGONOFF:print cResume					

		#fini
		if CBStatus:
			SerieState = ""
			nameRegex = SERIE_STATUS.search(Entete)
			if nameRegex:
				fin = checkWebChar(nameRegex.group(1).strip())
				log_BD(fin, Trans(25), 1)
				#fin = checkWebChar(nameRegex.group('fin').decode('utf-8'))
			else:
				fin = ""

#modif kiwi
			if ("finie" in fin) or ("One shot" in fin) or (dlgNumber == "One Shot"):
				book.SeriesComplete = YesNo.Yes
				SerieState = Trans(54)
			elif ("cours" in fin):
				book.SeriesComplete = YesNo.No
				SerieState = Trans(55)
			else:
				book.SeriesComplete = YesNo.Unknown
				SerieState = Trans(56)

			if DBGONOFF:print Trans(57) + SerieState + if_else(dlgNumber == "One Shot", " (One Shot)", "")

		# Language
		if CBLanguage:
			nameRegex = SERIE_LANGUE.search(Entete)
			dLang = {"Fr": "fr", "Al": "de", "An": "en", "It":"it", "Es":"es", "Ne":"du", "Po":"pt", "Ja":"ja"}
			if nameRegex:
				langue = nameRegex.group(1).strip()
				if DBGONOFF:print Trans(36), langue[:2]
				book.LanguageISO = dLang[langue[:2]]	
			
		#Default Values
		if not CBDefault:
			book.EnableProposed = YesNo.No
			if DBGONOFF:print Trans(136), "No"

		SerieInfoRegex = SERIE_HEADER2.search(request)
		if SerieInfoRegex:
			Entete2 = SerieInfoRegex.group(1)

			#Notes-Rating
			#if CBRating:
			#	nameRegex = SERIE_NOTE.search(Entete)
			#	if nameRegex:
			#		note = nameRegex.group('note')
			#	else:
			#		note = "0.0"

			#	book.CommunityRating = float(note) / 2
			#	if DBGONOFF:print Trans(58) + str(float(note) / 2)
			
			# Number of...
			if CBCount and not lDirect:			
					
				count = 0
				cCountText = ""
				if not COUNTOF:				
					nameRegex = SERIE_COUNT.search(Entete2)
					if nameRegex and AlbumNumNum:
						count = checkWebChar(nameRegex.group(1))
						book.Count = int(count)
						cCountText = str(int(count))				
					else:					
						book.Count = -1
						cCountText = "---"
				elif COUNTFINIE and book.SeriesComplete == YesNo.No:				
					book.Count = -1
					cCountText = "---"
				else:				
					nameRegex = SERIE_COUNT_REAL.search(request)				
					if nameRegex:							
						for numof in SERIE_COUNTOF.finditer(nameRegex.group(1)):						
							if isnumeric(numof.group(1)) and int(numof.group(1)) > count:
								count = int(numof.group(1))
						if count > 0 and AlbumNumNum:						
							book.Count = int(count)	
							cCountText = str(int(count))
					else:					
						book.Count = -1
						cCountText = "---"
				
				if DBGONOFF:print Trans(59) + if_else(dlgNumber == "One Shot", "1", cCountText)
		
		Regex = re.compile(r'<label>([^<]*?)<span\sclass=\"numa\">(.*?)</span.*?<a\shref=\"(.*?)".*?title=.+?\">(.+?)</', re.IGNORECASE | re.DOTALL)
						
		i = 0
		ListAlbum, ListAlbumAll = list(), list()
		for r in Regex.finditer(request):
			n, a, url, title = r.group(1), r.group(2), r.group(3), r.group(4)
			num = if_else(n,n, if_else(a, a, ""))
			ListAlbumAll.append([url, num + ". " + title, str(i).zfill(3)])
			if dlgNumber != "" and (n == dlgNumber or a == dlgNumber) and not lDirect:
				ListAlbum.append([url, num + ". " + title, str(i).zfill(3)])
			i = i + 1
		
		if len(ListAlbum) == 0: 
			ListAlbum = ListAlbumAll
		
		if DBGONOFF:print "Nbr. d'item dans la Liste Album est de: " + str(len(ListAlbum))
		if len(ListAlbum) > 1:
			if (CBStop == True or CBStop == "2"):
				NewLink = ""
				NewSeries = ""									
				pickAnAlbum = SeriesForm(dlgNumber, ListAlbum, FormType.ALBUM)
				result = pickAnAlbum.ShowDialog()
				
				if result == DialogResult.Cancel:
					albumURL = ListAlbum[0][0]	
					if DBGONOFF:print "---> Appuie sur Cancel, choix du 1er item"
				else:
					albumURL = NewLink
			else:
				albumURL = ListAlbum[0][0]
				if DBGONOFF:print "---> Plus d'un item mais l'option pause scrape est désactivé, choix du 1er item"
		elif len(ListAlbum) == 1:
			albumURL = ListAlbum[0][0]
			if DBGONOFF:print "---> Seulement 1 item dans la liste"	
		else:
			Regex = re.compile(r'class="titre"\shref="(.+?)".+?<span class="numa">.*?</span>.+?', re.IGNORECASE | re.DOTALL)#Rien trouvé il ce peux qu'il n'est pas de liste sur le coté, surement 1 seul item
			r = Regex.search(request)
			if r:
				albumURL = r.group(1)
				if DBGONOFF:print "---> Numéro n'existe pas dans la liste, choix du 1er item"
			else:
				return False

	return albumURL

class AlbumInfo:
	def __init__ (self, n, a, title, info, couv, url):
		self.Couv = couv
		self.N = n
		self.A = a
		self.Title = title
		self.Info = info	
		self.URL = url

def parseAlbumInfo(book, pageUrl, num, lDirect = False):

	global dlgAltNumber, aWord, RenameSeries, dlgName, dlgNumber, CBelid, NewLink, NewSeries
	global TBTags, CBCover, CBStatus, CBGenre, CBNotes, CBWeb, CBCount, CBSynopsys,	CBImprint, CBLetterer, CBPrinted, CBRating, CBISBN, CBDefault, CBRescrape, CBStop, PopUpEditionForm
	global CBLanguage, CBEditor, CBFormat, CBColorist, CBPenciller, CBWriter, CBTitle, CBSeries, ARTICLES, SUBPATT, COUNTOF, Shadow1, Shadow2, CBCouverture, COUNTFINIE, TITLEIT, TIMEOUT, TIMEOUTS, TIMEPOPUP, PadNumber
	
	if DBGONOFF:print "=" * 60
	if DBGONOFF:print "parseAlbumInfo", "a)", pageUrl, "b)", num , "c)", lDirect
	if DBGONOFF:print "=" * 60
	
	AlbumBDThequeNum = ""
	
	albumUrl = _read_url(pageUrl, False)							
	
	#identify the album n. in BDTHQ
	cBDNum = False
	cBDNumS = re.search(r'\-(\d+).html', pageUrl)
	if cBDNumS:
		cBDNum = cBDNumS.group(1)
		if cBDNum:				
			AlbumBDThequeNum = cBDNum
	elif "serie-" in pageUrl:
		ID_ALBUM_PATT = re.search(r'serie.*?\.html\#(\d+)$', pageUrl)		
		if ID_ALBUM_PATT:			
			ID_ALBUM = ID_ALBUM_PATT.group(1)		
			AlbumBDThequeNum = ID_ALBUM
				
	else:		
		# Album N. est Numerique
		if dlgNumber or dlgAltNumber:
			ALBUM_BDTHEQUE_NUM_PATTERN = r'tails\">%s<span\sclass=\"numa">%s</span>.*?<a name=\"(.*?)\"'
			ALBUM_BDTHEQUE_NUM = re.compile(ALBUM_BDTHEQUE_NUM_PATTERN % (num, dlgAltNumber), re.IGNORECASE | re.MULTILINE | re.DOTALL)

			nameRegex = ALBUM_BDTHEQUE_NUM.search(albumUrl)

			if nameRegex:
				AlbumBDThequeNum = nameRegex.group(1)
			else:
				ALBUM_BDTHEQUE_NUM_PATTERN = r'>%s<span\sclass=\"numa">.*?</span>.*?<a name=\"(.*?)\"'
				ALBUM_BDTHEQUE_NUM = re.compile(ALBUM_BDTHEQUE_NUM_PATTERN % num, re.IGNORECASE | re.MULTILINE | re.DOTALL)
				nameRegex = ALBUM_BDTHEQUE_NUM.search(albumUrl)
				if nameRegex:
					AlbumBDThequeNum = nameRegex.group(1)
				else:
					# Album not found
					nameRegex = ""
					return False
		
		# Album N. in Lettres				
		else:			
			#ALBUM_BDTHEQUE_NOTNUM = re.compile(ALBUM_BDTHEQUE_NOTNUM_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)
			nameRegex = ALBUM_BDTHEQUE_NOTNUM.search(albumUrl)
			if nameRegex:
				AlbumBDThequeNum = nameRegex.group(1)
					
			else:
			
				nameRegex = ""
				return False
	
	try:		
		i = 0
		ListAlbum = list()
		pickedVar = ""
		picked = False
		info = albumUrl
		tome = re.search(r'<h2>\s*(\w*?)<span class="numa">(.*?)</span>.', albumUrl, re.IGNORECASE | re.DOTALL)
		t = if_else(tome.group(1), tome.group(1), tome.group(2)) if tome else ""
		nameRegex = re.compile(r'class="couv">.+?<img.+?src="(.+?)".+?class="titre".*?>([^<>]*?)<span class="numa">(.*?)</span>.+?\r\n\s+(.+?)</.+?>(.+?)<!--.+?class="album-admin".*?id="bt-album-(.+?)">', re.IGNORECASE | re.DOTALL | re.MULTILINE)
		for albumPick in nameRegex.finditer(albumUrl):	
			couv = re.sub('/cache/thb_couv/', '/media/Couvertures/', albumPick.group(1)) if albumPick.group(1) else "" #get higher resolution image
			title = checkWebChar(albumPick.group(4).strip())
			nfo = albumPick.group(5)
			a = albumPick.group(3).strip() if isnumeric(dlgNumber) else re.sub(t,'',albumPick.group(3).strip()).strip()
			url = pageUrl if i == 0 else pageUrl + "#" + albumPick.group(6).strip()
			albumInfo = AlbumInfo(t, a, title, nfo, couv, url)
			if DBGONOFF:print "Tome)", t, "Alt)", a, "Title)", title
			
			ListAlbum.append([a, albumInfo, str(i).zfill(3)])
			i = i + 1
		
		if len(ListAlbum) == 1:
			pickedVar = ListAlbum[0][1]
			if DBGONOFF:print "---> Seulement 1 item dans la liste"	
		elif len(ListAlbum) > 1:			
			for f in ListAlbum:
				if dlgAltNumber != "" and f[1].A == dlgAltNumber:
					pickedVar = f[1]
					picked = True
					break
			
			if PopUpEditionForm:
				picked = False
			
			if PopUpEditionForm and (CBStop == True or CBStop == "2") and not picked:
				NewLink = ""
				NewSeries = ""	
				pickAvar = SeriesForm(num, ListAlbum, FormType.EDITION)
				result = pickAvar.ShowDialog()
				
				if result == DialogResult.Cancel:
					pickedVar = ListAlbum[0][1]
					if DBGONOFF:print "---> Cancel appuyer, on choisi le premier"

				else:
					pickedVar = NewSeries
			elif not picked:
				pickedVar = ListAlbum[0][1]
				if DBGONOFF:print "---> Choix du 1er item"
				
		if pickedVar :
			info = pickedVar.Info
			if DBGONOFF:print "Choisi #Alt: " + pickedVar.A + " // Titre: " + pickedVar.Title
			
		if info :
			if RenameSeries:
				if CBSeries:
					book.Series = titlize(RenameSeries)
			elif (Shadow1 or book.Series != titlize(dlgName)):
				if CBSeries:	
					book.Series = titlize(dlgName)

			if Shadow2:
				book.Number = dlgNumber
			
			#web
			if CBWeb == True and not CBRescrape:			
				book.Web = pickedVar.URL
				if DBGONOFF:print Trans(123), book.Web
			elif CBWeb == "2" and not CBRescrape:
				cBelid = re.search(r'\-(\d+).html', pageUrl)
				if cBelid:			
					book.Web = 'www.bedetheque.com/BD--' + cBelid.group(1) + '.html'
					if DBGONOFF:print Trans(123), book.Web
			
			qnum = pickedVar.N#is equal to t always, but keep it in case of needed modification
			anum = pickedVar.A
			book.Number = anum if not qnum and anum else qnum#set number to Alt if no number and an Alt Exists
			book.AlternateNumber = dlgAltNumber if not qnum and anum else anum#Don't change if prev was set to anum, else set to Alt
			if PadNumber != "0":
				if isPositiveInt(book.Number): book.Number = str(book.Number).zfill(int(PadNumber))
				if isPositiveInt(book.AlternateNumber): book.AlternateNumber = str(book.AlternateNumber).zfill(int(PadNumber))
			if DBGONOFF:print "Num: ", book.Number
			if DBGONOFF:print "Alt: ", book.AlternateNumber
		
			series = book.Series
			nameRegex = re.search('bandeau-info.+?<h1>.+?>([^"]+?)[<>]', albumUrl, re.IGNORECASE | re.DOTALL | re.MULTILINE)# Les 5 Terres Album et Serie, Comme avant
			#nameRegex2 = re.search("<label>S.rie : </label>(.+?)</li>", albumUrl, re.IGNORECASE | re.DOTALL | re.MULTILINE)# 5 Terres (Les) sur Album seulement
			if nameRegex:
				series = checkWebChar(nameRegex.group(1).strip())
				if DBGONOFF:  print Trans(9) + series
				
			if CBTitle:
				NewTitle = ""		
				try:
					NewTitle = titlize(strip_tags(pickedVar.Title))
				except:
					NewTitle = pickedVar.Title
				
				if NewTitle.lower() == series.lower():
					NewTitle = ""
				
				book.Title = NewTitle
				if DBGONOFF:print Trans(29), book.Title
			
			if CBNotes:
				book.Notes = "Bedetheque.com - " + str(datetime.now().strftime("%A %d %B %Y %H:%M:%S")) + chr(10) + "BD2 scraper v" + VERSION
						
			if TBTags == "DEL":
				book.Tags = ""
			elif TBTags != "":
				book.Tags = TBTags	
			
			if CBWriter:
				nameRegex = ALBUM_SCENAR_MULTI_AUTHOR.search(info, 0)
				if nameRegex:
					scenaristes = ""
					thisscen = ""					
					for scenar_multi in ALBUM_SCENAR_MULTI_AUTHOR_NAMES.finditer(nameRegex.group(1)):
						thisscen = parseNames(scenar_multi.group(1).strip())
						if thisscen not in scenaristes:	
							scenaristes = scenaristes + thisscen + ", "

					thisscen = ""
					for scenar_multi in ALBUM_STORYBOARD_MULTI_AUTHOR.finditer(info, 0):
						thisscen = parseNames(scenar_multi.group(1).strip())
						if thisscen not in scenaristes:
							scenaristes = scenaristes + thisscen + ", "
			
					book.Writer = scenaristes[:-2]

				else:

					nameRegex = ALBUM_SCENAR.search(info, 0)
					if nameRegex:					
						scenaristes = nameRegex.group(1).strip()
						book.Writer = parseNames(scenaristes)
						log_BD(parseNames(scenaristes),"",1)                        
  
					else:
						book.Writer = ""					
				if DBGONOFF:print Trans(30), book.Writer
			
			if CBPenciller:
				nameRegex = ALBUM_DESSIN_MULTI_AUTHOR.search(info, 0)
				if nameRegex:
					dessinateurs = ""				
					for dessin_multi in ALBUM_DESSIN_MULTI_AUTHOR_NAMES.finditer(nameRegex.group(1)):		
						dessinateurs = dessinateurs + parseNames(dessin_multi.group(1).strip()) + ", "
							
					book.Penciller = dessinateurs[:-2]

				else:
					nameRegex = ALBUM_DESSIN.search(info, 0)					
					if nameRegex:
						dessinateurs = nameRegex.group(1).strip()				
						book.Penciller = parseNames(dessinateurs)
  
					else:
						book.Penciller = ""
					
				if DBGONOFF:print Trans(31), book.Penciller
			
			if CBColorist:
				cColorNote = ""
				nameRegex = ALBUM_COLOR_MULTI_AUTHOR.search(info, 0)
				cColorist = ""				
				if nameRegex:					
					for color_multi in ALBUM_COLOR_MULTI_AUTHOR_NAMES.finditer(nameRegex.group(1)):
						cColorist = cColorist + parseNames(color_multi.group(1).strip()) + ", "
							
					book.Colorist = cColorist[:-2]
					cColorist = cColorist[:-2]

				else:
					nameRegex = ALBUM_COLOR.search(info, 0)						
					if nameRegex:
						coloristes = nameRegex.group(1).strip()					
						cColorist = parseNames(coloristes)
						if re.search("<.*?>", cColorist):
							book.Colorist = ""
							cColorNote = Trans(32)
						else:
							book.Colorist = cColorist							
					else:
						book.Colorist = ""
						
				if DBGONOFF:print Trans(33), cColorist , cColorNote
			
			if CBCouverture:
				nameRegex = ALBUM_COUVERT_MULTI_AUTHOR.search(info, 0)
				cCoverNote = ""	
				if nameRegex:						
					for cover_multi in ALBUM_COUVERT_MULTI_AUTHOR_NAMES.finditer(nameRegex.group(1)):				
						cCoverNote = cCoverNote + parseNames(cover_multi.group(1).strip()) + ", "
							
					book.CoverArtist = cCoverNote[:-2]
					cCoverNote = ""						

				else:
					nameRegex = ALBUM_COUVERT.search(info, 0)						
					if nameRegex:					
						couvertures = nameRegex.group(1)
						cCouvertures = parseNames(couvertures)
						if re.search("<.*?>", cCouvertures):
							book.CoverArtist = ""
							cCoverNote = Trans(32)
						else:
							book.CoverArtist = cCouvertures							
					else:
						book.CoverArtist = ""
						
				if DBGONOFF:print Trans(120), book.CoverArtist , cCoverNote
			
			if CBPrinted:
				nameRegex = ALBUM_DEPOT.search(info, 0)
				if nameRegex:
					if nameRegex.group('month') != '-' and nameRegex.group('month') != "":
						book.Month = int(nameRegex.group('month'))
						book.Year = int(nameRegex.group('year'))
						if DBGONOFF:print Trans(34), str(book.Month) + "/" + str(book.Year)
					else:
						book.Month = -1
						book.Year = -1
				else:
					book.Month = -1
					book.Year = -1	
			
			if CBEditor:
				nameRegex = ALBUM_EDITEUR.search(info, 0)
				if nameRegex:
					#editeur = parseNames(nameRegex.group(1).decode('utf-8'))
					editeur = parseNames(nameRegex.group(1))
					book.Publisher = editeur
				else:
					book.Publisher = ""
					
				if DBGONOFF:print Trans(35), book.Publisher
			
			if CBISBN:
				nameRegex = ALBUM_ISBN.search(info, 0)
				if nameRegex:
					isbn = nameRegex.group(1)
					if isbn	!= '</span>':
						book.ISBN = checkWebChar(isbn)
					else:
						book.ISBN = ""
				else:
					book.ISBN = ""
					
				if DBGONOFF:print "ISBN: ", book.ISBN
			
			# Lettrage is optional => So, there is a specific research
			if CBLetterer:
				#ALBUM_LETTRAGE = re.compile(ALBUM_LETTRAGE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	
				nameRegex = ALBUM_LETTRAGE.search(info, 0)								
				if nameRegex:
					letterer = nameRegex.group(1).strip()
					#letterer = nameRegex.group(1).decode('utf-8')
					book.Letterer = parseNames(letterer)
				else:
					book.Letterer = ""
						
				if DBGONOFF:print Trans(38), book.Letterer 
			
			# Album evaluation is optional => So, there is a specific research
			if CBRating:
				#ALBUM_EVAL = re.compile(ALBUM_EVAL_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	
				nameRegex = ALBUM_EVAL.search(albumUrl, 0)														
				if nameRegex:
					evaluation = nameRegex.group(1)
					book.CommunityRating = float(evaluation)
					if DBGONOFF:print Trans(39) + str(float(evaluation))
			
			# Achevè imp. is optional => So, there is a specific research
			if CBPrinted:
				#ALBUM_ACHEVE = re.compile(ALBUM_ACHEVE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)																	   
				nameRegex = ALBUM_ACHEVE.search(info, 0)
				if nameRegex and book.Month < 1:
					book.Month = int(nameRegex.group('month'))
					book.Year = int(nameRegex.group('year'))
					if DBGONOFF:print Trans(40), str(book.Month) + "/" + str(book.Year)
			
			# Collection is optional => So, there is a specific research
			if CBImprint:
				#ALBUM_COLLECTION = re.compile(ALBUM_COLLECTION_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	
				nameRegex = ALBUM_COLLECTION.search(albumUrl, 0)
				nameRegex2 = ALBUM_COLLECTION.search(info, 0)
				if nameRegex or nameRegex2:
					if nameRegex2:
						nameRegex = nameRegex2
						
					collection = nameRegex.group(1)
					#collection = nameRegex.group(1).decode('utf-8')
					book.Imprint = checkWebChar(collection)						
				else:
					book.Imprint = ""
					
				if DBGONOFF:print Trans(41), book.Imprint
			
			# Format is optional => So, there is a specific research
			if CBFormat:
				#ALBUM_TAILLE = re.compile(ALBUM_TAILLE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)								   
				nameRegex = ALBUM_TAILLE.search(info, 0)
				if nameRegex:
					taille = nameRegex.group(1)
					book.Format = taille
				else:
					book.Format = "" 
					
				if DBGONOFF:print Trans(42), book.Format
			
			# Album summary is optional => So, there is a specific research
			if CBSynopsys:
				#ALBUM_RESUME = re.compile(ALBUM_RESUME_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	
				nameRegex = ALBUM_RESUME.search(albumUrl, 0)																		
				if nameRegex:					
					resume = strip_tags(nameRegex.group(1)).strip()						
					resume = re.sub(r'Tout sur la série.*?:\s?', "", resume, re.IGNORECASE)
					#resume = strip_tags(nameRegex.group(1)).decode('utf-8').strip()					
					if not lDirect and book.Summary != resume and resume:
						book.Summary = book.Summary + chr(10) + chr(10) + if_else(book.Title, '>' + book.Title + '< ' + chr(10), "") + resume
					elif resume and book.Title:
						book.Summary = if_else(book.Title, '>' + book.Title + '< ' + chr(10), "") + resume
							
						if DBGONOFF:print Trans(100)						
				else:
					if DBGONOFF:print Trans(101)

			# Info edition			
			if CBSynopsys:
				#ALBUM_INFOEDITION = re.compile(ALBUM_INFOEDITION_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	
				nameRegex = ALBUM_INFOEDITION.search(info, 0)														
				if nameRegex:										
					if nameRegex.group(1) !=" &nbsp;":						
						infoedition = strip_tags(nameRegex.group(1)).strip()
						#infoedition = strip_tags(nameRegex.group(1)).decode('utf-8').strip()
						if infoedition:
							book.Summary = if_else(book.Summary != "",book.Summary + chr(10) + chr(10) + Trans(118) + infoedition,Trans(118) + infoedition)
						if DBGONOFF:print Trans(118) + Trans(119)		
						
			# series only formatted
			if CBSeries:													
				book.Series = titlize(series, True)							
				if DBGONOFF:print Trans(9), book.Series
			
			# Cover Image only for fileless
			if CBCover and not book.FilePath:													 
				if pickedVar.Couv:
					CoverImg = pickedVar.Couv
					request = HttpWebRequest.Create(CoverImg)					
					response = request.GetResponse()
					response_stream = response.GetResponseStream()
					retval = Image.FromStream(response_stream)
					ComicRack.App.SetCustomBookThumbnail(book, retval)
					if DBGONOFF:print Trans(105), CoverImg	
			
			#When QS, no language is set. This is a Temp solution, because there could be other language, but we must go through the series page to check
			if CBLanguage and lDirect and not book.LanguageISO:
				book.LanguageISO = "fr"
					
			# Planches			
			if not book.FilePath:
					#ALBUM_PLANCHES = re.compile(ALBUM_PLANCHES_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)	
					nameRegex = ALBUM_PLANCHES.search(info, 0)	
					if nameRegex:
						if nameRegex.group(1):
							book.PageCount =  int(nameRegex.group(1).strip())
						else:
							book.PageCount =  0

						if DBGONOFF:print Trans(122), book.PageCount
				
	except:
		nameRegex = ""
		cError = debuglog()
		log_BD("   " + pageUrl + " " + Trans(43), "", 1)
		return False
		
	return True

def parseNames(extractedNames):

	global aWord
	
	#RAW_STR = re.compile(RAW_STR_PATTERN)
	newstr = RAW_STR.sub('=', extractedNames)

	splitted = newstr.split('=')
	names = ""

	for splitT in splitted:

		Regex = re.compile(LAST_FIRST_NAMES, re.IGNORECASE)
		nameRegex = Regex.search(splitT)

		if nameRegex:
			names = names + ',' + nameRegex.group('firstname') + ' ' + nameRegex.group('name')

		else:

			if splitT != "":
				names = names + ',' + splitT

		if re.match(r',&lt;', names):
			names = ''
		names = re.sub(',&nbsp;,', r', ', names)

	return checkWebChar(names[1:len(names)]).strip(",")

def _read_url(url, bSingle):

	global dlgName, dlgNumber, dlgAltNumber, aWord
	
	page = ''
	#headers = { 'User-Agent' : 'Mozilla/5.0'}
	##headers = { 'User-Agent' : 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; WOW64; Trident/6.0)', 'Accept-Encoding':'gzip, deflate','Accept':'text/html, application/xhtml+xml, */*','Accept-Language':'en-GB,it-IT;q=0.8,it;q=0.6,en-US;q=0.4,en;q=0.2'}
	if not bSingle and re.search("https://www.bedetheque.com/", url, re.IGNORECASE):
		bSingle = True

	if bSingle:
		requestUri = quote(url, safe = "%/:=&~#+$!,?;'@()*[]")
	else:
		requestUri = quote("https://www.bedetheque.com/" + url, safe = "%/:=&~#+$!,?;'@()*[]")
			
	#try:		
	#	req = Request (requestUri, None, headers)
	#	page = urlopen(req).read()
	#	Application.DoEvents()

	#except URLError, e:
	#	if DBGONOFF:print Trans(60)
	#	if DBGONOFF:print Trans(61), e
	#	cError = debuglog()
	#	log_BD("   [" + dlgName + "] " + dlgNumber + " Alt.No " + dlgAltNumber + " -> " , cError, 1)
	#	Result = MessageBox.Show(ComicRack.MainWindow, Trans(98) + cError ,Trans(97), MessageBoxButtons.OK, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button1)

	#return page

	try:
		System.Net.ServicePointManager.SecurityProtocol = System.Net.SecurityProtocolType.Tls12
		Req = System.Net.HttpWebRequest.Create(requestUri)		
		Req.CookieContainer = CookieContainer		
		#Req.CookieContainer.Add(System.Uri(requestUri), Cookie("__utma", "164207276.656597940.1352121294.1352232667.1352393821.4"))
		#Req.CookieContainer.Add(System.Uri(requestUri), Cookie("__utmb", "164207276.4.10.1352232512"))
		#Req.CookieContainer.Add(System.Uri(requestUri), Cookie("__utmc", "164207276"))
		#Req.CookieContainer.Add(System.Uri(requestUri), Cookie("__utmz", "164207276.1352121300.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)"))		
		#Req.CookieContainer.Add(System.Uri(requestUri), Cookie("SERVERID1", "A"))
		#Req.CookieContainer.Add(System.Uri(requestUri), Cookie("BELlangue","Français"))
		Req.Timeout = 15000
		Req.UserAgent = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; WOW64; Trident/6.0)'
		#Req.Headers.Add('Accept-Encoding','gzip, deflate')
		Req.AutomaticDecompression = DecompressionMethods.Deflate | DecompressionMethods.GZip		
		Req.Headers.Add('X-Powered-By', 'PHP/5.3.17')
		Req.Referer = requestUri
		Req.Accept = 'text/html, application/xhtml+xml, */*'
		Req.Headers.Add('Accept-Language','en-GB,it-IT;q=0.8,it;q=0.6,en-US;q=0.4,en;q=0.2')
		Req.KeepAlive = True		
		webresponse = Req.GetResponse()
		a = webresponse.Cookies	

		Application.DoEvents()

		inStream = webresponse.GetResponseStream()		
		encode = System.Text.Encoding.GetEncoding("utf-8")
		ReadStream = System.IO.StreamReader(inStream, encode)
		#ReadStream.BaseStream.ReadTimeout = 15000		
		page = ReadStream.ReadToEnd()
			
	except URLError, e:
		if DBGONOFF:print Trans(60)
		if DBGONOFF:print Trans(61), e
		cError = debuglog()
		log_BD("   [" + dlgName + "] " + dlgNumber + " Alt.No " + dlgAltNumber + " -> " , cError, 1)
		Result = MessageBox.Show(ComicRack.MainWindow, Trans(98) + cError ,Trans(97), MessageBoxButtons.OK, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button1)
	
	inStream.Close()
	webresponse.Close()
	
	return page

def isnumeric(nNum):

	try:
		n = float(nNum)
	except ValueError:
		return False
	else:
		return True

def checkWebChar(strIn):

	strIn = re.sub('&lt;', '<', strIn)
	strIn = re.sub('&gt;', '>', strIn)
	strIn = re.sub('&amp;', '&', strIn)
	strIn = re.sub('&nbsp;', ' ', strIn)
	strIn = re.sub('<br />', '', strIn)
	strIn = re.sub('&quot;', '"', strIn)
	strIn = re.sub('\x92', '\'', strIn)
	strIn = re.sub('\xc3', u'\xc3', strIn)
	strIn = re.sub('\xa2', u'\xa2', strIn)
	strIn = re.sub('\xc3', u'\xc3', strIn)

	return strIn 

def checkRegExp(strIn):

	strIn = re.sub('\\(', '.', strIn)
	strIn = re.sub('\\)', '.', strIn)
	strIn = re.sub('&', '&amp;', strIn)
	strIn = re.sub('\$', '\\$', strIn)
	
	return strIn

class MLStripper(HTMLParser):

	def __init__(self):
		self.reset()
		self.fed = []

	def handle_data(self, d):
		self.fed.append(d)

	def Set_data(self):
		return ''.join(self.fed)

def strip_tags(html):
	try:
		s = MLStripper()
		s.feed(html)
		return s.Set_data()
	except:
		return html

def thread_proc():	 
	
	pass
	
	def handle(w, a): 
		pass

def debuglog():

	global bError

	traceback = sys.exc_info()[2]
	stackTrace = []

	logfile = (__file__[:-len('BedethequeScraper2.py')] + "BD2_debug_log.txt")

	print "Writing Log to " + logfile
	print 'Caught ', sys.exc_info()[0].__name__, ': ', sstr(sys.exc_info()[1])

	log = open(logfile, 'a')
	log.write ("\n\n" + str(datetime.now().strftime("%A %d %B %Y %H:%M:%S")) + "\n")
	cError = sstr(sys.exc_info()[1])
	log.write ("".join(['Caught ', sys.exc_info()[0].__name__, ': ', cError, '\n']))


	while traceback is not None:
		frame = traceback.tb_frame
		lineno = traceback.tb_lineno
		code = frame.f_code
		filename = code.co_filename
		name = code.co_name
		stackTrace.append((filename, lineno, name))
		traceback = traceback.tb_next

	nL = 0
	for line in stackTrace:
		nL += 1
		print nL, "-", line
		log.write (",".join("%s" % tup for tup in line) + "\n")

	log.flush()
	log.close()

	bError = True

	return cError

def sstr(object):

	''' safely converts the given object into a  (sstr = safestr) '''
	if object is None:
		return '<None>'

	if type(object) is str:
		# this is needed, because str() breaks on some strings that have unicode
		# characters, due to a python bug (all strings in python are unicode).
		return object

	return str(object)

def isPositiveInt(value):

	try:
		return int(value) >= 0
	except:
		return False

def url_fix(s, charset='utf-8'):
		
	if isinstance(s, unicode):
		s = s.encode(charset, 'ignore')
		s = s.replace("/","-")
		
	scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
	path = quote(path, '/%')
	qs = quote_plus(qs, ':&=')

	return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))

def log_BD(bdstr, bdstat, lTime):

	bdlogfile = (__file__[:-len('BedethequeScraper2.py')] + "BD2_Rename_Log.txt")

	bdlog = open(bdlogfile, 'a')
	if lTime == 1:
		cDT = str(datetime.now().strftime("%A %d %B %Y %H:%M:%S")) + " > "

	else:
		cDT = ""

	bdlog.write (cDT.encode('utf-8') + bdstr.encode('utf-8') + "   " + bdstat.encode('utf-8') + "\n")
	
	bdlog.close()

def if_else(condition, trueVal, falseVal):

	if condition:
		return trueVal
	else:
		return falseVal

class ProgressBarDialog(Form):
	
	def __init__(self, nMax):
		
		global aWord, bStopit
		self.Text = Trans(62)
		#self.Size = Size(350, 150)
		self.Size = Size(350, 600)
		pIcon = (__file__[:-len('BedethequeScraper2.py')] + "BD2.ico")
		self.Icon = System.Drawing.Icon(pIcon)
		self.ControlBox = False
		self.HelpButton = True
		self.MaximizeBox = False
		self.MinimizeBox = False
		self.SizeGripStyle = System.Windows.Forms.SizeGripStyle.Hide
		self.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen
		self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog

		self.pb = ProgressBar()
		self.traitement = Label()
		self.cancel = Button()
		self.cover = PictureBox()

		self.traitement.Location = Point(20, 5)
		self.traitement.Name = "traitement"
		self.traitement.Size = Size(300, 50)
		self.traitement.Text = ""

		self.pb.Size = Size(300, 20)
		self.pb.Location = Point(20, 50)
		self.pb.Maximum = nMax
		self.pb.Minimum = 0
		self.pb.Step = 1
		self.pb.Value = 0
		self.pb.BackColor = Color.LightGreen
		self.pb.Text = ""
		self.pb.ForeColor = Color.Black

		self.cancel.DialogResult = DialogResult.Cancel
		self.cancel.Location = Point(140, 80)
		self.cancel.Name = "cancel"
		self.cancel.Size = Size(75, 25)
		self.cancel.TabIndex = 1
		self.cancel.Text = Trans(99)
		self.cancel.UseVisualStyleBackColor = True
		self.cancel.BackColor = Color.Red
		self.cancel.Click += self.button_Click

		self.cover.Location = Point(20, 110)
		self.cover.Name = "cover"
		self.cover.Size = Size(300, 430)
		self.cover.SizeMode = PictureBoxSizeMode.StretchImage

		self.Controls.Add(self.pb)
		self.Controls.Add(self.traitement)
		self.Controls.Add(self.cancel)
		self.Controls.Add(self.cover)

	def Update(self, cText, nInc = 1, book = False):
		Application.DoEvents()
		self.traitement.Text = "\n" + cText
		if nInc == 1: 
			self.pb.Increment(self.pb.Step)
			percent = int((float(self.pb.Value - self.pb.Minimum) / float(self.pb.Maximum - self.pb.Minimum)) * 100)
			self.Text = Trans(63) + percent.ToString() + "%"
			
		if book:
			cCovImage = (ComicRack.App.GetComicThumbnail(book, 0))

		else:
			cCovImage = (__file__[:-len('BedethequeScraper2.py')] + "BD2.png")

		if nInc == 1 or not book: 
			self.cover.Image = System.Drawing.Bitmap(cCovImage)

	def button_Click(self, sender, e):

		global bStopit

		Application.DoEvents()
		if sender.Name.CompareTo(self.cancel.Name) == 0:
			bStopit = True
	
def LoadSetting():

	global SHOWRENLOG, SHOWDBGLOG, DBGONOFF, DBGLOGMAX, RENLOGMAX, LANGENFR, aWord, ARTICLES, SUBPATT, COUNTOF, COUNTFINIE, TITLEIT, TIMEOUT, TIMEOUTS, TIMEPOPUP, FORMATARTICLES
	global TBTags, CBCover, CBStatus, CBGenre, CBNotes, CBWeb, CBCount, CBSynopsys,	CBImprint, CBLetterer, CBPrinted, CBRating, CBISBN, CBDefault, CBRescrape, CBStop, PopUpEditionForm, PadNumber
	global	CBLanguage,	CBEditor, CBFormat,	CBColorist,	CBPenciller, CBWriter, CBTitle, CBSeries, CBCouverture

	###############################################################
	# Config read #

	path = (__file__[:-len('BedethequeScraper2.py')])
	
	if not File.Exists(path + "\App.Config"):
		fs = File.Create(path + "\App.Config")
		info = System.Text.UTF8Encoding(True).GetBytes('<?xml version="1.0" encoding="UTF-8"?><configuration></configuration>')
		fs.Write(info, 0, info.Length)
		fs.Close()

	try:	
		MySettings = AppSettings()
		MySettings.Load(path + "\App.Config")
	except Exception as e:
		cError = debuglog()		
		return False

	try:
		SHOWRENLOG = ft(MySettings.Get("SHOWRENLOG"))
	except Exception as e:
		SHOWRENLOG = False
	try:
		SHOWDBGLOG = ft(MySettings.Get("SHOWDBGLOG"))
	except Exception as e:
		SHOWDBGLOG = False
	try:
		DBGONOFF = ft(MySettings.Get("DBGONOFF"))	
	except Exception as e:
		DBGONOFF = False
	try:
		DBGLOGMAX = int(MySettings.Get("DBGLOGMAX"))
	except Exception as e:
		DBGLOGMAX = 10000
	try:
		RENLOGMAX = int(MySettings.Get("RENLOGMAX"))
	except Exception as e:
		RENLOGMAX = 10000
	try:
		LANGENFR = MySettings.Get("LANGENFR")
	except Exception as e:
		LANGENFR = "FR"
	try:
		TBTags = MySettings.Get("TBTags")
	except Exception as e:
		TBTags = ""
	try:
		CBCover = ft(MySettings.Get("CBCover"))	
	except Exception as e:
		CBCover = True
	try:
		CBStatus = ft(MySettings.Get("CBStatus"))	
	except Exception as e:
		CBStatus = True
	try:
		CBGenre = ft(MySettings.Get("CBGenre"))	
	except Exception as e:
		CBGenre = True
	try:
		CBNotes = ft(MySettings.Get("CBNotes"))	
	except Exception as e:
		CBNotes = True
	try:
		CBWeb = ft(MySettings.Get("CBWeb"))	
	except Exception as e:
		CBWeb = True
	try:
		CBCount = ft(MySettings.Get("CBCount"))	
	except Exception as e:
		CBCount = True
	try:
		CBSynopsys = ft(MySettings.Get("CBSynopsys"))	
	except Exception as e:
		CBSynopsys = True
	try:
		CBImprint = ft(MySettings.Get("CBImprint"))	
	except Exception as e:
		CBImprint = True
	try:
		CBLetterer = ft(MySettings.Get("CBLetterer"))	
	except Exception as e:
		CBLetterer = True
	try:
		CBPrinted = ft(MySettings.Get("CBPrinted"))	
	except Exception as e:
		CBPrinted = True
	try:
		CBRating = ft(MySettings.Get("CBRating"))	
	except Exception as e:
		CBRating = True
	try:
		CBISBN = ft(MySettings.Get("CBISBN"))	
	except Exception as e:
		CBISBN = True
	try:
		CBLanguage = ft(MySettings.Get("CBLanguage"))	
	except Exception as e:
		CBLanguage = True
	try:
		CBEditor = ft(MySettings.Get("CBEditor"))	
	except Exception as e:
		CBEditor = True
	try:
		CBFormat = ft(MySettings.Get("CBFormat"))	
	except Exception as e:
		CBFormat = True
	try:
		CBColorist = ft(MySettings.Get("CBColorist"))	
	except Exception as e:
		CBColorist = True
	try:
		CBPenciller = ft(MySettings.Get("CBPenciller"))	
	except Exception as e:
		CBPenciller = True
	try:
		CBWriter = ft(MySettings.Get("CBWriter"))
	except Exception as e:
		CBWriter = True
	try:
		CBSeries = ft(MySettings.Get("CBSeries")	)
	except Exception as e:
		CBSeries = True
	try:
		CBTitle = ft(MySettings.Get("CBTitle"))	
	except Exception as e:
		CBTitle = True
	try:
		CBDefault = ft(MySettings.Get("CBDefault"))
	except Exception as e:
		CBDefault = False
	try:
		CBRescrape = ft(MySettings.Get("CBRescrape"))
	except Exception as e:
		CBRescrape = False
	try:
		CBStop = ft(MySettings.Get("CBStop"))
	except Exception as e:
		CBStop = "2"
	try:
		ARTICLES = MySettings.Get("ARTICLES")
	except Exception as e:
		ARTICLES = "Le,La,Les,L',The"
 	try:
		SUBPATT = MySettings.Get("SUBPATT")
	except Exception as e:
		SUBPATT = " - - "   	
	try:
		COUNTOF = ft(MySettings.Get("COUNTOF"))	
	except Exception as e:
		COUNTOF = True
	try:
		CBCouverture = ft(MySettings.Get("CBCouverture"))	
	except Exception as e:
		CBCouverture = True
	try:
		COUNTFINIE = ft(MySettings.Get("COUNTFINIE"))	
	except Exception as e:
		COUNTFINIE = True
	try:
		TITLEIT = ft(MySettings.Get("TITLEIT"))	
	except Exception as e:
		TITLEIT = True
	try:
		TIMEOUT = MySettings.Get("TIMEOUT")
	except Exception as e:
		TIMEOUT = "1000"
	try:
		TIMEOUTS = MySettings.Get("TIMEOUTS")
	except Exception as e:
		TIMEOUTS = "7"
	try:
		TIMEPOPUP = MySettings.Get("TIMEPOPUP")
	except Exception as e:
		TIMEPOPUP = "30"
	try:
		FORMATARTICLES = ft(MySettings.Get("FORMATARTICLES"))	
	except Exception as e:
		FORMATARTICLES = True
		
	try:
		PopUpEditionForm = ft(MySettings.Get("PopUpEditionForm"))	
	except Exception as e:
		PopUpEditionForm = False

	try:
		PadNumber = MySettings.Get("PadNumber")
	except Exception as e:
		PadNumber = "0"

	###############################################################
	
	SaveSetting()

	aWord = Translate()

	return True
	
def SaveSetting():

	global SHOWRENLOG, SHOWDBGLOG, DBGONOFF, DBGLOGMAX, RENLOGMAX, LANGENFR, aWord, ARTICLES, SUBPATT, COUNTOF, COUNTFINIE, TITLEIT, TIMEOUT, TIMEOUTS, TIMEPOPUP, FORMATARTICLES
	global TBTags, CBCover, CBStatus, CBGenre, CBNotes, CBWeb, CBCount, CBSynopsys,	CBImprint, CBLetterer, CBPrinted, CBRating, CBISBN, CBDefault, CBRescrape, CBStop, PopUpEditionForm, PadNumber
	global	CBLanguage,	CBEditor, CBFormat,	CBColorist,	CBPenciller, CBWriter, CBTitle, CBSeries, CBCouverture
	
	MySettings = AppSettings()
	
	MySettings.Set("SHOWRENLOG", tf(SHOWRENLOG))		
	MySettings.Set("SHOWDBGLOG", tf(SHOWDBGLOG))	
	MySettings.Set("DBGONOFF",  tf(DBGONOFF))	
	MySettings.Set("DBGLOGMAX", str(DBGLOGMAX))	
	MySettings.Set("RENLOGMAX",  str(RENLOGMAX))
	MySettings.Set("LANGENFR",  LANGENFR)
	MySettings.Set("TBTags",  TBTags)
	MySettings.Set("CBCover",  tf(CBCover))	
	MySettings.Set("CBStatus",  tf(CBStatus))	
	MySettings.Set("CBGenre",  tf(CBGenre))	
	MySettings.Set("CBNotes",  tf(CBNotes))	
	#MySettings.Set("CBWeb",  tf(CBWeb))	
	if CBWeb == True:
		MySettings.Set("CBWeb",  "1")	
	elif CBWeb == False:
		MySettings.Set("CBWeb",  "0")	
	elif CBWeb == "2":
		MySettings.Set("CBWeb",  "2")	

	MySettings.Set("CBCount",  tf(CBCount))	
	MySettings.Set("CBSynopsys",  tf(CBSynopsys))	
	MySettings.Set("CBImprint",  tf(CBImprint))	
	MySettings.Set("CBLetterer",  tf(CBLetterer))	
	MySettings.Set("CBPrinted",  tf(CBPrinted))	
	MySettings.Set("CBRating",  tf(CBRating))	
	MySettings.Set("CBISBN",  tf(CBISBN))	
	MySettings.Set("CBLanguage",  tf(CBLanguage))	
	MySettings.Set("CBEditor",  tf(CBEditor))	
	MySettings.Set("CBFormat",  tf(CBFormat))	
	MySettings.Set("CBColorist",  tf(CBColorist))
	MySettings.Set("CBPenciller",  tf(CBPenciller))	
	MySettings.Set("CBWriter",  tf(CBWriter))	
	MySettings.Set("CBSeries",  tf(CBSeries))	
	MySettings.Set("CBTitle",  tf(CBTitle))	
	MySettings.Set("CBDefault",  tf(CBDefault))	
	MySettings.Set("CBRescrape",  tf(CBRescrape))	
	MySettings.Set("ARTICLES",  ARTICLES)
 	MySettings.Set("SUBPATT",  SUBPATT)   
	MySettings.Set("COUNTOF",  tf(COUNTOF))	
	MySettings.Set("CBCouverture",  tf(CBCouverture))	
	MySettings.Set("COUNTFINIE",  tf(COUNTFINIE))	
	MySettings.Set("TITLEIT",  tf(TITLEIT))	
	MySettings.Set("TIMEOUT",  TIMEOUT)
	MySettings.Set("TIMEOUTS",  TIMEOUTS) 
	MySettings.Set("TIMEPOPUP",  TIMEPOPUP)
	MySettings.Set("FORMATARTICLES", tf(FORMATARTICLES))
	MySettings.Set("PopUpEditionForm", tf(PopUpEditionForm))
	MySettings.Set("PadNumber", PadNumber)

	if CBStop == True:
		MySettings.Set("CBStop",  "1")	
	elif CBStop == False:
		MySettings.Set("CBStop",  "0")	
	elif CBStop == "2":
		MySettings.Set("CBStop",  "2")	
													
	MySettings.Save((__file__[:-len('BedethequeScraper2.py')] + "App.Config"))

class AppSettings(object):

	def __init__(self):
		self._FilePath = ""
		self._SetUp(BasicXml)

	def _SetUp(self, Xml):
		self.Document = XmlDocument()
		self.Document.LoadXml(Xml)

	def Get(self, Name):
		Value = self.Document.SelectSingleNode("/configuration/" + Name).InnerText
		return Value

	def Set(self, Name, Value): 
		ValTrue = self.Document.SelectSingleNode("/configuration/" + Name)
		if ValTrue:
			self.Document.SelectSingleNode("/configuration/" + Name).InnerText = Value
		else:
			ValNode = self.Document.CreateElement(Name)        
			ValNode.InnerText = Value
			self.Document.DocumentElement.AppendChild(ValNode)

	def Load(self, FilePath):
		self._FilePath = FilePath
		rawXML = File.ReadAllText(self._FilePath)
		self._SetUp(rawXML)

	def Save(self, FilePath):
		self._FilePath = FilePath		
		xd = XmlDocument()
		xd.LoadXml(self.Document.OuterXml)
		sb = StringBuilder()
		sw = System.IO.StringWriter(sb)
		xtw = XmlTextWriter(sw)
		xtw.Formatting = Formatting.Indented
		xd.WriteTo(xtw)
		rawXML = File.WriteAllText(self._FilePath, sb.ToString())

def ft(n):
	if n == "1":
		return True
	elif n== "0":
		return False
	elif n== "2":
		return "2"

def tf(bool):
	if bool == True:
		return "1"
	elif bool == False:
		return "0"
	elif bool == "2":
		return "2"

class BDConfigForm(Form):

	global aWord

	def __init__(self):

		global SHOWRENLOG, SHOWDBGLOG, DBGONOFF, DBGLOGMAX, RENLOGMAX, LANGENFR, aWord, ARTICLES, SUBPATT, COUNTOF, COUNTFINIE, TITLEIT, TIMEOUT, TIMEOUTS, TIMEPOPUP, FORMATARTICLES
		global TBTags, CBCover, CBStatus, CBGenre, CBNotes, CBWeb, CBCount, CBSynopsys,	CBImprint, CBLetterer, CBPrinted, CBRating, CBISBN, CBDefault, CBRescrape, CBStop, PopUpEditionForm, PadNumber
		global CBLanguage, CBEditor, CBFormat,	CBColorist,	CBPenciller, CBWriter, CBTitle, CBSeries, CBCouverture

		self.Name = "BDConfigForm"
		self.Text = "Bedetheque Scraper 2"
		pIcon = (__file__[:-len('BedethequeScraper2.py')] + "BD2.ico")
		self.Icon = System.Drawing.Icon(pIcon)		
		self.HelpButton = False
		self.MaximizeBox = False
		self.MinimizeBox = False
		self.SizeGripStyle = System.Windows.Forms.SizeGripStyle.Hide
		self.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen
		self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog

		self._TabData = System.Windows.Forms.TabControl()
		self._tabPage1 = System.Windows.Forms.TabPage()
		self._tabPage2 = System.Windows.Forms.TabPage()
		self._label5 = System.Windows.Forms.Label()
		self._TBTags = System.Windows.Forms.TextBox()
		self._CBCover = System.Windows.Forms.CheckBox()
		self._CBCouverture = System.Windows.Forms.CheckBox()		
		self._CBStatus = System.Windows.Forms.CheckBox()
		self._CBGenre = System.Windows.Forms.CheckBox()
		self._CBNotes = System.Windows.Forms.CheckBox()
		self._CBWeb = System.Windows.Forms.CheckBox()
		self._CBCount = System.Windows.Forms.CheckBox()
		self._CBSynopsys = System.Windows.Forms.CheckBox()
		self._CBImprint = System.Windows.Forms.CheckBox()
		self._CBLetterer = System.Windows.Forms.CheckBox()
		self._CBPrinted = System.Windows.Forms.CheckBox()
		self._CBRating = System.Windows.Forms.CheckBox()
		self._CBISBN = System.Windows.Forms.CheckBox()
		self._CBLanguage = System.Windows.Forms.CheckBox()
		self._CBEditor = System.Windows.Forms.CheckBox()
		self._CBFormat = System.Windows.Forms.CheckBox()
		self._CBColorist = System.Windows.Forms.CheckBox()
		self._CBPenciller = System.Windows.Forms.CheckBox()
		self._CBWriter = System.Windows.Forms.CheckBox()
		self._CBTitle = System.Windows.Forms.CheckBox()
		self._CBSeries = System.Windows.Forms.CheckBox()
		self._CancelButton = System.Windows.Forms.Button()
		self._OKButton = System.Windows.Forms.Button()
		self._label1 = System.Windows.Forms.Label()		
		self._label2 = System.Windows.Forms.Label()		
		self._label3 = System.Windows.Forms.Label()
		self._label4 = System.Windows.Forms.Label()		
		self._label6 = System.Windows.Forms.Label()		
		self._labelArt = System.Windows.Forms.Label()
		self._RENLOGMAX = System.Windows.Forms.TextBox()		
		self._DBGLOGMAX = System.Windows.Forms.TextBox()
		self._DBGONOFF = System.Windows.Forms.CheckBox()
		self._SHOWDBGLOG = System.Windows.Forms.CheckBox()
		self._SHOWRENLOG = System.Windows.Forms.CheckBox()
		self._radioENG = System.Windows.Forms.RadioButton()
		self._radioFRE = System.Windows.Forms.RadioButton()
		self._PB1 = System.Windows.Forms.PictureBox()
		self._ButtonReset = System.Windows.Forms.Button()		
		self._ARTICLES = System.Windows.Forms.TextBox()
#modif kiwi
		self._SUBPATT = System.Windows.Forms.TextBox()
		self._labelSUBPATT = System.Windows.Forms.Label()
		self._COUNTOF = System.Windows.Forms.CheckBox()
		self._COUNTFINIE = System.Windows.Forms.CheckBox()
		self._TITLEIT = System.Windows.Forms.CheckBox()
		self._FORMATARTICLES = System.Windows.Forms.CheckBox()
		self._PopUpEditionForm = System.Windows.Forms.CheckBox()
		self._TIMEOUT = System.Windows.Forms.TextBox()
		self._TIMEOUTS = System.Windows.Forms.TextBox()
#modif kiwi
		self._TIMEPOPUP = System.Windows.Forms.TextBox()
		self._labelTIMEPOPUP = System.Windows.Forms.Label()
		self._PadNumber = System.Windows.Forms.TextBox()
		self._labelPadNumber = System.Windows.Forms.Label()
		self._CBDefault = System.Windows.Forms.CheckBox()
		self._CBRescrape = System.Windows.Forms.CheckBox()		
		self._CBStop = System.Windows.Forms.CheckBox()		
		self._TabData.SuspendLayout()
		self._tabPage1.SuspendLayout()
		self._tabPage2.SuspendLayout()
		self._PB1.BeginInit()
		self.SuspendLayout()
		#
		# TabData
		#
		self._TabData.Controls.Add(self._tabPage1)
		self._TabData.Controls.Add(self._tabPage2)
		self._TabData.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._TabData.Location = System.Drawing.Point(0, 0)
		self._TabData.Name = "TabData"
		self._TabData.SelectedIndex = 0
		self._TabData.Size = System.Drawing.Size(512, 412)
		self._TabData.TabIndex = 22
		#
		# tabPage1
		#
		self._tabPage1.Controls.Add(self._PB1)		
		self._tabPage1.Controls.Add(self._CancelButton)
		self._tabPage1.Controls.Add(self._OKButton)				
		self._tabPage1.Controls.Add(self._label3)		
		self._tabPage1.Controls.Add(self._label2)		
		self._tabPage1.Controls.Add(self._RENLOGMAX)		
		self._tabPage1.Controls.Add(self._label1)
		self._tabPage1.Controls.Add(self._DBGLOGMAX)
		self._tabPage1.Controls.Add(self._DBGONOFF)
		self._tabPage1.Controls.Add(self._SHOWDBGLOG)
		self._tabPage1.Controls.Add(self._SHOWRENLOG)
		self._tabPage1.Controls.Add(self._radioENG)
		self._tabPage1.Controls.Add(self._radioFRE)						
		self._tabPage1.Controls.Add(self._ARTICLES)	
		self._tabPage1.Controls.Add(self._labelArt)	
#modif kiwi
		self._tabPage1.Controls.Add(self._SUBPATT)
		self._tabPage1.Controls.Add(self._labelSUBPATT)	
		self._tabPage1.Controls.Add(self._COUNTOF)
		self._tabPage1.Controls.Add(self._COUNTFINIE)
		self._tabPage1.Controls.Add(self._TITLEIT)
		self._tabPage1.Controls.Add(self._FORMATARTICLES)		
		self._tabPage1.Controls.Add(self._PopUpEditionForm)	
		self._tabPage1.Controls.Add(self._TIMEOUT)
		self._tabPage1.Controls.Add(self._TIMEOUTS)
#modif kiwi
		self._tabPage1.Controls.Add(self._TIMEPOPUP)
 		self._tabPage1.Controls.Add(self._labelTIMEPOPUP)
		self._tabPage1.Controls.Add(self._PadNumber)
 		self._tabPage1.Controls.Add(self._labelPadNumber)
		self._tabPage1.Controls.Add(self._label4)		
		self._tabPage1.Controls.Add(self._label6)	
		self._tabPage1.Location = System.Drawing.Point(4, 22)
		self._tabPage1.Name = "tabPage1"
		self._tabPage1.Padding = System.Windows.Forms.Padding(3)
		self._tabPage1.Size = System.Drawing.Size(500, 400)
		self._tabPage1.TabIndex = 0
		self._tabPage1.Text = Trans(95)
		self._tabPage1.UseVisualStyleBackColor = True
		self._tabPage1.Tag = "Tab"
		#
		# tabPage2
		#
		self._tabPage2.Controls.Add(self._ButtonReset)
		self._tabPage2.Controls.Add(self._label5)
		self._tabPage2.Controls.Add(self._TBTags)
		self._tabPage2.Controls.Add(self._CBCover)
		self._tabPage2.Controls.Add(self._CBCouverture)		
		self._tabPage2.Controls.Add(self._CBStatus)
		self._tabPage2.Controls.Add(self._CBGenre)
		self._tabPage2.Controls.Add(self._CBNotes)
		self._tabPage2.Controls.Add(self._CBWeb)
		self._tabPage2.Controls.Add(self._CBCount)
		self._tabPage2.Controls.Add(self._CBSynopsys)
		self._tabPage2.Controls.Add(self._CBImprint)
		self._tabPage2.Controls.Add(self._CBLetterer)
		self._tabPage2.Controls.Add(self._CBPrinted)
		self._tabPage2.Controls.Add(self._CBRating)
		self._tabPage2.Controls.Add(self._CBISBN)
		self._tabPage2.Controls.Add(self._CBLanguage)
		self._tabPage2.Controls.Add(self._CBEditor)
		self._tabPage2.Controls.Add(self._CBFormat)
		self._tabPage2.Controls.Add(self._CBColorist)
		self._tabPage2.Controls.Add(self._CBPenciller)
		self._tabPage2.Controls.Add(self._CBWriter)
		self._tabPage2.Controls.Add(self._CBTitle)
		self._tabPage2.Controls.Add(self._CBSeries)
		self._tabPage2.Controls.Add(self._CBDefault)		
		self._tabPage1.Controls.Add(self._CBRescrape)		
		self._tabPage1.Controls.Add(self._CBStop)		
		self._tabPage2.Location = System.Drawing.Point(4, 22)
		self._tabPage2.Name = "tabPage2"
		self._tabPage2.Padding = System.Windows.Forms.Padding(3)
		self._tabPage2.Size = System.Drawing.Size(500, 400)
		self._tabPage2.TabIndex = 1
		self._tabPage2.Text = Trans(96)
		self._tabPage2.UseVisualStyleBackColor = True
		self._tabPage2.Tag = "Tab"
		#
		# label5
		#
		self._label5.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._label5.Location = System.Drawing.Point(352, 181)
		self._label5.Name = "label5"
		self._label5.Size = System.Drawing.Size(56, 24)
		self._label5.TabIndex = 99
		self._label5.Text = Trans(91)
		self._label5.Tag = "Label"
		self._label5.TextAlign = System.Drawing.ContentAlignment.MiddleLeft
		#
		# TBTags
		#
		self._TBTags.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._TBTags.Location = System.Drawing.Point(336, 211)
		self._TBTags.MaxLength = 255
		self._TBTags.Name = "TBTags"
		self._TBTags.Size = System.Drawing.Size(80, 20)
		self._TBTags.TabIndex = 40
		self._TBTags.Text = TBTags
		#
		# CBDefault
		#
		self._CBDefault.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBDefault.Location = System.Drawing.Point(336, 11)
		self._CBDefault.Name = "CBDefault"
		self._CBDefault.Size = System.Drawing.Size(104, 24)
		self._CBDefault.TabIndex = 38
		self._CBDefault.Text = Trans(136)
		self._CBDefault.UseVisualStyleBackColor = True
		self._CBDefault.CheckState = if_else(CBDefault, CheckState.Checked, CheckState.Unchecked)
		#
		# CBCover
		#
		self._CBCover.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBCover.Location = System.Drawing.Point(248, 211)
		self._CBCover.Name = "CBCover"
		self._CBCover.Size = System.Drawing.Size(104, 24)
		self._CBCover.TabIndex = 38
		self._CBCover.Text = Trans(90)
		self._CBCover.UseVisualStyleBackColor = True
		self._CBCover.CheckState = if_else(CBCover, CheckState.Checked, CheckState.Unchecked)
		#
		# CBCouverture
		#
		self._CBCouverture.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBCouverture.Location = System.Drawing.Point(16, 251)
		self._CBCouverture.Name = "CBCouverture"
		self._CBCouverture.Size = System.Drawing.Size(104, 24)
		self._CBCouverture.TabIndex = 14
		self._CBCouverture.Text = Trans(121)
		self._CBCouverture.UseVisualStyleBackColor = True
		self._CBCouverture.CheckState = if_else(CBCover, CheckState.Checked, CheckState.Unchecked)		
		#
		# CBStatus
		#
		self._CBStatus.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBStatus.Location = System.Drawing.Point(248, 91)
		self._CBStatus.Name = "CBStatus"
		self._CBStatus.Size = System.Drawing.Size(104, 24)
		self._CBStatus.TabIndex = 23
		self._CBStatus.Text = Trans(87)
		self._CBStatus.UseVisualStyleBackColor = True
		self._CBStatus.CheckState = if_else(CBStatus, CheckState.Checked, CheckState.Unchecked)
		#
		# CBGenre
		#
		self._CBGenre.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBGenre.Location = System.Drawing.Point(248, 171)
		self._CBGenre.Name = "CBGenre"
		self._CBGenre.Size = System.Drawing.Size(104, 24)
		self._CBGenre.TabIndex = 37
		self._CBGenre.Text = Trans(89)
		self._CBGenre.UseVisualStyleBackColor = True
		self._CBGenre.CheckState = if_else(CBGenre, CheckState.Checked, CheckState.Unchecked)
		#
		# CBNotes
		#
		self._CBNotes.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBNotes.Location = System.Drawing.Point(248, 51)
		self._CBNotes.Name = "CBNotes"
		self._CBNotes.Size = System.Drawing.Size(104, 24)
		self._CBNotes.TabIndex = 22
		self._CBNotes.Text = Trans(86)
		self._CBNotes.UseVisualStyleBackColor = True
		self._CBNotes.CheckState = if_else(CBNotes, CheckState.Checked, CheckState.Unchecked)
		#
		# CBWeb
		#
		self._CBWeb.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBWeb.Location = System.Drawing.Point(248, 131)
		self._CBWeb.Name = "CBWeb"
		self._CBWeb.Size = System.Drawing.Size(104, 24)
		self._CBWeb.TabIndex = 36
		self._CBWeb.Text = Trans(88)
		self._CBWeb.UseVisualStyleBackColor = True
		self._CBWeb.ThreeState = True
		if CBWeb == True:
			self._CBWeb.CheckState = CheckState.Checked
		elif  CBWeb == False:
			self._CBWeb.CheckState = CheckState.Unchecked
		elif CBWeb == "2":
			self._CBWeb.CheckState = CheckState.Indeterminate
		#self._CBWeb.CheckState = if_else(CBWeb, CheckState.Checked, CheckState.Unchecked)

		#
		# CBCount
		#
		self._CBCount.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBCount.Location = System.Drawing.Point(248, 11)
		self._CBCount.Name = "CBCount"
		self._CBCount.Size = System.Drawing.Size(84, 24)
		self._CBCount.TabIndex = 21
		self._CBCount.Text = Trans(85)
		self._CBCount.UseVisualStyleBackColor = True
		self._CBCount.CheckState = if_else(CBCount, CheckState.Checked, CheckState.Unchecked)
		#
		# CBSynopsys
		#
		self._CBSynopsys.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBSynopsys.Location = System.Drawing.Point(136, 251)
		self._CBSynopsys.Name = "CBSynopsys"
		self._CBSynopsys.Size = System.Drawing.Size(104, 24)
		self._CBSynopsys.TabIndex = 20
		self._CBSynopsys.Text = Trans(84)
		self._CBSynopsys.UseVisualStyleBackColor = True
		self._CBSynopsys.CheckState = if_else(CBSynopsys, CheckState.Checked, CheckState.Unchecked)
		#
		# CBImprint
		#
		self._CBImprint.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBImprint.Location = System.Drawing.Point(136, 211)
		self._CBImprint.Name = "CBImprint"
		self._CBImprint.Size = System.Drawing.Size(104, 24)
		self._CBImprint.TabIndex = 19
		self._CBImprint.Text = Trans(83)
		self._CBImprint.UseVisualStyleBackColor = True
		self._CBImprint.CheckState = if_else(CBImprint, CheckState.Checked, CheckState.Unchecked)
		#
		# CBLetterer
		#
		self._CBLetterer.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBLetterer.Location = System.Drawing.Point(16, 211)
		self._CBLetterer.Name = "CBLetterer"
		self._CBLetterer.Size = System.Drawing.Size(104, 24)
		self._CBLetterer.TabIndex = 13
		self._CBLetterer.Text = Trans(76)
		self._CBLetterer.UseVisualStyleBackColor = True
		self._CBLetterer.CheckState = if_else(CBLetterer, CheckState.Checked, CheckState.Unchecked)
		#
		# CBPrinted
		#
		self._CBPrinted.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBPrinted.Location = System.Drawing.Point(136, 171)
		self._CBPrinted.Name = "CBPrinted"
		self._CBPrinted.Size = System.Drawing.Size(104, 24)
		self._CBPrinted.TabIndex = 18
		self._CBPrinted.Text = Trans(82)
		self._CBPrinted.UseVisualStyleBackColor = True
		self._CBPrinted.CheckState = if_else(CBPrinted, CheckState.Checked, CheckState.Unchecked)
		#
		# CBRating
		#
		self._CBRating.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBRating.Location = System.Drawing.Point(136, 131)
		self._CBRating.Name = "CBRating"
		self._CBRating.Size = System.Drawing.Size(104, 24)
		self._CBRating.TabIndex = 17
		self._CBRating.Text = Trans(81)
		self._CBRating.UseVisualStyleBackColor = True
		self._CBRating.CheckState = if_else(CBRating, CheckState.Checked, CheckState.Unchecked)
		#
		# CBISBN
		#
		self._CBISBN.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBISBN.Location = System.Drawing.Point(248, 251)
		self._CBISBN.Name = "CBISBN"
		self._CBISBN.Size = System.Drawing.Size(104, 24)
		self._CBISBN.TabIndex = 39
		self._CBISBN.Text = Trans(80)
		self._CBISBN.UseVisualStyleBackColor = True
		self._CBISBN.CheckState = if_else(CBISBN, CheckState.Checked, CheckState.Unchecked)
		#
		# CBLanguage
		#
		self._CBLanguage.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBLanguage.Location = System.Drawing.Point(136, 51)
		self._CBLanguage.Name = "CBLanguage"
		self._CBLanguage.Size = System.Drawing.Size(104, 24)
		self._CBLanguage.TabIndex = 15
		self._CBLanguage.Text = Trans(79)
		self._CBLanguage.UseVisualStyleBackColor = True
		self._CBLanguage.CheckState = if_else(CBLanguage, CheckState.Checked, CheckState.Unchecked)
		#
		# CBEditor
		#
		self._CBEditor.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBEditor.Location = System.Drawing.Point(136, 11)
		self._CBEditor.Name = "CBEditor"
		self._CBEditor.Size = System.Drawing.Size(104, 24)
		self._CBEditor.TabIndex = 14
		self._CBEditor.Text = Trans(78)
		self._CBEditor.UseVisualStyleBackColor = True
		self._CBEditor.CheckState = if_else(CBEditor, CheckState.Checked, CheckState.Unchecked)
		#
		# CBFormat
		#
		self._CBFormat.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBFormat.Location = System.Drawing.Point(136, 91)
		self._CBFormat.Name = "CBFormat"
		self._CBFormat.Size = System.Drawing.Size(104, 24)
		self._CBFormat.TabIndex = 16
		self._CBFormat.Text = Trans(77)
		self._CBFormat.UseVisualStyleBackColor = True
		self._CBFormat.CheckState = if_else(CBFormat, CheckState.Checked, CheckState.Unchecked)
		#
		# CBColorist
		#
		self._CBColorist.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBColorist.Location = System.Drawing.Point(16, 171)
		self._CBColorist.Name = "CBColorist"
		self._CBColorist.Size = System.Drawing.Size(104, 24)
		self._CBColorist.TabIndex = 12
		self._CBColorist.Text = Trans(75)
		self._CBColorist.UseVisualStyleBackColor = True
		self._CBColorist.CheckState = if_else(CBColorist, CheckState.Checked, CheckState.Unchecked)
		#
		# CBPenciller
		#
		self._CBPenciller.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBPenciller.Location = System.Drawing.Point(16, 131)
		self._CBPenciller.Name = "CBPenciller"
		self._CBPenciller.Size = System.Drawing.Size(104, 24)
		self._CBPenciller.TabIndex = 11
		self._CBPenciller.Text = Trans(74)
		self._CBPenciller.UseVisualStyleBackColor = True
		self._CBPenciller.CheckState = if_else(CBPenciller, CheckState.Checked, CheckState.Unchecked)
		#
		# CBWriter
		#
		self._CBWriter.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBWriter.Location = System.Drawing.Point(16, 91)
		self._CBWriter.Name = "CBWriter"
		self._CBWriter.Size = System.Drawing.Size(104, 24)
		self._CBWriter.TabIndex = 10
		self._CBWriter.Text = Trans(73)
		self._CBWriter.UseVisualStyleBackColor = True
		self._CBWriter.CheckState = if_else(CBWriter, CheckState.Checked, CheckState.Unchecked)
		#
		# CBTitle
		#
		self._CBTitle.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBTitle.Location = System.Drawing.Point(16, 51)
		self._CBTitle.Name = "CBTitle"
		self._CBTitle.Size = System.Drawing.Size(104, 24)
		self._CBTitle.TabIndex = 9
		self._CBTitle.Text = Trans(72)
		self._CBTitle.UseVisualStyleBackColor = True
		self._CBTitle.CheckState = if_else(CBTitle, CheckState.Checked, CheckState.Unchecked)
		#
		# CBSeries
		#
		self._CBSeries.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBSeries.Location = System.Drawing.Point(16, 11)
		self._CBSeries.Name = "CBSeries"
		self._CBSeries.Size = System.Drawing.Size(104, 24)
		self._CBSeries.TabIndex = 8
		self._CBSeries.Text = Trans(71)
		self._CBSeries.UseVisualStyleBackColor = True
		self._CBSeries.CheckState = if_else(CBSeries, CheckState.Checked, CheckState.Unchecked)
		#
		# CancelButton
		#
		self._CancelButton.BackColor = System.Drawing.Color.Red
		self._CancelButton.DialogResult = System.Windows.Forms.DialogResult.Cancel
		self._CancelButton.Font = System.Drawing.Font("Microsoft Sans Serif", 9, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, 0)
		self._CancelButton.Location = System.Drawing.Point(420, 350)
		self._CancelButton.Name = "CancelButton"
		self._CancelButton.Size = System.Drawing.Size(75, 32)
		self._CancelButton.TabIndex = 30
		self._CancelButton.Text = Trans(93)
		self._CancelButton.UseVisualStyleBackColor = False
		#
		# OKButton
		#
		self._OKButton.BackColor = System.Drawing.Color.FromArgb(128, 255, 128)
		self._OKButton.DialogResult = System.Windows.Forms.DialogResult.OK
		self._OKButton.Font = System.Drawing.Font("Microsoft Sans Serif", 9, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, 0)
		self._OKButton.ForeColor = System.Drawing.Color.Black
		self._OKButton.Location = System.Drawing.Point(8, 350)
		self._OKButton.Name = "OKButton"
		self._OKButton.Size = System.Drawing.Size(75, 32)
		self._OKButton.TabIndex = 29
		self._OKButton.Text = Trans(92)
		self._OKButton.UseVisualStyleBackColor = False
		self._OKButton.Click += self.button_Click
		#
		# ButtonReset
		#
		self._ButtonReset.BackColor = System.Drawing.Color.FromArgb(255, 192, 128)
		self._ButtonReset.Font = System.Drawing.Font("Microsoft Sans Serif", 9, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, 0)
		self._ButtonReset.Location = System.Drawing.Point(336, 128)
		self._ButtonReset.Name = "ButtonReset"
		self._ButtonReset.Size = System.Drawing.Size(75, 30)
		self._ButtonReset.TabIndex = 53
		self._ButtonReset.Text = Trans(94)
		self._ButtonReset.UseVisualStyleBackColor = False
		self._ButtonReset.Tag = "Button"
		self._ButtonReset.Click += self.button_Click
		#
		# label3
		#
		self._label3.Font = System.Drawing.Font("Microsoft Sans Serif", 6.75, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._label3.ImageAlign = System.Drawing.ContentAlignment.BottomCenter
		self._label3.Location = System.Drawing.Point(114, 360)
		self._label3.Name = "label3"
		self._label3.Size = System.Drawing.Size(264, 16)
		self._label3.TabIndex = 19
		self._label3.Text = "Version " + VERSION + " (c) 2021 kiwi13 && maforget"
		self._label3.TextAlign = System.Drawing.ContentAlignment.BottomCenter
		#
		# label1
		#
		self._label1.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._label1.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
		self._label1.Location = System.Drawing.Point(96, 120)
		self._label1.Name = "label1"
		self._label1.Size = System.Drawing.Size(124, 21)
		self._label1.TabIndex = 16
		self._label1.Text = Trans(69)
		#
		# DBGLOGMAX
		#
		self._DBGLOGMAX.Location = System.Drawing.Point(8, 120)
		self._DBGLOGMAX.Name = "DBGLOGMAX"
		self._DBGLOGMAX.Size = System.Drawing.Size(72, 23)
		self._DBGLOGMAX.TabIndex = 4
		self._DBGLOGMAX.Text = str(DBGLOGMAX)
		#
		# labelArt
		#
		self._labelArt.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._labelArt.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
		self._labelArt.Location = System.Drawing.Point(250, 80)
		self._labelArt.Name = "labelArt"
		self._labelArt.Size = System.Drawing.Size(184, 17)
		self._labelArt.TabIndex = 18
		self._labelArt.Text = Trans(109)
		#
		# ARTICLES
		#
		self._ARTICLES.Location = System.Drawing.Point(320, 80)
		self._ARTICLES.Name = "ARTICLES"
		self._ARTICLES.Size = System.Drawing.Size(180, 20)
		self._ARTICLES.TabIndex = 19
		self._ARTICLES.Text = ARTICLES
#modif kiwi
		#
		# label chaine à supp
		#
		self._labelSUBPATT.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._labelSUBPATT.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
		self._labelSUBPATT.Location = System.Drawing.Point(8, 324)
		self._labelSUBPATT.Name = "labelSubPatt"
		self._labelSUBPATT.Size = System.Drawing.Size(184, 17)
		self._labelSUBPATT.TabIndex = 100
		self._labelSUBPATT.Text = "Chaîne fin nom de série"
		#
		# Pattern a supp
		#
		self._SUBPATT.Location = System.Drawing.Point(180, 320)
		self._SUBPATT.Name = "PATTSUB"
		self._SUBPATT.Size = System.Drawing.Size(130, 20)
		self._SUBPATT.TabIndex = 101
		self._SUBPATT.Text = SUBPATT
		#
		# label time out popup
		#
		self._labelTIMEPOPUP.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._labelTIMEPOPUP.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
		self._labelTIMEPOPUP.Location = System.Drawing.Point(8, 266)
		self._labelTIMEPOPUP.Name = "labelTimePopup"
		self._labelTIMEPOPUP.Size = System.Drawing.Size(184, 17)
		self._labelTIMEPOPUP.TabIndex = 102
		self._labelTIMEPOPUP.Text = "Durée pop-up choix (en s)"
		#
		# time out popup
		#
		self._TIMEPOPUP.Location = System.Drawing.Point(180, 262)
		self._TIMEPOPUP.Name = "TIMEPOPUP"
		self._TIMEPOPUP.Size = System.Drawing.Size(50, 20)
		self._TIMEPOPUP.TabIndex = 103
		self._TIMEPOPUP.MaxLength = 3
		self._TIMEPOPUP.TextAlign = HorizontalAlignment.Center
		self._TIMEPOPUP.Text = TIMEPOPUP
 ##############
		#
		# label pad number
		#
		self._labelPadNumber.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._labelPadNumber.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
		self._labelPadNumber.Location = System.Drawing.Point(8, 295)
		self._labelPadNumber.Name = "labelPadNumber"
		self._labelPadNumber.Size = System.Drawing.Size(184, 23)
		self._labelPadNumber.TabIndex = 104
		self._labelPadNumber.Text = Trans(148)
		#
		# pad number
		#
		self._PadNumber.Location = System.Drawing.Point(180, 291)
		self._PadNumber.Name = "PadNumber"
		self._PadNumber.Size = System.Drawing.Size(50, 20)
		self._PadNumber.TabIndex = 105
		self._PadNumber.MaxLength = 3
		self._PadNumber.TextAlign = HorizontalAlignment.Center
		self._PadNumber.Text = PadNumber
		#
		# label2
		#
		self._label2.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._label2.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
		self._label2.Location = System.Drawing.Point(96, 160)
		self._label2.Name = "label2"
		self._label2.Size = System.Drawing.Size(124, 21)
		self._label2.TabIndex = 20
		self._label2.Text = Trans(70)
		#
		# RENLOGMAX
		#
		self._RENLOGMAX.Location = System.Drawing.Point(8, 160)
		self._RENLOGMAX.Name = "RENLOGMAX"
		self._RENLOGMAX.Size = System.Drawing.Size(72, 23)
		self._RENLOGMAX.TabIndex = 5
		self._RENLOGMAX.Text = str(RENLOGMAX)
		#
		# CBRescrape
		#
		self._CBRescrape.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBRescrape.Location = System.Drawing.Point(320, 105)
		self._CBRescrape.Name = "CBRescrape"
		self._CBRescrape.Size = System.Drawing.Size(180, 20)
		self._CBRescrape.TabIndex = 21
		self._CBRescrape.Text = Trans(137)
		self._CBRescrape.UseVisualStyleBackColor = True
		self._CBRescrape.CheckState = if_else(CBRescrape, CheckState.Checked, CheckState.Unchecked)
		#
		# COUNTOF
		#
		self._COUNTOF.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._COUNTOF.Location = System.Drawing.Point(320, 128)
		self._COUNTOF.Name = "COUNTOF"
		self._COUNTOF.Size = System.Drawing.Size(180, 20)
		self._COUNTOF.TabIndex = 22
		self._COUNTOF.Text = Trans(110)
		self._COUNTOF.UseVisualStyleBackColor = True
		self._COUNTOF.CheckState = if_else(COUNTOF, CheckState.Checked, CheckState.Unchecked)		
		#
		# COUNTFINIE
		#
		self._COUNTFINIE.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._COUNTFINIE.Location = System.Drawing.Point(320, 150)
		self._COUNTFINIE.Name = "COUNTFINIE"
		self._COUNTFINIE.Size = System.Drawing.Size(180, 20)
		self._COUNTFINIE.TabIndex = 23
		self._COUNTFINIE.Text = Trans(126)
		self._COUNTFINIE.UseVisualStyleBackColor = True
		self._COUNTFINIE.CheckState = if_else(COUNTFINIE, CheckState.Checked, CheckState.Unchecked)
		#
		# TITLEIT
		#
		self._TITLEIT.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._TITLEIT.Location = System.Drawing.Point(320, 172)
		self._TITLEIT.Name = "TITLEIT"
		self._TITLEIT.Size = System.Drawing.Size(180, 20)
		self._TITLEIT.TabIndex = 24
		self._TITLEIT.Text = Trans(127)
		self._TITLEIT.UseVisualStyleBackColor = True
		self._TITLEIT.CheckState = if_else(TITLEIT, CheckState.Checked, CheckState.Unchecked)
		#
		# FORMATARTICLES
		#
		self._FORMATARTICLES.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._FORMATARTICLES.Location = System.Drawing.Point(320, 194)
		self._FORMATARTICLES.Name = "FORMATARTICLES"
		self._FORMATARTICLES.Size = System.Drawing.Size(180, 20)
		self._FORMATARTICLES.TabIndex = 25
		self._FORMATARTICLES.Text = Trans(144)
		self._FORMATARTICLES.UseVisualStyleBackColor = True
		self._FORMATARTICLES.CheckState = if_else(FORMATARTICLES, CheckState.Checked, CheckState.Unchecked)
		#
		# PopUpEditionForm
		#
		self._PopUpEditionForm.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._PopUpEditionForm.Location = System.Drawing.Point(320, 216)
		self._PopUpEditionForm.Name = "PopUpEditionForm"
		self._PopUpEditionForm.Size = System.Drawing.Size(180, 20)
		self._PopUpEditionForm.TabIndex = 25
		self._PopUpEditionForm.Text = Trans(147)
		self._PopUpEditionForm.UseVisualStyleBackColor = True
		self._PopUpEditionForm.CheckState = if_else(PopUpEditionForm, CheckState.Unchecked, CheckState.Checked)
		#
		# Stop at error scraping
		#
		self._CBStop.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._CBStop.Location = System.Drawing.Point(320, 238)
		self._CBStop.Name = "CBStop"
		self._CBStop.Size = System.Drawing.Size(180, 20)
		self._CBStop.TabIndex = 26
		self._CBStop.Text = Trans(141)
		self._CBStop.UseVisualStyleBackColor = True
		self._CBStop.ThreeState = True
		if CBStop == True:
			self._CBStop.CheckState = CheckState.Checked
		elif  CBStop == False:
			self._CBStop.CheckState = CheckState.Unchecked
		elif CBStop == "2":
			self._CBStop.CheckState = CheckState.Indeterminate
		#
		# TIMEOUT Label4
		#
		self._label4.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._label4.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
		self._label4.Location = System.Drawing.Point(320, 280)
		self._label4.Name = "label4"
		self._label4.Size = System.Drawing.Size(160, 23)
		self._label4.TabIndex = 99
		self._label4.Text = Trans(128)
		#
		# TIMEOUT
		#
		self._TIMEOUT.Location = System.Drawing.Point(435, 280)
		self._TIMEOUT.Name = "TIMEOUT"
		self._TIMEOUT.Size = System.Drawing.Size(50, 21)
		self._TIMEOUT.TabIndex = 27
		self._TIMEOUT.TextAlign = HorizontalAlignment.Center
		self._TIMEOUT.MaxLength = 4
		self._TIMEOUT.Text = TIMEOUT
		#
		# TIMEOUTS Label6
		#
		self._label6.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._label6.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
		self._label6.Location = System.Drawing.Point(8, 236)
		self._label6.Name = "label6"
		self._label6.Size = System.Drawing.Size(160, 23)
		self._label6.TabIndex = 99
		self._label6.Text = Trans(129)
		#
		# TIMEOUTS
		#
		self._TIMEOUTS.Location = System.Drawing.Point(180, 232)
		self._TIMEOUTS.Name = "TIMEOUTS"
		self._TIMEOUTS.Size = System.Drawing.Size(50, 21)
		self._TIMEOUTS.TabIndex = 28
		self._TIMEOUTS.TextAlign = HorizontalAlignment.Center
		self._TIMEOUTS.MaxLength = 3
		self._TIMEOUTS.Text = TIMEOUTS
		#
		# DBGONOFF
		#
		self._DBGONOFF.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._DBGONOFF.Location = System.Drawing.Point(8, 80)
		self._DBGONOFF.Name = "DBGONOFF"
		self._DBGONOFF.Size = System.Drawing.Size(200, 25)
		self._DBGONOFF.TabIndex = 3
		self._DBGONOFF.Text = Trans(68)
		self._DBGONOFF.UseVisualStyleBackColor = True
		self._DBGONOFF.CheckState = if_else(DBGONOFF, CheckState.Checked, CheckState.Unchecked)
		#
		# SHOWDBGLOG
		#
		self._SHOWDBGLOG.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._SHOWDBGLOG.Location = System.Drawing.Point(8, 40)
		self._SHOWDBGLOG.Name = "SHOWDBGLOG"
		self._SHOWDBGLOG.Size = System.Drawing.Size(300, 25)
		self._SHOWDBGLOG.TabIndex = 2
		self._SHOWDBGLOG.Text = Trans(67)
		self._SHOWDBGLOG.UseVisualStyleBackColor = True
		self._SHOWDBGLOG.CheckState = if_else(SHOWDBGLOG, CheckState.Checked, CheckState.Unchecked)
		#
		# SHOWRENLOG
		#
		self._SHOWRENLOG.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._SHOWRENLOG.Location = System.Drawing.Point(8, 0)
		self._SHOWRENLOG.Name = "SHOWRENLOG"
		self._SHOWRENLOG.Size = System.Drawing.Size(300, 25)
		self._SHOWRENLOG.TabIndex = 1
		self._SHOWRENLOG.Text = Trans(66)
		self._SHOWRENLOG.UseVisualStyleBackColor = True
		self._SHOWRENLOG.CheckState = if_else(SHOWRENLOG, CheckState.Checked, CheckState.Unchecked)
		#
		# radioENG
		#
		self._radioENG.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._radioENG.Location = System.Drawing.Point(8, 200)
		self._radioENG.Name = "radioENG"
		self._radioENG.Size = System.Drawing.Size(104, 24)
		self._radioENG.TabIndex = 6
		self._radioENG.Text = "English"
		self._radioENG.UseVisualStyleBackColor = True
		#
		# radioFRE
		#
		self._radioFRE.Checked = True
		self._radioFRE.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
		self._radioFRE.Location = System.Drawing.Point(160, 200)
		self._radioFRE.Name = "radioFRE"
		self._radioFRE.Size = System.Drawing.Size(104, 24)
		self._radioFRE.TabIndex = 7
		self._radioFRE.TabStop = True
		self._radioFRE.Text = "Français"
		self._radioFRE.UseVisualStyleBackColor = True
		if LANGENFR == "FR":
			self._radioFRE.Checked = True
			self._radioENG.Checked = False
		else:
			self._radioENG.Checked = True
			self._radioFRE.Checked = False
		#
		# PB1
		#
		pImage = (__file__[:-len('BedethequeScraper2.py')] + "BD2.png")
		self._PB1.Image = System.Drawing.Bitmap(pImage)
		self._PB1.Location = System.Drawing.Point(420, 4)
		self._PB1.Name = "PB1"
		self._PB1.Size = System.Drawing.Size(72, 64)
		self._PB1.TabIndex = 35
		self._PB1.TabStop = False
		#
		# ConfigForm
		#
		self.ClientSize = System.Drawing.Size(512, 412)
		self.Controls.Add(self._TabData)

		self._TabData.ResumeLayout(False)
		self._tabPage1.ResumeLayout(False)
		self._tabPage1.PerformLayout()
		self._tabPage2.ResumeLayout(False)
		self._tabPage2.PerformLayout()
		self.AcceptButton = self._OKButton
		self.CancelButton = self._CancelButton
		self.KeyPreview = True
		self.ResumeLayout(False)


	def button_Click(self, sender, e):

		global SHOWRENLOG, SHOWDBGLOG, DBGONOFF, DBGLOGMAX, RENLOGMAX, LANGENFR, aWord
		global TBTags, CBCover, CBStatus, CBGenre, CBNotes, CBWeb, CBCount, CBSynopsys,	CBImprint, CBLetterer, CBPrinted, CBRating, CBISBN, CBDefault, CBRescrape, CBStop, PopUpEditionForm
		global	CBLanguage,	CBEditor, CBFormat,	CBColorist,	CBPenciller, CBWriter, CBTitle, CBSeries, ARTICLES, SUBPATT, COUNTOF, CBCouverture, COUNTFINIE, TITLEIT, TIMEOUT, TIMEOUTS, TIMEPOPUP, FORMATARTICLES, PadNumber

		if sender.Name.CompareTo(self._OKButton.Name) == 0:
			SHOWRENLOG = if_else(self._SHOWRENLOG.CheckState == CheckState.Checked, True, False)
			SHOWDBGLOG = if_else(self._SHOWDBGLOG.CheckState == CheckState.Checked, True, False)
			DBGONOFF = if_else(self._DBGONOFF.CheckState == CheckState.Checked, True, False)
			DBGLOGMAX = int(self._DBGLOGMAX.Text)
			RENLOGMAX = int(self._RENLOGMAX.Text)
			LANGENFR = if_else(self._radioENG.Checked,"EN", "FR")
			TBTags = self._TBTags.Text
			CBCover = if_else(self._CBCover.CheckState == CheckState.Checked, True, False)
			CBStatus = if_else(self._CBStatus.CheckState == CheckState.Checked, True, False)
			CBGenre = if_else(self._CBGenre.CheckState == CheckState.Checked, True, False)
			CBNotes = if_else(self._CBNotes.CheckState == CheckState.Checked, True, False)			
			if self._CBWeb.CheckState == CheckState.Checked:
				CBWeb = True
			elif self._CBWeb.CheckState == CheckState.Unchecked:
				CBWeb = False
			elif self._CBWeb.CheckState == CheckState.Indeterminate:
				CBWeb = "2"

			CBCount = if_else(self._CBCount.CheckState == CheckState.Checked, True, False)
			CBSynopsys = if_else(self._CBSynopsys.CheckState == CheckState.Checked, True, False)
			CBImprint = if_else(self._CBImprint.CheckState == CheckState.Checked, True, False)
			CBLetterer = if_else(self._CBLetterer.CheckState == CheckState.Checked, True, False)
			CBPrinted = if_else(self._CBPrinted.CheckState == CheckState.Checked, True, False)
			CBRating = if_else(self._CBRating.CheckState == CheckState.Checked, True, False)
			CBISBN = if_else(self._CBISBN.CheckState == CheckState.Checked, True, False)
			CBLanguage = if_else(self._CBLanguage.CheckState == CheckState.Checked, True, False)
			CBEditor = if_else(self._CBEditor.CheckState == CheckState.Checked, True, False)
			CBFormat = if_else(self._CBFormat.CheckState == CheckState.Checked, True, False)
			CBColorist = if_else(self._CBColorist.CheckState == CheckState.Checked, True, False)
			CBPenciller = if_else(self._CBPenciller.CheckState == CheckState.Checked, True, False)
			CBWriter = if_else(self._CBWriter.CheckState == CheckState.Checked, True, False)
			CBTitle = if_else(self._CBTitle.CheckState == CheckState.Checked, True, False)
			CBSeries = if_else(self._CBSeries.CheckState == CheckState.Checked, True, False)
			CBDefault = if_else(self._CBDefault.CheckState == CheckState.Checked, True, False)
			CBRescrape = if_else(self._CBRescrape.CheckState == CheckState.Checked, True, False)
			if self._CBStop.CheckState == CheckState.Checked:
				CBStop = True
			elif self._CBStop.CheckState == CheckState.Unchecked:
				CBStop = False
			elif self._CBStop.CheckState == CheckState.Indeterminate:
				CBStop = "2"
			
			ARTICLES = self._ARTICLES.Text
			SUBPATT = self._SUBPATT.Text
			COUNTOF = if_else(self._COUNTOF.CheckState == CheckState.Checked, True, False)
			COUNTFINIE = if_else(self._COUNTFINIE.CheckState == CheckState.Checked, True, False)
			TITLEIT = if_else(self._TITLEIT.CheckState == CheckState.Checked, True, False)
			FORMATARTICLES = if_else(self._FORMATARTICLES.CheckState == CheckState.Checked, True, False)
			PopUpEditionForm = if_else(self._PopUpEditionForm.CheckState == CheckState.Checked, False, True)
#modif kiwi
			try:
				if int(self._TIMEOUT.Text) > 0:
					TIMEOUT = self._TIMEOUT.Text
				else:
					TIMEOUT = "1000"
			except:
				TIMEOUT = "1000"

			try:
				if int(self._TIMEOUTS.Text) > 0:
					TIMEOUTS = self._TIMEOUTS.Text
				else:
					TIMEOUTS = "7"
			except:
				TIMEOUTS = "7"

			try:
				if int(self._TIMEPOPUP.Text) > 0:
					TIMEPOPUP = self._TIMEPOPUP.Text
				else:
					TIMEPOPUP = "30"
			except:
				TIMEPOPUP = "30"

			try:
				if int(self._PadNumber.Text) >= 0:
					PadNumber = self._PadNumber.Text
				else:
					PadNumber = "0"
			except:
				PadNumber = "0"

			aWord = Translate()
			log_BD(TIMEOUTS,"",1)

		if sender.Name.CompareTo(self._ButtonReset.Name) == 0:
			for CBControl in self._tabPage2.Controls:
				try:
					if CBControl.CheckState == CheckState.Checked:
						CBControl.CheckState = CheckState.Unchecked
					else:
						CBControl.CheckState = CheckState.Checked
				except:
					pass
			self._TBTags.Text = ""

def Translate():

	global aWord, LANGENFR

	path = (__file__[:-len('BedethequeScraper2.py')])
	
	if not File.Exists(path + "\BDTranslations.Config"):				
		log_BD("File BDTranslations.Config missing !", "Error!", 1)
		sys.exit(0)

	try:	
		TransSettings = AppSettings()
		TransSettings.Load(path + "\BDTranslations.Config")
	except Exception as e:
		log_BD("Error loading file BDTranslations.Config !", e.message, 1)
		sys.exit(0)

	aWord = list()
	
	for i in range (1, 200):
		try:
			aWord.append(TransSettings.Get('T' + '%04d' % i + '/' + LANGENFR))
		except:
			exit	
	
	return aWord

def Trans(nWord):

	global aWord

	tText = aWord[nWord-1]

	return tText

def cleanARTICLES(s):

	global ARTICLES
	Regex = re.compile(r"^(" + ARTICLES.replace(',','|') + ")\s*(?<=['\s])([^\/\r\n\-\–\(]*).*", re.IGNORECASE)
	ns = Regex.sub(r"\2", s)
	if ns:
		s = ns.strip()
	ns2 = re.sub(r"^([^\/\r\n\-\–\(\:]*).*", r"\1", s, re.IGNORECASE)
	if ns2:
		s = ns2.strip()

	return s

def formatARTICLES(s):

	global ARTICLES
	#Regex = re.compile(r"^(" + ARTICLES.replace(',','|') + ")\s*(?<=['\s])([^\(\/\r\n]*)(?!\(|\/)\s*([^\r\n]*)", re.IGNORECASE)
	Regex = re.compile(r"^(" + ARTICLES.replace(',','|') + ")\s*(?<=['\s])((?=.*(?:\s-\s))[^\-\r\n]*|[^\(\/\r\n]*)(?!\(|\/|\-)\s*([^\r\n]*)", re.IGNORECASE) #Mettre l'Articles avant le " - "
	ns = Regex.sub(r"\2 (\1) \3", s)
	if ns:
		s = ns.strip()

	return s

def titlize(s, formatArticles = False):
	
	global TITLEIT, FORMATARTICLES, ARTICLES
	
	if formatArticles and FORMATARTICLES:
		s = formatARTICLES(s)
	
	if TITLEIT:
		#CharList = '[\.\?\!\(\[]\s\"\'\[\]'		
		NewString = ""
		Ucase = False
		for i in range(len(s.strip())):
			if Ucase or i == 0:
				NewString += s[i:i + 1].upper()
			else:
				NewString += s[i:i + 1]
				
			if not (s[i:i + 1]).isalnum(): # in CharList:
				Ucase = True
			else:				
				Ucase = False
		test = s.title()
		return NewString		
	else:
		return s

class FormType():
	SERIE = 1
	ALBUM = 2
	EDITION = 3	

class SeriesForm(Form):
	
	global aWord, NewLink, NewSeries	
	
	def __init__(self, serie, listItems, formType = FormType.SERIE):
		
		global aWord, NewLink, NewSeries
		
		self.List = listItems
		self.formType = formType
		self.InitializeComponent(serie)
	
	def InitializeComponent(self, serie):

		global SeriesSearch, NewLink, NewSeries, TIMEPOPUP, CBStop
		
		self._ListSeries = System.Windows.Forms.ListBox()
		self._CancelButton = System.Windows.Forms.Button()
		self._OKButton = System.Windows.Forms.Button()
		#self._SearchSeries = System.Windows.Forms.TextBox()
		#self._labelSearch = System.Windows.Forms.Label()
		if CBStop == "2":
			self._timer1 = System.Windows.Forms.Timer()
#modif kiwi
			self._timer1.Interval = int(TIMEPOPUP) * 1000
			self._timer1.Enabled = True
			self._timer1.Tick += self.CloseForm
		
		#self.SuspendLayout()
		# 
		# ListSeries
		# 
		self._ListSeries.Font = System.Drawing.Font("Microsoft Sans Serif", 9, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
		self._ListSeries.FormattingEnabled = True
		self._ListSeries.ItemHeight = 15
		self._ListSeries.Location = System.Drawing.Point(8, 8)
		self._ListSeries.Name = "ListSeries"
		self._ListSeries.Size = System.Drawing.Size(450, 229)
		self._ListSeries.Sorted = True
		self._ListSeries.TabIndex = 1
		self._ListSeries.DoubleClick += self.DoubleClick		
		# 
		# CancelButton
		# 
		self._CancelButton.BackColor = System.Drawing.Color.Red
		self._CancelButton.DialogResult = System.Windows.Forms.DialogResult.Cancel
		self._CancelButton.Font = System.Drawing.Font("Microsoft Sans Serif", 9, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, 0)
		self._CancelButton.Location = System.Drawing.Point(301, 290)
		self._CancelButton.Name = "CancelButton"
		self._CancelButton.Size = System.Drawing.Size(75, 30)
		self._CancelButton.TabIndex = 2
		self._CancelButton.Text = Trans(93)
		self._CancelButton.UseVisualStyleBackColor = False
		self._CancelButton.DialogResult = DialogResult.Cancel
		# 
		# OKButton
		# 
		self._OKButton.BackColor = System.Drawing.Color.FromArgb(128, 255, 128)
		self._OKButton.DialogResult = System.Windows.Forms.DialogResult.OK
		self._OKButton.Font = System.Drawing.Font("Microsoft Sans Serif", 9, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, 0)
		self._OKButton.ForeColor = System.Drawing.Color.Black
		self._OKButton.Location = System.Drawing.Point(8, 290)
		self._OKButton.Name = "OKButton"
		self._OKButton.Size = System.Drawing.Size(75, 30)
		self._OKButton.TabIndex = 3
		self._OKButton.Text = Trans(92)
		self._OKButton.UseVisualStyleBackColor = False
		self._OKButton.Click += self.button_Click
		self._OKButton.DialogResult = DialogResult.OK
		
			
		self.ClientSize = System.Drawing.Size(390, 325)		
		self.Controls.Add(self._ListSeries)
		self.Controls.Add(self._OKButton)
		self.Controls.Add(self._CancelButton)
		#self.Controls.Add(self._timer1)
		self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
		self.MaximizeBox = False
		self.MinimizeBox = False
		self.Name = "SeriesForm"
		self.SizeGripStyle = System.Windows.Forms.SizeGripStyle.Hide
		self.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen
		
		frmTitle = ""
		if self.formType == FormType.SERIE: 
			frmTitle = Trans(132) + serie
		elif self.formType == FormType.EDITION: 
			frmTitle = Trans(145) + serie
		elif self.formType == FormType.ALBUM: 
			frmTitle = Trans(146) + serie
		self.Text = frmTitle
			
		self.AcceptButton = self._OKButton
		self.CancelButton = self._CancelButton
		self.KeyPreview = True

		for x in range(len(self.List)):			
			if self.List[x]:
				title = ""		
				if self.formType == FormType.EDITION: 
					title = self.List[x][1].Title
				else: 
					title = self.List[x][1]
			
				self._ListSeries.Items.Add("(" + self.List[x][2] + ") - " + title + if_else(self.List[x][0], "   (", "") + self.List[x][0] + if_else(self.List[x][0], ")", ""))
				# self._ListSeries.Items.Add("(" + self.List[x][2] + ")- " + self.List[x][1] + if_else(self.List[x][0], "   (", "") + self.List[x][0] + if_else(self.List[x][0], ")", ""))
				#self._ListSeries.Items.Add("(" + ListSeries[x][2] + ")- " + ListSeries[x][1].decode('utf-8') + if_else(ListSeries[x][0], "   (", "") + ListSeries[x][0] + if_else(ListSeries[x][0], ")", ""))
			#self._ListSeries.Items.soSort()

		#self.ResumeLayout(False)		
		#self.PerformLayout()
		if CBStop == "2":
			self._timer1.Start()

	def button_Click(self, sender, e):
	
		global NewLink, NewSeries
				
		if sender.Name.CompareTo(self._OKButton.Name) == 0 and self.List[self._ListSeries.SelectedIndex][1]: 			
			NewLink = self.List[self._ListSeries.SelectedIndex][0]
			NewSeries = self.List[self._ListSeries.SelectedIndex][1]			
			self.Hide()

	def CloseForm(self, sender, e):
	
			self.Hide()
	
	def DoubleClick(self, sender, e):
				
		global NewLink, NewSeries
		
		title = ""
		link = ""
		if self.formType == FormType.SERIE: 
			title = self.List[self._ListSeries.SelectedIndex][1]
			link = "https://www.bedetheque.com/" + self.List[self._ListSeries.SelectedIndex][0]
		elif self.formType == FormType.EDITION: 
			title = self.List[self._ListSeries.SelectedIndex][1].Title + " (" + self.List[self._ListSeries.SelectedIndex][1].A + ")"
			link = self.List[self._ListSeries.SelectedIndex][1].URL# or self.List[self._ListSeries.SelectedIndex][1].Couv
		elif self.formType == FormType.ALBUM: 
			title = self.List[self._ListSeries.SelectedIndex][1]
			link = self.List[self._ListSeries.SelectedIndex][0]
					
		if title:
			print title, self._ListSeries.SelectedIndex
			NewLink = link
			NewSeries = self.List[self._ListSeries.SelectedIndex][1]
			Start(NewLink)			
			#NewSeries = ListSeries[self._ListSeries.SelectedIndex][1]			
			#self.Hide()
			#self.DialogResult = DialogResult.OK
			#return

			
#@Key Bedetheque2
#@Hook ConfigScript
#@Name Configurer BD2
def ConfigureBD2Quick():
	global SHOWRENLOG, SHOWDBGLOG, DBGONOFF, DBGLOGMAX, RENLOGMAX, LANGENFR, aWord
	global TBTags, CBCover, CBStatus, CBGenre, CBNotes, CBWeb, CBCount, CBSynopsys,	CBImprint, CBLetterer, CBPrinted, CBRating, CBISBN, CBDefault, CBRescrape, CBStop
	global	CBLanguage,	CBEditor, CBFormat,	CBColorist,	CBPenciller, CBWriter, CBTitle, CBSeries, ARTICLES, SUBPATT, COUNTOF, CBCouverture, COUNTFINIE, TITLEIT, TIMEOUT, TIMEOUTS, TIMEPOPUP, PadNumber
	
	if not LoadSetting():
		return
	
	config = BDConfigForm()
	result = config.ShowDialog()

	if result == DialogResult.Cancel:
		return
	else:
		SaveSetting()

#@Name Configurer BD2
#@Image BD2.png
#@Hook Library
#@Key ConfigureBD2
def ConfigureBD2(self):

	global SHOWRENLOG, SHOWDBGLOG, DBGONOFF, DBGLOGMAX, RENLOGMAX, LANGENFR, aWord
	global TBTags, CBCover, CBStatus, CBGenre, CBNotes, CBWeb, CBCount, CBSynopsys,	CBImprint, CBLetterer, CBPrinted, CBRating, CBISBN, CBDefault, CBRescrape, CBStop
	global	CBLanguage,	CBEditor, CBFormat,	CBColorist,	CBPenciller, CBWriter, CBTitle, CBSeries, ARTICLES, COUNTOF, CBCouverture, COUNTFINIE, TITLEIT, TIMEOUT, TIMEOUTS, TIMEPOPUP, PadNumber
	
	if not LoadSetting():
		return

	config = BDConfigForm()
	result = config.ShowDialog()

	if result == DialogResult.Cancel:
		return
	else:
		SaveSetting()

#@Name QuickScrape BD2
#@Image BD2Q.png
#@Hook Books
#@Key QuickScrapeBD2
def QuickScrapeBD2(books, book = "", cLink = False):

	global SHOWRENLOG, SHOWDBGLOG, DBGONOFF, DBGLOGMAX, RENLOGMAX, LANGENFR, aWord, dlgName, dlgNumber
	global TBTags, CBCover, CBStatus, CBGenre, CBNotes, CBWeb, CBCount, CBSynopsys,	CBImprint, CBLetterer, CBPrinted, CBRating, CBISBN, CBDefault, CBRescrape, CBStop
	global CBLanguage,	CBEditor, CBFormat,	CBColorist,	CBPenciller, CBWriter, CBTitle, CBSeries, LinkBD2, Numero
	global AlbumNumNum, dlgNumber, dlgName, nRenamed, nIgnored, dlgAltNumber, ARTICLES, SUBPATT, COUNTOF, Shadow1, Shadow2, RenameSeries, CBCouverture, COUNTFINIE, TITLEIT, TIMEOUT, TIMEOUTS, TIMEPOPUP, PadNumber

	RetAlb = False

	if not cLink:
		if not LoadSetting():
			return False
	
	RenameSeries = False
	
	#FICHE_SERIE_PATTERN = r'<a\sclass=\"back\"\shref=\"(.*?)\">'
	# FICHE_SERIE_PATTERN = r'>album</a>.*?href=\"(.*)\">s.rie\s?:'
	# FICHE_SERIE = re.compile(FICHE_SERIE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

	if not books:
		Result = MessageBox.Show(ComicRack.MainWindow, Trans(1),Trans(2), MessageBoxButtons.OK, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button1)
		return False

	LinkBD2 = ""

	if not cLink:
		nRenamed = 0
		nIgnored = 0	
	cError = False
	MyBooks = ComicBook()
	
	try:	
		f = ProgressBarDialog(books.Count)
		if books.Count > 1:
			f.Show(ComicRack.MainWindow)
		
		if books:
			if cLink:
				MyBooks = book
			else:
				MyBooks = books
				
			# if MyBooks.Count <> 1:
				# return False
				
			log_BD(Trans(7) + str(MyBooks.Count) +  Trans(8), "\n============ " + str(datetime.now().strftime("%A %d %B %Y %H:%M:%S")) + " ===========", 0)
					
			for MyBook in MyBooks:
						
				if cLink:					
					Numero = ""			
					serieUrl = re.sub('https://www.bedetheque.com/', '', cLink)
					if re.search(r'album', serieUrl):
						LinkBD2 = serieUrl
					
				else:
					
					if MyBook.Number:
						dlgNumber = MyBook.Number
						Shadow2 = False
					else:
						dlgNumber = MyBook.ShadowNumber
						Shadow2 = True

					if MyBook.Series:
						dlgName = titlize(MyBook.Series)
						Shadow1 = False
					else:
						dlgName = MyBook.ShadowSeries
						Shadow1 = True

					dlgAltNumber = ""
					if MyBook.AlternateNumber:
						dlgAltNumber = MyBook.AlternateNumber

					albumNum = dlgNumber
					mPos = re.search(r'([.|,|\\|\/|-])', dlgNumber)

					if not isnumeric(dlgNumber):
						albumNum = dlgNumber
						AlbumNumNum = False
					elif isnumeric(dlgNumber) and not re.search(r'[.|,|\\|\/|-]', dlgNumber):
						dlgNumber = str(int(dlgNumber))
						albumNum = str(int(dlgNumber))
						AlbumNumNum = True
					elif mPos:
						nPos = mPos.start(1)
						albumNum = dlgNumber[:nPos]
						dlgAltNumber = dlgNumber[nPos:]
						dlgNumber = albumNum
						AlbumNumNum = True
					
					if not cLink:
						f.Update(dlgName + if_else(dlgNumber != "", " - " + dlgNumber, " ") + if_else(dlgAltNumber == '', '', ' AltNo.[' + dlgAltNumber + ']') + " - " + titlize(MyBook.Title), 1, MyBook)
						f.Refresh()	
					
					scrape = DirectScrape()
					result = scrape.ShowDialog()
				
					if result == DialogResult.Cancel or (LinkBD2 == ""):
						return False
				
					if LinkBD2:						
						serieUrl = LinkBD2
						
				# try:
					# ficheUrl = _read_url(serieUrl, False)
				# except:
					# return False

				# fiche = FICHE_SERIE.search(ficheUrl)

				if LinkBD2:
					if DBGONOFF:print Trans(104), LinkBD2

				# if fiche:	
					# RetVal = parseSerieInfo(MyBook, fiche.group(1), True)
				RetVal = serieUrl
				if "serie-" in serieUrl:	
					serieUrl = serieUrl.lower().replace(".html", u'__10000.html') if "__10000.html" in serieUrl else serieUrl
					RetVal = parseSerieInfo(MyBook, serieUrl, True)
																		
				if RetVal:
					if LinkBD2:					
						RetVal = parseAlbumInfo(MyBook, RetVal, dlgNumber, True)															

				if RetVal:
					if not cLink:
						nRenamed += 1
					log_BD("[" + serieUrl + "]", Trans(13), 1)
				else:
					if not cLink:
						nIgnored += 1
					log_BD("[" + serieUrl + "]", Trans(14) + "\n", 1)

		else:
			if DBGONOFF:print Trans(15) +"\n"
			log_BD(Trans(15), "", 1)
			return False

	except:		
		cError = debuglog()
		try:
			log_BD("   [" + serieUrl + "]", cError, 1)		
		except:
			log_BD("   [error]", cError, 1)		
		if not cLink:
			f.Close()
		return False

	finally:
		if not cLink:
			f.Update(Trans(16), 1, book)
			f.Refresh()		
			f.Close()
			#rdlg = MessageBox.Show(ComicRack.MainWindow, Trans(2),Trans(2), MessageBoxButtons.OK, MessageBoxIcon.Error, MessageBoxDefaultButton.Button1)

			return False

		log_BD("\n" + Trans(17) + str(nRenamed) , "", 0)
		log_BD(Trans(18) + str(nIgnored), "", 0)
		log_BD("============= " + str(datetime.now().strftime("%A %d %B %Y %H:%M:%S")) + " =============", "\n\n", 0)
		if not cLink and cError and SHOWDBGLOG:
			rdlg = MessageBox.Show(ComicRack.MainWindow, Trans(17) + str(nRenamed) + "," + Trans(18) + str(nIgnored) + "\n\n" + Trans(19), Trans(20), MessageBoxButtons.YesNo, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button1)
			if rdlg == DialogResult.Yes:
				# open debug log automatically
				if FileInfo(__file__[:-len('BedethequeScraper2.py')] + "BD2_Debug_Log.txt"):
					Start(__file__[:-len('BedethequeScraper2.py')] + "BD2_Debug_Log.txt")
		elif SHOWRENLOG:
			if not cLink:
				rdlg = MessageBox.Show(ComicRack.MainWindow, Trans(17) + str(nRenamed) + "," + Trans(18) + str(nIgnored) + "\n\n" + Trans(21), Trans(22), MessageBoxButtons.YesNo, MessageBoxIcon.Question, MessageBoxDefaultButton.Button1)
				if rdlg == DialogResult.Yes:
					# open rename log automatically
					if FileInfo(__file__[:-len('BedethequeScraper2.py')] + "BD2_Rename_Log.txt"):
						Start(__file__[:-len('BedethequeScraper2.py')] + "BD2_Rename_Log.txt")
		elif not cLink:
			rdlg = MessageBox.Show(ComicRack.MainWindow, Trans(17) + str(nRenamed) + "," + Trans(18) + str(nIgnored) , Trans(22), MessageBoxButtons.OK, MessageBoxIcon.Exclamation, MessageBoxDefaultButton.Button1)

	return True

class DirectScrape(Form):

	global aWord

	def __init__(self):

		global aWord

		self.InitializeComponent()

	def InitializeComponent(self):

		global aWord, LinkBD2, Numero

		try:
			# BD
			self._LinkBD2 = System.Windows.Forms.TextBox()
			self._label1 = System.Windows.Forms.Label()						
			self._OKScrape = System.Windows.Forms.Button()
			self._CancScrape = System.Windows.Forms.Button()
			#
			# LinkBD2
			#
			self._LinkBD2.Location = System.Drawing.Point(8, 40)
			self._LinkBD2.Name = "LinkBD2"
			self._LinkBD2.Size = System.Drawing.Size(646, 20)
			self._LinkBD2.TabIndex = 1
			self._LinkBD2.Text = ""
			self._LinkBD2.WordWrap = False
			#
			# label1
			#
			self._label1.Font = System.Drawing.Font("Microsoft Sans Serif", 11.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
			self._label1.Location = System.Drawing.Point(104, 8)
			self._label1.Name = "label1"
			self._label1.Size = System.Drawing.Size(450, 20)
			self._label1.TabIndex = 99
			self._label1.Text = Trans(102)
			self._label1.TextAlign = System.Drawing.ContentAlignment.MiddleCenter
			#
			# OKScrape
			#
			self._OKScrape.BackColor = System.Drawing.Color.FromArgb(128, 255, 128)
			self._OKScrape.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, 0)
			self._OKScrape.Location = System.Drawing.Point(48, 72)
			self._OKScrape.Name = "OKScrape"
			self._OKScrape.Size = System.Drawing.Size(104, 30)
			self._OKScrape.TabIndex = 3
			self._OKScrape.Text =  Trans(92)
			self._OKScrape.UseVisualStyleBackColor = False
			self._OKScrape.Click += self.button_Click
			self._OKScrape.DialogResult = System.Windows.Forms.DialogResult.OK
			#
			# CancScrape
			#
			self._CancScrape.BackColor = System.Drawing.Color.FromArgb(255, 128, 128)
			self._CancScrape.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, 0)
			self._CancScrape.Location = System.Drawing.Point(550, 72)
			self._CancScrape.DialogResult = System.Windows.Forms.DialogResult.Cancel
			self._CancScrape.Name = "CancScrape"
			self._CancScrape.Size = System.Drawing.Size(104, 30)
			self._CancScrape.TabIndex = 4
			self._CancScrape.Text =  Trans(93)
			self._CancScrape.UseVisualStyleBackColor = False
			self._CancScrape.Click += self.button_Click
			#
			# ScrapeLink
			#
			# BD
			self.ClientSize = System.Drawing.Size(710, 108)
			self.ControlBox = False
			self.Controls.Add(self._CancScrape)
			self.Controls.Add(self._OKScrape)
			self.Controls.Add(self._label1)
			self.Controls.Add(self._LinkBD2)			
			#
			self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
			self.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen
			self.Name = "ScrapeLink"
			self.Text = Trans(103)
			pIcon = (__file__[:-len('BedethequeScraper2.py')] + "BD2.ico")
			self.Icon = System.Drawing.Icon(pIcon)
			self.KeyPreview = True
			self.ResumeLayout(False)
			self.PerformLayout()

		except:
			cError = debuglog()

	def button_Click(self, sender, e):

		if sender.Name.CompareTo(self._OKScrape.Name) == 0:

			global LinkBD2

			if not self._LinkBD2.Text:
				self.Hide()				
				LinkBD2 = ""
			#elif not re.search ('www.bedetheque.*?album', self._LinkBD2.Text):
			#	self.Hide()
			#	Result = MessageBox.Show(ComicRack.MainWindow, Trans(106), Trans(2), MessageBoxButtons.OK, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button1)
			#	LinkBD2 = ""
			
			else:
				LinkBD2 = self._LinkBD2.Text
