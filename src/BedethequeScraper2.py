# -*- coding: utf-8 -*-
#@Name Bedetheque Scraper 2
#@Key Bedetheque2
#@Hook    Books, Editor
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
import operator, collections
from datetime import datetime, timedelta
from time import strftime, clock

from urllib import *
from urllib2 import *
from HTMLParser import HTMLParser

clr.AddReference('System')
clr.AddReference('System.Windows.Forms')
from System.Windows.Forms import * 

try:
    clr.AddReference('cYo.Common.Windows')
    from cYo.Common.Windows.Forms import FormEx, UserControlEx
    BaseForm = FormEx
    BaseUserControl = UserControlEx
except (ImportError, AttributeError):
    # Fallback for older program versions
    BaseForm = Form
    BaseUserControl = UserControl

from System.IO import FileInfo, File
from System.Diagnostics.Process import Start
from System.Net import HttpWebRequest, Cookie, DecompressionMethods
from System.Threading import Thread, ThreadStart
from System import Math

clr.AddReference('System.Drawing')
from System.Drawing import *

from System.Text import StringBuilder

from cYo.Projects.ComicRack.Engine import *

clr.AddReference('System.Xml')
from System.Xml import *
BasicXml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><configuration></configuration>"

CookieContainer = System.Net.CookieContainer()

VERSION = "6.01"

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
ShortWebLink = False
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
CBInker = True
CBWriter = True
CBTitle = True
CBSeries = True
CBDefault = False
CBRescrape = False
AllowUserChoice = "2"
PopUpEditionForm = False
ARTICLES = "Le,La,Les,L',The"
FORMATARTICLES = True
SUBPATT = " - - "
COUNTOF = True
COUNTFINIE = True
TITLEIT = True
CBCouverture = True
SerieResumeEverywhere = True
AcceptGenericArtists = True
TIMEOUT = "1000"
TIMEOUTS = "7"
TIMEPOPUP = "30"
PadNumber = "0"
Serie_Resume = ""
ONESHOTFORMAT = False
bStopit = False
AlwaysChooseSerie = False
TimerExpired = False
SkipAlbum = False
log_messages = []

########################################
# Nombres auteurs
LAST_FIRST_NAMES_PATTERN = r'(?P<name>[^,]*?), (?P<firstname>[^,]*?)$'
LAST_FIRST_NAMES = re.compile(LAST_FIRST_NAMES_PATTERN)

########################################
# Info Serie
SERIE_LIST_PATTERN = r'<a\shref="https://www.bedetheque.com/serie-(.*?)">.*?libelle">(.*?)\r'

SERIE_LIST_CHECK_PATTERN = r's.ries\strouv.{20,60}?La\srecherche.*?\srenvoie\splus\sde\s500\sdonn'
SERIE_LIST_CHECK = re.compile(SERIE_LIST_CHECK_PATTERN, re.IGNORECASE | re.DOTALL)

SERIE_URL_PATTERN = r'<a\shref="(.*?)">\r\n.{50,60}<span\sclass="libelle">%s\s*?</span>'

ALBUM_ID_PATTERN = r'id="%s".*?album-%s(.*?)\.html'
ALBUM_INFO_PATTERN = r'<meta\sname="description"\scontent="(.*?)"'

SERIE_LANGUE_PATTERN = r'class="flag"/>(.*?)</span>'
SERIE_LANGUE = re.compile(SERIE_LANGUE_PATTERN, re.IGNORECASE)

SERIE_GENRE_PATTERN = r'<span\sclass="style">(.*?)<'
SERIE_GENRE = re.compile(SERIE_GENRE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_RESUME_PATTERN = r'<meta\sname="description"\scontent="(.*?)"\s/>'
SERIE_RESUME = re.compile(SERIE_RESUME_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_STATUS_PATTERN = r'<h3>.*?<span><i\sclass="icon-info-sign"></i>(.*?)</span>'
SERIE_STATUS = re.compile(SERIE_STATUS_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_NOTE_PATTERN = r'<p\sclass="static">Note:\s<strong>\s(?P<note>[^<]*?)</strong>'
SERIE_NOTE = re.compile(SERIE_NOTE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_COUNT_PATTERN = r'class="icon-book"></i>\s(\d+)'
SERIE_COUNT = re.compile(SERIE_COUNT_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_COUNT_REAL_PATTERN = r'liste-albums-side(.*?)WIDGET'
SERIE_COUNT_REAL = re.compile(SERIE_COUNT_REAL_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_COUNTOF_PATTERN = r'<label>(.*?)<span'
SERIE_COUNTOF = re.compile(SERIE_COUNTOF_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

SERIE_HEADER2_PATTERN = r'<h3(.+?)</p'
SERIE_HEADER2 = re.compile(SERIE_HEADER2_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

# Info Serie for Quickscrape

SERIE_QSERIE_PATTERN = r'<h1>\s*<a href="serie-[^\.]+\.html">([^"<>]+)</a>'

# Info Album from Album
INFO_SERIENAMENUMBER_ALBUM_PATTERN = r'<span\sclass="type">S.*?rie\s:\s</span>\s?(.*?)<.*?id="%s">.*?<div\sclass="titre">(?:(.*?)<.*?numa">(.*?)</span>\.?\s?)?(.*?)<'

ALBUM_BDTHEQUE_NOTNUM_PATTERN = r'tails">.*?<span\sclass="numa"></span>.*?<a name="(.*?)"'
ALBUM_BDTHEQUE_NOTNUM = re.compile(ALBUM_BDTHEQUE_NOTNUM_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_TITLE_PATTERN = r'itemprop="url"\shref="%s"\stitle="(.*?)">'

ALBUM_EVAL_PATTERN = r'ratingValue">(.*?)<'
ALBUM_EVAL = re.compile(ALBUM_EVAL_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_MULTI_AUTHOR_NAMES_PATTERN = r'">(.*?)</'
ALBUM_MULTI_AUTHOR_NAMES = re.compile(ALBUM_MULTI_AUTHOR_NAMES_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_SCENAR_MULTI_AUTHOR_PATTERN = r'<label>sc.*?nario\s:</label>(.*?)<label>[^&]'
ALBUM_SCENAR_MULTI_AUTHOR = re.compile(ALBUM_SCENAR_MULTI_AUTHOR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

# Storyboard artists (i.e https://www.bedetheque.com/BD-Aio-Zitelli-Tome-1-Recits-de-guerre-14-18-215576.html)
ALBUM_STORYBOARD_MULTI_AUTHOR_PATTERN = r'label>storyboard\s:</label>(.*?)<label>[^&]'
ALBUM_STORYBOARD_MULTI_AUTHOR = re.compile(ALBUM_STORYBOARD_MULTI_AUTHOR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_DESSIN_MULTI_AUTHOR_PATTERN = r'<label>dessin\s:</label>(.*?)<label>[^&]'
ALBUM_DESSIN_MULTI_AUTHOR = re.compile(ALBUM_DESSIN_MULTI_AUTHOR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_COLOR_MULTI_AUTHOR_PATTERN = r'<label>couleurs\s:</label>(.*?)<label>[^&]'
ALBUM_COLOR_MULTI_AUTHOR = re.compile(ALBUM_COLOR_MULTI_AUTHOR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_COUVERT_MULTI_AUTHOR_PATTERN = r'<label>couverture\s:</label>(.*?)<label>[^&]'
ALBUM_COUVERT_MULTI_AUTHOR = re.compile(ALBUM_COUVERT_MULTI_AUTHOR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_LETTRAGE_MULTI_AUTHOR_PATTERN = r'<label>lettrage\s:</label>(.*?)<label>[^&]'
ALBUM_LETTRAGE_MULTI_AUTHOR = re.compile(ALBUM_LETTRAGE_MULTI_AUTHOR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_INKER_MULTI_AUTHOR_PATTERN = r'<label>encrage\s:</label>(.*?)<label>[^&]'
ALBUM_INKER_MULTI_AUTHOR = re.compile(ALBUM_INKER_MULTI_AUTHOR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_DEPOT_PATTERN = r'<label>D.pot L.gal\s:\s?</label>(?P<month>[\d|-]{0,2})/?(?P<year>[\d]{2,4})?'
ALBUM_DEPOT = re.compile(ALBUM_DEPOT_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_ACHEVE_PATTERN = r'<label>Achev.*?\s:\s?</label>(?P<month>[\d|-]{0,2})/?(?P<year>[\d]{2,4})?<'
ALBUM_ACHEVE = re.compile(ALBUM_ACHEVE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_EDITEUR_PATTERN = r'<label>Editeur\s:\s?</label>(.*?)</'
ALBUM_EDITEUR = re.compile(ALBUM_EDITEUR_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_COLLECTION_PATTERN = r'<label>Collection\s:\s?</label>.*?">(.*?)</'
ALBUM_COLLECTION = re.compile(ALBUM_COLLECTION_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_TAILLE_PATTERN = r'<label>Format\s:\s?</label>.*?(.+?)</'
ALBUM_TAILLE = re.compile(ALBUM_TAILLE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_ISBN_PATTERN = r'<label>.*?ISBN\s:\s</label.*?>([^<]*?)</'
ALBUM_ISBN = re.compile(ALBUM_ISBN_PATTERN, re.IGNORECASE | re.DOTALL)

ALBUM_PLANCHES_PATTERN = r'<label>Planches\s:\s?</label>(\d*?)</'
ALBUM_PLANCHES = re.compile(ALBUM_PLANCHES_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_COVER_PATTERN = r'<meta\sproperty="og:title".*?="https:(.*?)"'
ALBUM_COVER = re.compile(ALBUM_COVER_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_RESUME_PATTERN = r'<meta\sname="description"\scontent="(.*?)"'
ALBUM_RESUME = re.compile(ALBUM_RESUME_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_INFOEDITION_PATTERN = r'<em>Info\s.*?dition\s:\s?</em>\s?(.*?)<'
ALBUM_INFOEDITION = re.compile(ALBUM_INFOEDITION_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

ALBUM_URL_PATTERN = r'<label>%s<span\sclass="numa.*?\.<.*?<a\shref="(.*?)"\s.*?title=.+?">(.+?)</'

ALBUM_SINGLE_URL_PATTERN = r'<label>%s<span\sclass="numa.*?\.%s<.*?<a\shref="(.*?)\#(.*?)"'

ALBUM_NON_NUM_URL_PATTERN = r'<label><span\sclass="numa">%s</span>.*?\.<.*?<a\shref="(.*?)"\s.*?title=.+?">(.+?)</'  

ALBUM_SINGLEALBUM_URLALL_PATTERN = r'<h3>(.*?)</h3>'
ALBUM_SINGLEALBUM_URLALL = re.compile(ALBUM_SINGLEALBUM_URLALL_PATTERN, re.DOTALL | re.IGNORECASE)

ALBUM_SINGLEALBUM_URL_PATTERN = r'href="(.*?)"\stitle.*?">.*?%s<span\sclass="numa">%s<'

ALBUMDETAILS_URL_PATTERN = r'https://www.bedetheque.com/album-%s-(.*?)"'
ALBUMDETAILSSINGLE_URL_PATTERN = r'https://www.bedetheque.com/album-(.*?)"'

ALBUM_URL_PATTERN_NOTNUM = r'<div\sclass="album.*?href="(.*?)"'
ALBUM_URL_NOTNUM = re.compile(ALBUM_URL_PATTERN_NOTNUM, re.MULTILINE | re.DOTALL | re.IGNORECASE)

ALBUM_QNUM_PATTERN = r'og:title"\scontent="(.*?)-(.*?)-?\s(.*?)"\s*/>'
ALBUM_QNUM = re.compile(ALBUM_QNUM_PATTERN, re.IGNORECASE)

ALBUM_QTITLE_PATTERN = r'titre.*?%s<span.*?name">(.*?)<'
########################################
# Info Revues
REVUE_LIST_PATTERN = r'<a\shref="https://www.bedetheque.com/revue-(.*?)">.*?libelle">(.*?)\r'

REVUE_LIST_EXISTS_PATTERN = r'<h3>\d{1,3} revue\w?? trouvée\w??</h3>'
REVUE_LIST_EXISTS = re.compile(REVUE_LIST_EXISTS_PATTERN, re.IGNORECASE | re.DOTALL)

REVUE_LIST_CHECK_PATTERN = r'<h1>Revues</h1>.*?La\srecherche\seffectu.*?\srenvoie\splus\sde\s.*?<h1>S.*?ries<'
REVUE_LIST_CHECK = re.compile(REVUE_LIST_CHECK_PATTERN, re.IGNORECASE | re.DOTALL)

REVUE_CALC_PATTERN = r'<option\svalue="(.{1,160}?)">%s</'

REVUE_HEADER_PATTERN = r'class="couv"(.{1,100}?couvertures"\shref="(https.{1,150}?)">.{1,600}?class="titre".{1,100}?#(%s)\..+?class="autres".+?)</li>'
REVUE_HEADER_PATTERN_ALT = r'<a name="%s">.+?class="couv"(.{1,100}?couvertures"\shref="(https.{1,150}?)">.+?class="titre".{1,100}?#(.+?)\..+?class="autres".+?)</li>'

REVUE_RESUME_PATTERN = r'<em>Sommaire.*?</em>(.*?)</p'
REVUE_RESUME = re.compile(REVUE_RESUME_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

REVUE_PLANCHES_PATTERN = r'>Nb\sPages\s:\s??</label>(.*?)<'
REVUE_PLANCHES = re.compile(REVUE_PLANCHES_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

REVUE_DEPOT_PATTERN = r'<label>Parution\s:s??</label>(.*?)</'
REVUE_DEPOT = re.compile(REVUE_DEPOT_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

REVUE_PERIOD_PATTERN = r'<label>P.riodicit.\s:\s??</label>(.*?)</'
REVUE_PERIOD = re.compile(REVUE_PERIOD_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)

def BD_start(books):

    global nRenamed, nIgnored, aWord

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

    global AlbumNumNum, dlgNumber, dlgName, dlgNameClean, nRenamed, nIgnored, dlgAltNumber, bError
    global PickSeries, serie_rech_prev, Shadow1, Shadow2, log_messages

    t = Thread(ThreadStart(thread_proc))

    bError = False
    log_messages = []

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

        debuglog(chr(10) + "=" * 25 + "- Begin! -" + "=" * 25 + chr(10))

        nTIMEDOUT = 0
        
        nBooks = len(books)
        PickSeries = False
        serie_rech_prev = None

        for book in books:

            TimeBookStart = clock()
            debuglog("v" * 60)

            if bStopit or (nTIMEDOUT == int(TIMEOUT)):
                if bStopit: debuglog("Cancelled from WorkerThread Start")
                return

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

            findCara = dlgName.find(SUBPATT)
            if findCara > 0 :
                lenDlgName = len(dlgName)
                totalchar = lenDlgName - findCara
                dlgName = dlgName[:-totalchar]

            mPos = re.search(r'([.,\\/])', dlgNumber)
            if not isnumeric(dlgNumber):
                albumNum = dlgNumber
                AlbumNumNum = False
            elif isnumeric(dlgNumber) and not re.search(r'[.,\\/]', dlgNumber):
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

            if bStopit:
                debuglog("Cancelled from WorkerThread after Update")
                return

            RetAlb = False
            if CBRescrape:
                if book.Web:
                    RetAlb = QuickScrapeBD2(books, book, book.Web)

            if not CBRescrape:
                debuglog(Trans(9) + dlgName + "\tNo = [" + albumNum + "]" + if_else(dlgAltNumber == '', '', '\tAltNo. = [' + dlgAltNumber + ']'))
                serieUrl = None
                debuglog(Trans(10), dlgName)
                
                RetAlb = False
                serieUrl = GetFullURL(SetSerieId(book, dlgName, albumNum, nBooks))

                if bStopit:
                    debuglog("Cancelled from WorkerThread after SetSerieId return")
                    return

                if serieUrl:
                    RetAlb = True
                    if not '/revue-' in serieUrl: 
                        LongSerie= serieUrl.lower().replace(".html", u'__10000.html')
                        serieUrl = LongSerie
                        
                    if AlbumNumNum:
                        debuglog(Trans(11), albumNum + "]", if_else(dlgAltNumber == '', '', ' - AltNo.: ' + dlgAltNumber))
                    else:
                        debuglog(Trans(12) + albumNum + "]", if_else(dlgAltNumber == '', '', ' - AltNo. [' + dlgAltNumber + ']'))

                    RetAlb = SetAlbumInformation(book, serieUrl, dlgName, albumNum)

                    #SkipAlbum utlisez lorsque l'on appuye sur Annuler (ou AllowUserChoice == 0) dans la fenetre pour choisir l'album ParseSerieInfo
                    if not SkipAlbum and not RetAlb and not '/revue-' in serieUrl:
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
            debuglog(Trans(125), str(timedelta(seconds=nSec)) + chr(10))
            debuglog("^" * 60)

            # timeout in seconds before next scrape
            if TIMEOUTS and nOrigBooks > nIgnored + nRenamed:
                cPause = Trans(140).replace("%%", str(TIMEOUTS))
                f.Update(cPause, 0, False)
                f.Refresh()
                for ii in range(20*int(TIMEOUTS)):
                    t.CurrentThread.Join(50)
                    Application.DoEvents()
                    if bStopit:
                        debuglog("Cancelled from WorkerThread TIMEOUT Loop")
                        return
            if bStopit:
                debuglog("Cancelled from WorkerThread End")
                return

    except:
        cError = debuglogOnError()
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

        TimeEnd = clock()
        nSec = int(TimeEnd - TimeStart)
        debuglog(Trans(124), str(timedelta(seconds=nSec)) )
        debuglog("=" * 25 + "- End! -" + "=" * 25 + chr(10))
        flush_debuglog()

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

            rdlg = MessageBox.Show(ComicRack.MainWindow, Trans(17) + str(nRenamed) + ", " + Trans(18) + str(nIgnored) + " (" + Trans(108) + str(nOrigBooks) + ")" , Trans(22), MessageBoxButtons.OK, MessageBoxIcon.Exclamation, MessageBoxDefaultButton.Button1)            

        t.Abort()

        return

def SetSerieId(book, serie, num, nBooksIn):

    global ListSeries, NewLink, NewSeries, RenameSeries, PickSeries, PickSeriesLink, serie_rech_prev
    
    if serie:
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

        debuglog("AlwaysChooseSerie: " + str(AlwaysChooseSerie))
        if not AlwaysChooseSerie:
            request = _read_url(urlN.encode('utf-8'), False)

            if bStopit:
                debuglog("Cancelled from SetSerieId after letter page return")
                return ''

            if request:
                RegCompile = re.compile(SERIE_URL_PATTERN % checkRegExp(serie.strip()),  re.IGNORECASE)
                nameRegex = RegCompile.search(request)

                if nameRegex:

                    serieUrl = nameRegex.group(1)
                    if not ".html" in serieUrl:serieUrl += ".html"

                    debuglog(Trans(23) + serieUrl)
                    return serieUrl

        serie_rech = remove_accents(serie.lower())
        if serie_rech == serie_rech_prev and PickSeries != False:
            serie_rech_prev = serie_rech
            RenameSeries = PickSeries
            return PickSeriesLink
        else:
            serie_rech_prev = serie_rech
            PickSeries = False

        ListSeries = list()
        debuglog("Nom de Série pour recherche = " + dlgNameClean)
        urlN = '/search/tout?RechTexte=' + remove_accents(dlgNameClean.lower().strip()) +'&RechWhere=0'

        debuglog(Trans(113), 'www.bedetheque.com' + urlN)

        request = _read_url(urlN.encode('utf-8'), False)

        if bStopit:
            debuglog("Cancelled from SetSerieId after Search return")
            return ''

        if SERIE_LIST_CHECK.search(request) or REVUE_LIST_CHECK.search(request):
            Result = MessageBox.Show(ComicRack.MainWindow, Trans(114) + '[' + titlize(book.Series) + '] !', Trans(2), MessageBoxButtons.OK, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button1)
            debuglog(Trans(114) + '[' + titlize(book.Series) + '] !')
            return ''

        i = 1
        RegCompile = re.compile(SERIE_LIST_PATTERN, re.IGNORECASE | re.DOTALL )
        for seriepick in RegCompile.finditer(request):                        
            ListSeries.append(["serie-" + seriepick.group(1), checkWebChar(strip_tags(seriepick.group(2))), str(i).zfill(3)])
            i = i + 1

        RegCompile = re.compile(REVUE_LIST_PATTERN, re.IGNORECASE | re.DOTALL )
        if REVUE_LIST_EXISTS.search(request):
            for seriepick in RegCompile.finditer(request):
                ListSeries.append(["revue-" + seriepick.group(1), checkWebChar(strip_tags(seriepick.group(2))), str(i).zfill(3)])  
                i = i + 1

        ListSeries.sort(key=operator.itemgetter(2))

        if len(ListSeries) == 1 and not AlwaysChooseSerie:
            debuglog(Trans(24) + checkWebChar(serie) + "]" )
            debuglog(Trans(111) + (ListSeries[0][1]))
            log_BD("** [" + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com" + serieUrl + ")", Trans(25), 1)
            log_BD(Trans(111), "[" + ListSeries[0][1] + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com\\" + ListSeries[0][0] + ")", 1)
            RenameSeries = ListSeries[0][1]
            return ListSeries[0][0]

        elif len(ListSeries) > 1 or (AlwaysChooseSerie and len(ListSeries) >= 1) :
            if AllowUserChoice or nBooksIn == 1:
                lUnique = False
                for i in range(len(ListSeries)):
                    if remove_accents(ListSeries[i][1].lower()) == remove_accents(dlgName.lower().strip()):
                        lUnique = True
                        nItem = i
                    if remove_accents(ListSeries[i][1].lower()) == remove_accents(dlgName.lower().strip()) and re.search(r'\(.{4,}?\)', ListSeries[i][1].lower()):
                        lUnique = False
                    if AlwaysChooseSerie:
                        lUnique = False
                if lUnique:
                    debuglog(Trans(24) + checkWebChar(serie) + "]" )
                    debuglog(Trans(111) + (ListSeries[nItem][1]))
                    log_BD("** [" + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com" + serieUrl + ")", Trans(25), 1)
                    log_BD(Trans(111), "[" + ListSeries[nItem][1] + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com\\" + ListSeries[nItem][0] + ")", 1)
                    RenameSeries = ListSeries[nItem][1]
                    return ListSeries[nItem][0]
                # Pick a series
                NewLink = ''
                NewSeries = ''
                a = ListSeries
                pickAseries = SeriesForm(serie, ListSeries, FormType.SERIE)
                result = pickAseries.ShowDialog()

                if result == DialogResult.Cancel:
                    debuglog(Trans(24) + checkWebChar(serie) + "]")
                    log_BD("** [" + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com" + serieUrl + ")", Trans(25), 1)
                    return ''
                else:
                    debuglog(Trans(24) + checkWebChar(serie) + "]")
                    debuglog(Trans(111) + (NewSeries))
                    log_BD("** [" + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com" + serieUrl + ")", Trans(25), 1)
                    log_BD(Trans(111), "[" + NewSeries + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com\\" + NewLink + ")", 1)
                    RenameSeries = NewSeries
                    PickSeries = RenameSeries
                    PickSeriesLink = NewLink
                    return NewLink
            else:
                debuglog(Trans(142) + checkWebChar(serie) + "]")
                log_BD("** [" + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo. ' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com" + serieUrl + ")", Trans(25), 1)
                return ''

    except:

        cError = debuglogOnError()
        log_BD("** Error [" + serie + "] " + num + " - " + titlize(book.Title), cError, 1)

    return serieUrl

def GetFullURL(url):
    if url:
        if re.search("https://www.bedetheque.com/", url, re.IGNORECASE):
            return url
        else:
            return "https://www.bedetheque.com/" + url
    else:
        return ''

def write_book_notes(book):
    book.Notes = "Bedetheque.com - " + str(datetime.now().strftime("%A %d %B %Y %H:%M:%S")) + chr(10) + "BD2 scraper v" + VERSION

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

    albumUrl = parseSerieInfo(book, serieUrl, False)

    if bStopit:
        debuglog("Cancelled from SetAlbumInformation")
        return False

    if albumUrl and not '/revue-' in serieUrl:
        debuglog(Trans(26), albumUrl)
        if not parseAlbumInfo(book, albumUrl, num):
            return False
        return True

    elif '/revue-' in serieUrl:
        return albumUrl

    else:
        debuglog(Trans(26), Trans(25))
        debuglog(Trans(27) + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo.' + dlgAltNumber) + "\n")
        log_BD("   [" + serie + "] " + num + if_else(dlgAltNumber == '', '', ' AltNo.' + dlgAltNumber) + " - " + titlize(book.Title) + " (www.bedetheque.com" + serieUrl + ")", Trans(28), 1)
        return False

def parseSerieInfo(book, serieUrl, lDirect):

    global Serie_Resume, SkipAlbum

    debuglog("=" * 60)
    debuglog("parseSerieInfo", "a)", serieUrl, "b)", lDirect)
    debuglog("=" * 60)

    SERIE_QSERIE = re.compile(SERIE_QSERIE_PATTERN, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    
    SkipAlbum = False
    albumURL = ''
    
    if bStopit:
        debuglog("Cancelled from parseSerieInfo Start")
        return False

    try:
        request = _read_url(serieUrl, lDirect)
    except:
        cError = debuglogOnError()
        log_BD("   " + serieUrl + " " + Trans(43), "", 1)
        return False

    if bStopit:
        debuglog("Cancelled from parseSerieInfo after _read_url return")
        return False

    if '/revue-' in serieUrl:
        i = 1
        ListAlbum = list()
        REVUE_LIST_ALL = re.findall(r"<option\svalue=\"(https://www\.bedetheque\.com/revue-[^>]+?)\">(.+?)</option>", request, re.IGNORECASE | re.DOTALL | re.MULTILINE)

        #When only 1 page
        if not REVUE_LIST_ALL or len(REVUE_LIST_ALL) == 0:
            REVUE_LIST_ALL_ALT = re.findall(r'<a name="(.+?)">.+?class="titre".{1,100}?#(.+?)\..+?', request, re.IGNORECASE | re.DOTALL | re.MULTILINE)
            for revueNum in REVUE_LIST_ALL_ALT:
                full_url = serieUrl + "#" + revueNum[0] if "www.bedetheque.com" in serieUrl.lower() else "https://www.bedetheque.com/" + serieUrl + "#" + revueNum[0]
                ListAlbum.append([full_url, "Num: " + revueNum[1].strip(), str(i).zfill(5)])
                i = i + 1
        else:
            for albumPick in REVUE_LIST_ALL:
                ListAlbum.append([albumPick[0], "Num: " + albumPick[1].strip(), str(i).zfill(5)])
                i = i + 1

        matchedAlbum = next((x for x in ListAlbum if x[1] == "Num: " + dlgNumber), None) #find num in list
        if matchedAlbum is not None and not lDirect:
            albumURL = matchedAlbum[0]
        elif lDirect and '#' in serieUrl:
            albumURL = serieUrl
        else:
            albumURL = AlbumChooser(ListAlbum)

        if not albumURL:
            return ""

        request = _read_url(albumURL, False)
        
        ID = albumURL.split('#')[1] if '#' in albumURL else ''
        if ID:
            REVUE_HEADER = re.compile(REVUE_HEADER_PATTERN_ALT % ID, re.IGNORECASE | re.MULTILINE | re.DOTALL)   
        else:
            REVUE_HEADER = re.compile(REVUE_HEADER_PATTERN % dlgNumber, re.IGNORECASE | re.MULTILINE | re.DOTALL) 
            
        SerieInfoRegex = REVUE_HEADER.search(request)
        if SerieInfoRegex:
            RetVal = parseRevueInfo(book, SerieInfoRegex, albumURL)
            return RetVal
        else:
            return ""

    else:
        if request:

            Entete = request

            if RenameSeries:
                if CBSeries:
                    book.Series = titlize(RenameSeries)

            #Series if Quickscrape
            if lDirect and CBSeries:
                nameRegex = SERIE_QSERIE.search(Entete)
                if nameRegex:
                    qserie = checkWebChar(nameRegex.group(1).strip())
                    book.Series = titlize(qserie)
                    debuglog(Trans(9), qserie)
                else:
                    albumURL = False
                    return ""

            #genre
            if CBGenre:
                nameRegex = SERIE_GENRE.search(Entete)
                if nameRegex:
                    genre = checkWebChar(nameRegex.group(1).strip())
                else:
                    genre = ""
                if genre != "":
                    book.Genre = genre
                    # Flag Erotique/Érotique genre as PG
                    if 'rotique' in genre.lower():
                        book.AgeRating = "PG"
                elif genre == "" and '/revue-' in serieUrl:
                    book.Genre = "Revue"
                debuglog(Trans(51), book.Genre)

            #Resume
            if CBSynopsys:
                nameRegex = SERIE_RESUME.search(checkWebChar(Entete.replace("\r\n","")), 0)
                if nameRegex:
                    resume = strip_tags(nameRegex.group(1)).strip()
                else:
                    resume = ""

                resume = re.sub(r'Tout sur la série.*?:\s?', "", resume, re.IGNORECASE)
                Serie_Resume = (checkWebChar(resume)).strip()
                cResume = if_else(resume, Trans(52), Trans(53))
                debuglog(cResume)

            #fini
            if CBStatus:
                SerieState = ""
                nameRegex = SERIE_STATUS.search(Entete)
                if nameRegex:
                    fin = checkWebChar(nameRegex.group(1).strip())
                    log_BD(fin, Trans(25), 1)
                else:
                    fin = ""

                if ("finie" in fin) or (dlgNumber.lower() == "one shot"):
                    book.SeriesComplete = YesNo.Yes
                    SerieState = Trans(54)
                elif ("one shot" in fin.lower()) and (dlgNumber.lower() != "one shot"):
                    book.SeriesComplete = YesNo.Yes
                    if ONESHOTFORMAT and not CBFormat:
                        book.Format = "One Shot"
                    SerieState = Trans(54)
                elif ("cours" in fin):
                    book.SeriesComplete = YesNo.No
                    SerieState = Trans(55)
                else:
                    book.SeriesComplete = YesNo.Unknown
                    SerieState = Trans(56)

                debuglog(Trans(57) + SerieState + if_else(dlgNumber.lower() == "one shot", " (One Shot)", ""))

            # Language
            if CBLanguage:
                nameRegex = SERIE_LANGUE.search(Entete)
                dLang = {"Fr": "fr", "Al": "de", "An": "en", "It":"it", "Es":"es", "Ne":"du", "Po":"pt", "Ja":"ja"}
                if nameRegex:
                    langue = nameRegex.group(1).strip()
                    debuglog(Trans(36), langue[:2])
                    book.LanguageISO = dLang[langue[:2]]

            #Default Values
            if not CBDefault:
                book.EnableProposed = YesNo.No
                debuglog(Trans(136), "No")

            SerieInfoRegex = SERIE_HEADER2.search(request)
            if SerieInfoRegex:
                Entete2 = SerieInfoRegex.group(1)
    
                #Notes-Rating
                #if CBRating:
                #    nameRegex = SERIE_NOTE.search(Entete)
                #    if nameRegex:
                #        note = nameRegex.group('note')
                #    else:
                #        note = "0.0"
    
                #    book.CommunityRating = float(note) / 2
                #    debuglog(Trans(58) + str(float(note) / 2))
                
                # Number of...
                if CBCount and not lDirect:

                    count = 0
                    cCountText = ""
                    if COUNTFINIE and book.SeriesComplete == YesNo.No:
                        book.Count = -1
                        cCountText = "---"
                    elif not COUNTOF:
                        nameRegex = SERIE_COUNT.search(Entete2)
                        if nameRegex and AlbumNumNum:
                            count = checkWebChar(nameRegex.group(1))
                            book.Count = int(count)
                            cCountText = str(int(count))
                        else:
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
                            elif not AlbumNumNum:
                                book.Count = -1
                        else:
                            book.Count = -1
                            cCountText = "---"

                    debuglog(Trans(59) + if_else(dlgNumber.lower() == "one shot", "1", cCountText))

            Regex = re.compile(r'<label>([^<]*?)<span\sclass=\"numa\">(.*?)</span.*?<a\shref=\"(.*?)".*?title=.+?\">(.+?)</', re.IGNORECASE | re.DOTALL)

            i = 0
            ListAlbum, ListAlbumAll = list(), list()
            for r in Regex.finditer(request):
                n, a, url, title = r.group(1), r.group(2), r.group(3), r.group(4)
                num = if_else(n,n, if_else(a, a, ""))
                ListAlbumAll.append([url, num + ". " + title, str(i).zfill(3)])
                if dlgNumber != "" and (num == dlgNumber) and not lDirect:
                    ListAlbum.append([url, num + ". " + title, str(i).zfill(3)])
                i = i + 1

            if len(ListAlbum) == 0: 
                ListAlbum = ListAlbumAll

            albumURL = AlbumChooser(ListAlbum)
            if not albumURL and not SkipAlbum:
                #Rien trouvé il ce peux qu'il n'est pas de liste sur le coté, surement 1 seul item
                Regex = re.compile(r'class="titre"\shref="(.+?)".+?<span class="numa">.*?</span>.+?', re.IGNORECASE | re.DOTALL)
                r = Regex.search(request)
                if r:
                    albumURL = r.group(1)
                    debuglog("---> Numéro n'existe pas dans la liste, choix du 1er item")
                else:
                    return ""

    return albumURL

"""
ListAlbum elements: 
    1st is the URL
    2nd is the title
"""
def AlbumChooser(ListAlbum):

    global NewLink, SkipAlbum

    albumURL = ""
    debuglog("Nbr. d'item dans la Liste Album est de: " + str(len(ListAlbum)))
    if len(ListAlbum) > 1:
        if AllowUserChoice:
            NewLink = ""
            NewSeries = ""
            pickAnAlbum = SeriesForm(dlgNumber, ListAlbum, FormType.ALBUM)
            result = pickAnAlbum.ShowDialog()
                
            if result == DialogResult.Cancel:
                if TIMEPOPUP != "0" and TimerExpired:
                    albumURL = ListAlbum[0][0]
                    debuglog("---> Le temps est expiré, choix du 1er item")
                else:
                    albumURL = False
                    SkipAlbum = True
                    debuglog("---> Appuyer sur Cancel, ignorons ce livre")
            else:
                albumURL = NewLink
        else:
            albumURL = False
            SkipAlbum = True
            debuglog("---> Plus d'un item mais l'option pause scrape est désactivé")
    elif len(ListAlbum) == 1:
        albumURL = ListAlbum[0][0]
        debuglog("---> Seulement 1 item dans la liste")

    return albumURL

def parseRevueInfo(book, SerieInfoRegex, serieUrl, Numero = "", serie = ""):

    debuglog("=" * 60)
    debuglog("parseRevueInfo", "a)", serieUrl, "b)", Numero)
    debuglog("=" * 60)
    try:
        
        Entete = SerieInfoRegex.group(1)
        Numero = SerieInfoRegex.group(3) if not Numero else Numero

        if RenameSeries:
            if CBSeries:
                book.Series = titlize(RenameSeries)
        else:
            if CBSeries:
                book.Series = titlize(book.Series)

        if Numero:
            try:
                book.Number = Numero
                debuglog(Trans(115), book.Number)
            except:
                book.Number = ""

        if serie:
            try:
                if serie.group(1):
                    if CBSeries:
                        book.Series = titlize(serie.group(1))
                        debuglog(Trans(9), titlize(book.Series))
            except:
                pass

        #Title
        if CBTitle:
            nameRegex = re.search(r'<h3 class="titre".+?</span>(.+?)</h3>', Entete, re.IGNORECASE | re.DOTALL | re.MULTILINE)
            if nameRegex: 
                book.Title = titlize(nameRegex.group(1).strip())
            debuglog(Trans(29), book.Title)

        #genre
        if CBGenre:
            book.Genre = "Revue"
            debuglog(Trans(51), book.Genre)

        #Resume
        if CBSynopsys:
            nameRegex = REVUE_RESUME.search(Entete)
            if nameRegex:
                resume = strip_tags(nameRegex.group(1)).strip()
            else:
                resume = ""
            book.Summary = (checkWebChar(resume)).strip()
            cResume = if_else(resume, Trans(52), Trans(53))
            debuglog(cResume)

        #Notes-Rating
        if CBRating:
            nameRegex = SERIE_NOTE.search(Entete)
            if nameRegex:
                note = nameRegex.group('note')
            else:
                note = "0.0"

            book.CommunityRating = float(note)
            debuglog(Trans(58) + str(float(note)))

        #Couverture
        # Cover Image only for fileless
        if CBCover and not book.FilePath:
            CoverImg = SerieInfoRegex.group(2)
            request = HttpWebRequest.Create(CoverImg)
            response = request.GetResponse()
            response_stream = response.GetResponseStream()
            retval = Image.FromStream(response_stream)
            ComicRack.App.SetCustomBookThumbnail(book, retval)
            debuglog(Trans(105), CoverImg)

        #Parution
        if CBPrinted:
            nameRegex = REVUE_DEPOT.search(Entete, 0)
            if nameRegex:
                if nameRegex.group(1) != '-':
                    book.Month = int(nameRegex.group(1)[3:5])
                    book.Year = int(nameRegex.group(1)[6:10])
                    debuglog(Trans(34), str(book.Month) + "/" + str(book.Year))
                else:
                    book.Month = -1
                    book.Year = -1
            else:
                book.Month = -1
                book.Year = -1

        #Editeur
        if CBEditor:
            nameRegex = ALBUM_EDITEUR.search(Entete, 0)
            if nameRegex:
                editeur = parseName(nameRegex.group(1))
                book.Publisher = editeur
            else:
                book.Publisher = ""
                    
            debuglog(Trans(35), book.Publisher)

        # Planches
        if not book.FilePath:
            nameRegex = REVUE_PLANCHES.search(Entete, 0)
            if nameRegex:
                pages = nameRegex.group(1).strip()
                book.PageCount = int(pages) if isnumeric(pages) else -1
                debuglog(Trans(122), pages)

        #Periodicité
        if CBFormat:
            nameRegex = REVUE_PERIOD.search(Entete, 0)
            if nameRegex:
                book.Format = nameRegex.group(1).strip()
                debuglog(Trans(131), nameRegex.group(1))

        #Always set Language to french
        if CBLanguage and not book.LanguageISO:
            book.LanguageISO = "fr"

        #web
        if CBWeb == True and not CBRescrape:
            book.Web = serieUrl
            debuglog(Trans(123), book.Web)

        if CBNotes:
            write_book_notes(book)

        return True

    except:

        return False

class AlbumInfo:
    def __init__ (self, n, a, title, info, couv, url):
        self.Couv = couv
        self.N = n
        self.A = a
        self.Title = title
        self.Info = info
        self.URL = url

def parseAlbumInfo(book, pageUrl, num, lDirect = False):

    global CBelid, NewLink, NewSeries

    debuglog("=" * 60)
    debuglog("parseAlbumInfo", "a)", pageUrl, "b)", num , "c)", lDirect)
    debuglog("=" * 60)

    AlbumBDThequeNum = ""

    if bStopit:
        debuglog("Cancelled from parseAlbumInfo Start")
        return False

    albumUrl = _read_url(pageUrl, False)

    if bStopit:
        debuglog("Cancelled from parseAlbumInfo after _read_url return")
        return False

    #identify the album n. in BDTHQ
    cBDNum = False
    cBDNumS = re.search(r'-(\d+).html', pageUrl)
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
        tome = re.search(r'<h2>\s*(-?\w*?)<span class="numa">(.*?)</span>.', albumUrl, re.IGNORECASE | re.DOTALL)
        #if no tome take alt number from top of the page
        t = if_else(tome.group(1), tome.group(1), checkWebChar(tome.group(2).strip())) if tome else ""
        #nameRegex groups (inside editions): group#1 => cover, group#2 => tome, group#3 => alt, group#4 => titre, group#5 => info (artists table), group#6 => url anchor
        nameRegex = re.compile(r'class="couv">.+?href="(.+?)".+?class="titre".*?>([^<>]*?)<span class="numa">(.*?)</span>.+?\r\n\s+(.+?)</.+?>(.+?)<div class="album-admin".*?id="bt-album-(.+?)">', re.IGNORECASE | re.DOTALL | re.MULTILINE)
        for albumPick in nameRegex.finditer(albumUrl):    
            couv = re.sub('/cache/thb_couv/', '/media/Couvertures/', albumPick.group(1)) if albumPick.group(1) else "" #get higher resolution image
            title = checkWebChar(albumPick.group(4).strip())
            nfo = albumPick.group(5)
            # a is altNumber
            a = checkWebChar(albumPick.group(3).strip() if isnumeric(t) else albumPick.group(3).strip().replace(t,'',1).strip())
            url = pageUrl + "#reed" if i == 0 else pageUrl + "#" + albumPick.group(6).strip()
            albumInfo = AlbumInfo(t, a, title, nfo, couv, url)
            debuglog("Tome)", t, "Alt)", a, "Title)", title)

            ListAlbum.append([a, albumInfo, str(i).zfill(3)])
            i = i + 1

        if len(ListAlbum) == 1:
            pickedVar = ListAlbum[0][1]
            debuglog("---> Seulement 1 item dans la liste")
        elif len(ListAlbum) > 1:
            for f in ListAlbum:
                #iterate over editions and if AltNumber matches auto choose it.
                if dlgAltNumber != "" and f[1].A == dlgAltNumber:
                    pickedVar = f[1]
                    picked = True
                    break

            #set that the already picked edition from above wasn't chosen when the option to choose is enabled in config, so we will have the chance to pick it later.
            if PopUpEditionForm:
                picked = False

            #show the choose editions form when the option is enabled and the edition wasn't already chosen earlier based on the AltNumber from the book.
            #NewLink (first element from the ListAlbum, in this case the var "a") & NewSeries (object AlbumInfo) are global value that are set when ok is clicked on the form
            if PopUpEditionForm and AllowUserChoice and not picked:
                NewLink = ""
                NewSeries = ""
                pickAvar = SeriesForm(num, ListAlbum, FormType.EDITION)
                result = pickAvar.ShowDialog()

                if result == DialogResult.Cancel:
                    pickedVar = ListAlbum[0][1]
                    if TimerExpired: debuglog("---> Le temps est expiré, choix du 1er item") 
                    else: debuglog("---> Cancel appuyer, on choisi le premier")

                else:
                    pickedVar = NewSeries
            elif not picked:
                pickedVar = ListAlbum[0][1]
                debuglog("---> Choix du 1er item")

        if pickedVar :
            info = pickedVar.Info
            debuglog("Choisi #Alt: " + pickedVar.A + " // Titre: " + pickedVar.Title)

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
                if not ShortWebLink:
                    book.Web = pickedVar.URL.replace("#reed", "")
                    debuglog(Trans(123), book.Web)
                else:
                    cBelid = re.search(r'-(\d+).html', pageUrl)
                    if cBelid:
                        book.Web = 'www.bedetheque.com/BD--' + cBelid.group(1) + '.html'
                        debuglog(Trans(123), book.Web)

            qnum = pickedVar.N#is equal to t always, but keep it in case of needed modification
            anum = pickedVar.A
            book.Number = anum if not qnum and anum else qnum#set number to Alt if no number and an Alt Exists
            book.AlternateNumber = dlgAltNumber if not qnum and anum else anum#Don't change if prev was set to anum, else set to Alt
            if PadNumber != "0":
                if isPositiveInt(book.Number): book.Number = str(book.Number).zfill(int(PadNumber))
                if isPositiveInt(book.AlternateNumber): book.AlternateNumber = str(book.AlternateNumber).zfill(int(PadNumber))
            debuglog("Num: ", book.Number)
            debuglog("Alt: ", book.AlternateNumber)

            series = book.Series
            nameRegex = re.search('bandeau-info.+?<h1>.+?>([^"]+?)[<>]', albumUrl, re.IGNORECASE | re.DOTALL | re.MULTILINE)# Les 5 Terres Album et Serie, Comme avant
            nameRegex2 = re.search("<label>S.rie : </label>(.+?)</li>", albumUrl, re.IGNORECASE | re.DOTALL | re.MULTILINE)# 5 Terres (Les) sur Album seulement
            if nameRegex:
                series = checkWebChar(nameRegex.group(1).strip())
                seriesFormat = checkWebChar(nameRegex2.group(1).strip()) if nameRegex2 else series
                debuglog(Trans(9) + series + ' // Formaté: ' + seriesFormat)

            if CBTitle:
                NewTitle = ""
                try:
                    NewTitle = titlize(pickedVar.Title)
                except:
                    NewTitle = pickedVar.Title

                if NewTitle.lower() == series.lower():
                    NewTitle = ""

                book.Title = NewTitle
                debuglog(Trans(29), book.Title)

            if TBTags == "DEL":
                book.Tags = ""
            elif TBTags != "":
                book.Tags = TBTags

            if CBWriter:
                book.Writer = getGenericBookArtists([ALBUM_SCENAR_MULTI_AUTHOR, ALBUM_STORYBOARD_MULTI_AUTHOR], info, Trans(30))

            if CBPenciller:
                book.Penciller = getGenericBookArtists([ALBUM_DESSIN_MULTI_AUTHOR], info, Trans(31))

            if CBColorist:
                book.Colorist = getGenericBookArtists([ALBUM_COLOR_MULTI_AUTHOR], info, Trans(33))
                if '<N&B>' in book.Colorist:
                    book.BlackAndWhite = YesNo.Yes
                elif book.Colorist:
                    book.BlackAndWhite = YesNo.No
            
            if CBCouverture:
                book.CoverArtist = getGenericBookArtists([ALBUM_COUVERT_MULTI_AUTHOR], info, Trans(121))

            if CBLetterer:
                book.Letterer = getGenericBookArtists([ALBUM_LETTRAGE_MULTI_AUTHOR], info, Trans(38))

            if CBInker:
                book.Inker = getGenericBookArtists([ALBUM_INKER_MULTI_AUTHOR], info, Trans(73))

            if CBPrinted:
                nameRegex = ALBUM_DEPOT.search(info, 0)
                if nameRegex:
                    if nameRegex.group('month') != '-' and nameRegex.group('month') != "":
                        book.Month = int(nameRegex.group('month'))
                        book.Year = int(nameRegex.group('year'))
                        debuglog(Trans(34), str(book.Month) + "/" + str(book.Year))
                    else:
                        book.Month = -1
                        book.Year = -1
                else:
                    book.Month = -1
                    book.Year = -1

            if CBEditor:
                nameRegex = ALBUM_EDITEUR.search(info, 0)
                if nameRegex:
                    editeur = parseName(nameRegex.group(1)).strip()
                    book.Publisher = editeur
                else:
                    book.Publisher = ""

                debuglog(Trans(35), book.Publisher)

            if CBISBN:
                nameRegex = ALBUM_ISBN.search(info, 0)
                if nameRegex:
                    isbn = nameRegex.group(1)
                    if isbn    != '</span>':
                        book.ISBN = checkWebChar(isbn)
                    else:
                        book.ISBN = ""
                else:
                    book.ISBN = ""

                debuglog("ISBN: ", book.ISBN)

            # Album evaluation is optional => So, there is a specific research
            if CBRating:
                nameRegex = ALBUM_EVAL.search(albumUrl, 0)
                if nameRegex:
                    evaluation = nameRegex.group(1)
                    book.CommunityRating = float(evaluation)
                    debuglog(Trans(39) + str(float(evaluation)))

            # Achevè imp. is optional => So, there is a specific research
            if CBPrinted:
                nameRegex = ALBUM_ACHEVE.search(info, 0)
                if nameRegex and book.Month < 1:
                    book.Month = int(nameRegex.group('month'))
                    book.Year = int(nameRegex.group('year'))
                    debuglog(Trans(40), str(book.Month) + "/" + str(book.Year))

            # Collection is optional => So, there is a specific research
            if CBImprint:
                nameRegex = ALBUM_COLLECTION.search(albumUrl, 0)
                nameRegex2 = ALBUM_COLLECTION.search(info, 0)
                if nameRegex or nameRegex2:
                    if nameRegex2:
                        nameRegex = nameRegex2

                    collection = nameRegex.group(1)
                    book.Imprint = checkWebChar(collection)
                else:
                    book.Imprint = ""

                debuglog(Trans(41), book.Imprint)

            # Format is optional => So, there is a specific research
            if CBFormat:
                nameRegex = ALBUM_TAILLE.search(info, 0)
                if nameRegex:
                    taille = nameRegex.group(1)
                    book.Format = taille
                else:
                    book.Format = "" 

                debuglog(Trans(42), book.Format)

            # Album summary is optional => So, there is a specific research
            if CBSynopsys:
                summary = ""
                nameRegex = ALBUM_RESUME.search(albumUrl, 0)
                if nameRegex:
                    resume = strip_tags(nameRegex.group(1)).strip()
                    resume = re.sub(r'Tout sur la série.*?:\s?', "", resume, re.IGNORECASE)
                    PrintSerieResume = True if SerieResumeEverywhere else book.Number == '1'
                    if Serie_Resume and PrintSerieResume and remove_accents(Serie_Resume) != remove_accents(resume):
                        summary = Serie_Resume + if_else(resume, chr(10) + chr(10) + if_else(book.Title, '>' + book.Title + '< ' + chr(10), "") + resume, "")                    
                    elif resume:
                        summary = if_else(book.Title, '>' + book.Title + '< ' + chr(10), "") + resume

                        debuglog(Trans(100))
                else:
                    debuglog(Trans(101))

                # Info edition
                nameRegex = ALBUM_INFOEDITION.search(info, 0)
                if nameRegex:
                    if nameRegex.group(1) !=" &nbsp;":
                        infoedition = strip_tags(nameRegex.group(1)).strip()
                        if infoedition:
                            summary = if_else(summary != "",summary + chr(10) + chr(10) + Trans(118) + infoedition,Trans(118) + infoedition)
                        debuglog(Trans(118) + Trans(119))

                #Send Summary to book
                if summary:
                    book.Summary = summary

            # series
            if CBSeries:
                formatted = titlize(seriesFormat, False) if seriesFormat else titlize(series, True)
                book.Series = formatted if FORMATARTICLES else titlize(series, False)
                debuglog(Trans(9), book.Series)

            # Cover Image only for fileless
            if CBCover and not book.FilePath:
                if pickedVar.Couv:
                    CoverImg = pickedVar.Couv
                    request = HttpWebRequest.Create(CoverImg)
                    response = request.GetResponse()
                    response_stream = response.GetResponseStream()
                    retval = Image.FromStream(response_stream)
                    ComicRack.App.SetCustomBookThumbnail(book, retval)
                    debuglog(Trans(105), CoverImg    )

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

                    debuglog(Trans(122), book.PageCount)

            if CBNotes:
                write_book_notes(book)

    except:
        nameRegex = ""
        cError = debuglogOnError()
        log_BD("   " + pageUrl + " " + Trans(43), "", 1)
        return False

    return True

def getGenericBookArtists(patterns, book_info, label):

    """ Parse album info for artists (writer, penciller, colorist, etc.) """
    result = ''
    artist_list = []
    for pattern in patterns:
        nameRegex = pattern.search(book_info, 0)
        if nameRegex:
            # Special process for 'Indéterminé' which is not usually using a link (i.e. https://www.bedetheque.com/serie-25893-BD-June-Aredit.html)
            if '&lt;Indéterminé&gt;' in nameRegex.group(1):
                if AcceptGenericArtists:
                    thisArtist = '<Indéterminé>'
                    if thisArtist not in artist_list:
                        artist_list.append(thisArtist)
            else:
                for artist_multi in ALBUM_MULTI_AUTHOR_NAMES.finditer(nameRegex.group(1)):
                    thisArtist = parseName(artist_multi.group(1).strip())
                    if thisArtist not in artist_list:
                        artist_list.append(thisArtist)
            result = ', '.join(artist_list)
    debuglog(label + ':', result)
    return result

def parseName(extractedName):
    name = extractedName.strip()
    if not AcceptGenericArtists and re.match(r'&lt;', extractedName):
        return ''

    nameRegex = LAST_FIRST_NAMES.search(extractedName)
    if nameRegex:
        name = nameRegex.group('firstname') + ' ' + nameRegex.group('name')

    return checkWebChar(name).strip()


def _read_url(url, bSingle):

    page = ''
    if bStopit:
        debuglog("Cancelled from _read_url Start")
        return page

    if not bSingle and re.search("https://www.bedetheque.com/", url, re.IGNORECASE):
        bSingle = True

    if bSingle:
        requestUri = url_fix(url)
    else:
        requestUri = url_fix("https://www.bedetheque.com/" + url)

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
        if bStopit:
            debuglog("Cancelled from _read_url End")
            return page

        inStream = webresponse.GetResponseStream()
        encode = System.Text.Encoding.GetEncoding("utf-8")
        ReadStream = System.IO.StreamReader(inStream, encode)
        #ReadStream.BaseStream.ReadTimeout = 15000
        page = ReadStream.ReadToEnd()

    except URLError, e:
        debuglog(Trans(60))
        debuglog(Trans(61), e)
        cError = debuglogOnError()
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
    strIn = re.sub('"', '&quot;', strIn)
    strIn = re.sub('\$', '\\$', strIn)

    return strIn

def strip_tags(html):
    try:
        return re.sub("<[^<>]+?>", "", html, re.IGNORECASE | re.DOTALL | re.MULTILINE)
    except:
        return html

def thread_proc():

    pass

    def handle(w, a): 
        pass

def debuglogOnError():
    global bError

    traceback = sys.exc_info()[2]
    stackTrace = []

    logfile = (__file__[:-len('BedethequeScraper2.py')] + "BD2_debug_log.txt")

    print("Writing Log to " + logfile)
    print('Caught ', sys.exc_info()[0].__name__, ': ', sstr(sys.exc_info()[1]))

    with open(logfile, 'a') as log:
        log.write("\n\n" + str(datetime.now().strftime("%A %d %B %Y %H:%M:%S")) + "\n")
        cError = sstr(sys.exc_info()[1])
        log.write("".join(['Caught ', sys.exc_info()[0].__name__, ': ', cError, '\n']).encode('utf-8'))

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
            print(nL, "-", line)
            log.write(",".join("%s" % tup for tup in line).encode('utf-8') + "\n")

    bError = True

    return cError

def debuglog(*args):
    try:
        message = u' '.join(unicode(arg) for arg in args)
    
        if DBGONOFF: print(message)
        log_messages.append(message)
    except Exception as e:
        print(e)

def flush_debuglog():
    try:
        logfile = os.path.join(os.path.dirname(__file__), "BD2_debug_log.txt")
        
        with open(logfile, 'a') as log:
            log.write ("\n\n" + str(datetime.now().strftime("%A %d %B %Y %H:%M:%S")) + "\n")
            for message in log_messages:
                log.write(message.encode('utf-8') + "\n")
    
        del log_messages[:]

    except Exception as e:
        print(e)

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

    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
    path = quote(path, "%/:=&~#+$!,?;'@()*[]")
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

class ProgressBarDialog(BaseForm):

    def __init__(self, nMax):

        global bStopit
        bStopit = False
        self.Text = Trans(62)
        self.ClientSize = System.Drawing.Size(350, 590)
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

        self.traitement.Location = Point(8, 5)
        self.traitement.UseMnemonic = False
        self.traitement.Name = "traitement"
        self.traitement.Size = Size(334, 50)
        self.traitement.Text = ""

        self.pb.Size = Size(334, 20)
        self.pb.Location = Point(8, 40)
        self.pb.Maximum = nMax
        self.pb.Minimum = 0
        self.pb.Step = 1
        self.pb.Value = 0
        self.pb.BackColor = Color.LightGreen
        self.pb.Text = ""
        self.pb.ForeColor = Color.Black

        self.cancel.DialogResult = DialogResult.Cancel
        self.cancel.Location = Point(137, 70)
        self.cancel.Name = "cancel"
        self.cancel.Size = Size(76, 25)
        self.cancel.TabIndex = 1
        self.cancel.Text = Trans(99)
        self.cancel.UseVisualStyleBackColor = True
        self.cancel.BackColor = Color.Red
        self.cancel.Click += self.button_Click

        self.cover.Location = Point(8, 100)
        self.cover.Name = "cover"
        self.cover.Size = Size(334, 478)
        self.cover.SizeMode = PictureBoxSizeMode.Zoom

        self.Controls.Add(self.pb)
        self.Controls.Add(self.traitement)
        self.Controls.Add(self.cancel)
        self.Controls.Add(self.cover)

        # Adjust DPI scaling in this form
        HighDpiHelper.AdjustControlImagesDpiScale(self)

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

        HighDpiHelper.AdjustPictureBoxDpiScale(self.cover, HighDpiHelper.GetDpiScale(self))

    def button_Click(self, sender, e):

        global bStopit

        Application.DoEvents()
        if sender.Name.CompareTo(self.cancel.Name) == 0:
            debuglog("Cancel button pressed")
            bStopit = True

def LoadSetting():

    global SHOWRENLOG, SHOWDBGLOG, DBGONOFF, DBGLOGMAX, RENLOGMAX, LANGENFR, aWord, ARTICLES, SUBPATT, COUNTOF, COUNTFINIE, TITLEIT, TIMEOUT, TIMEOUTS, TIMEPOPUP, FORMATARTICLES, ONESHOTFORMAT
    global TBTags, CBCover, CBStatus, CBGenre, CBNotes, CBWeb, CBCount, CBSynopsys, CBImprint, CBLetterer, CBInker, CBPrinted, CBRating, CBISBN, CBDefault, CBRescrape, AllowUserChoice, PopUpEditionForm, PadNumber, SerieResumeEverywhere
    global CBLanguage, CBEditor, CBFormat, CBColorist, CBPenciller, CBWriter, CBTitle, CBSeries, CBCouverture, AlwaysChooseSerie, ShortWebLink, AcceptGenericArtists

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
        cError = debuglogOnError()
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
        ShortWebLink = ft(MySettings.Get("ShortWebLink"))
    except Exception as e:
        ShortWebLink = False
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
        CBInker = ft(MySettings.Get("CBInker"))
    except Exception as e:
        CBInker = True
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
        CBSeries = ft(MySettings.Get("CBSeries"))
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
        AllowUserChoice = ft(MySettings.Get("CBStop"))
    except Exception as e:
        AllowUserChoice = "2"
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
        SerieResumeEverywhere = ft(MySettings.Get("SerieResumeEverywhere"))
    except Exception as e:
        SerieResumeEverywhere = True
    try:
        PadNumber = MySettings.Get("PadNumber")
    except Exception as e:
        PadNumber = "0"
    try:
        ONESHOTFORMAT = ft(MySettings.Get("ONESHOTFORMAT"))
    except Exception as e:
        ONESHOTFORMAT = False
    try:
        AlwaysChooseSerie = ft(MySettings.Get("AlwaysChooseSerie"))
    except Exception as e:
        AlwaysChooseSerie = False
    try:
        AcceptGenericArtists = ft(MySettings.Get("AcceptGenericArtists"))
    except Exception as e:
        AcceptGenericArtists = False
    ###############################################################
    
    if ONESHOTFORMAT and CBFormat:
        CBFormat = False

    # Compatibility with old version
    if CBWeb == 2:
        CBWeb = True
        ShortWebLink = True

    SaveSetting()

    aWord = Translate()

    return True
    
def SaveSetting():
    
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
    MySettings.Set("CBWeb",  tf(CBWeb))
    MySettings.Set("ShortWebLink",  tf(ShortWebLink))
    MySettings.Set("CBCount",  tf(CBCount))
    MySettings.Set("CBSynopsys",  tf(CBSynopsys))
    MySettings.Set("CBImprint",  tf(CBImprint))
    MySettings.Set("CBLetterer",  tf(CBLetterer))
    MySettings.Set("CBInker",  tf(CBInker))
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
    MySettings.Set("SerieResumeEverywhere", tf(SerieResumeEverywhere))
    MySettings.Set("AlwaysChooseSerie", tf(AlwaysChooseSerie))
    MySettings.Set("ONESHOTFORMAT", tf(ONESHOTFORMAT))
    MySettings.Set("AcceptGenericArtists", tf(AcceptGenericArtists))
    
    if AllowUserChoice == True:
        MySettings.Set("CBStop",  "1")
    elif AllowUserChoice == False:
        MySettings.Set("CBStop",  "0")
    elif AllowUserChoice == "2":
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

class BDConfigForm(BaseForm):

    def __init__(self):

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
        self._tabPage3 = System.Windows.Forms.TabPage()
        self._labelTags = System.Windows.Forms.Label()
        self._TBTags = System.Windows.Forms.TextBox()
        self._CBDefault = System.Windows.Forms.CheckBox()
        
        self._ScrapedDataCheckedListBox = System.Windows.Forms.CheckedListBox()
        self._scrapedData = collections.OrderedDict(
            [
                ('Series', {'label': Trans(71), 'state': if_else(CBSeries, CheckState.Checked, CheckState.Unchecked)}),
                ('Title', {'label': Trans(72), 'state': if_else(CBTitle, CheckState.Checked, CheckState.Unchecked)}),
                ('Writer', {'label': Trans(30), 'state': if_else(CBWriter, CheckState.Checked, CheckState.Unchecked)}),
                ('Penciller', {'label': Trans(31), 'state': if_else(CBPenciller, CheckState.Checked, CheckState.Unchecked)}),
                ('Colorist', {'label': Trans(33), 'state': if_else(CBColorist, CheckState.Checked, CheckState.Unchecked)}),
                ('Letterer', {'label': Trans(38), 'state': if_else(CBLetterer, CheckState.Checked, CheckState.Unchecked)}),
                ('Inker', {'label': Trans(73), 'state': if_else(CBInker, CheckState.Checked, CheckState.Unchecked)}),
                ('CoverArtist', {'label': Trans(121), 'state': if_else(CBCouverture, CheckState.Checked, CheckState.Unchecked)}),
                ('Publisher', {'label': Trans(78), 'state': if_else(CBEditor, CheckState.Checked, CheckState.Unchecked)}),
                ('Language', {'label': Trans(79), 'state': if_else(CBLanguage, CheckState.Checked, CheckState.Unchecked)}),
                ('Format', {'label': Trans(77), 'state': if_else(CBFormat, CheckState.Checked, CheckState.Unchecked)}),
                ('Rating', {'label': Trans(81), 'state': if_else(CBRating, CheckState.Checked, CheckState.Unchecked)}),
                ('Printed', {'label': Trans(82), 'state': if_else(CBPrinted, CheckState.Checked, CheckState.Unchecked)}),
                ('Imprint', {'label': Trans(83), 'state': if_else(CBImprint, CheckState.Checked, CheckState.Unchecked)}),
                ('Synopsys', {'label': Trans(84), 'state': if_else(CBSynopsys, CheckState.Checked, CheckState.Unchecked)}),
                ('Count', {'label': Trans(85), 'state': if_else(CBCount, CheckState.Checked, CheckState.Unchecked)}),
                ('Notes', {'label': Trans(86), 'state': if_else(CBNotes, CheckState.Checked, CheckState.Unchecked)}),
                ('SerieStatus', {'label': Trans(87), 'state': if_else(CBStatus, CheckState.Checked, CheckState.Unchecked)}),
                ('Web', {'label': Trans(88), 'state': if_else(CBWeb, CheckState.Checked, CheckState.Unchecked)}),
                ('Genre', {'label': Trans(89), 'state': if_else(CBGenre, CheckState.Checked, CheckState.Unchecked)}),
                ('Cover', {'label': Trans(90), 'state': if_else(CBCover, CheckState.Checked, CheckState.Unchecked)}),
                ('ISBN', {'label': Trans(80), 'state': if_else(CBISBN, CheckState.Checked, CheckState.Unchecked)})
            ])
        self._CancelButton = System.Windows.Forms.Button()
        self._OKButton = System.Windows.Forms.Button()
        self._labelDBGLOGMAX = System.Windows.Forms.Label()
        self._labelRENLOGMAX = System.Windows.Forms.Label()
        self._labelVersion = System.Windows.Forms.Label()
        self._labelTIMEOUT = System.Windows.Forms.Label()
        self._labelTIMEOUTS = System.Windows.Forms.Label()
        self._labelArticles = System.Windows.Forms.Label()
        self._RENLOGMAX = System.Windows.Forms.TextBox()
        self._DBGLOGMAX = System.Windows.Forms.TextBox()
        self._DBGONOFF = System.Windows.Forms.CheckBox()
        self._SHOWDBGLOG = System.Windows.Forms.CheckBox()
        self._SHOWRENLOG = System.Windows.Forms.CheckBox()
        self._labelLanguage = System.Windows.Forms.Label()
        self._radioENG = System.Windows.Forms.RadioButton()
        self._radioFRE = System.Windows.Forms.RadioButton()
        self._PB1 = System.Windows.Forms.PictureBox()
        self._ButtonCheckNone = System.Windows.Forms.Button()
        self._ButtonCheckAll = System.Windows.Forms.Button()
        self._ARTICLES = System.Windows.Forms.TextBox()
        self._SUBPATT = System.Windows.Forms.TextBox()
        self._labelSUBPATT = System.Windows.Forms.Label()
        self._COUNTOF = System.Windows.Forms.CheckBox()
        self._COUNTFINIE = System.Windows.Forms.CheckBox()
        self._TITLEIT = System.Windows.Forms.CheckBox()
        self._FORMATARTICLES = System.Windows.Forms.CheckBox()
        self._PopUpEditionForm = System.Windows.Forms.CheckBox()
        self._SerieResumeEverywhere = System.Windows.Forms.CheckBox()
        self._AcceptGenericArtists = System.Windows.Forms.CheckBox()
        self._AlwaysChooseSerie = System.Windows.Forms.CheckBox()
        self._OneShotFormat = System.Windows.Forms.CheckBox()
        self._ShortWebLink = System.Windows.Forms.CheckBox()
        self._TIMEOUT = System.Windows.Forms.TextBox()
        self._TIMEOUTS = System.Windows.Forms.TextBox()
        self._TIMEPOPUP = System.Windows.Forms.TextBox()
        self._labelTIMEPOPUP = System.Windows.Forms.CheckBox()
        self._PadNumber = System.Windows.Forms.TextBox()
        self._labelPadNumber = System.Windows.Forms.Label()
        self._CBRescrape = System.Windows.Forms.CheckBox()
        self._labelChoice = System.Windows.Forms.GroupBox()
        self._radioChoiceSkip = System.Windows.Forms.RadioButton()
        self._radioChoiceUser = System.Windows.Forms.RadioButton()
        self._TabData.SuspendLayout()
        self._tabPage1.SuspendLayout()
        self._tabPage2.SuspendLayout()
        self._tabPage3.SuspendLayout()
        self._PB1.BeginInit()
        self.SuspendLayout()
        #
        # TabData
        #
        self._TabData.Controls.Add(self._tabPage1)
        self._TabData.Controls.Add(self._tabPage2)
        self._TabData.Controls.Add(self._tabPage3)
        self._TabData.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._TabData.Location = System.Drawing.Point(0, 0)
        self._TabData.Name = "TabData"
        self._TabData.SelectedIndex = 0
        self._TabData.Size = System.Drawing.Size(612, 362)
        self._TabData.TabIndex = 22
        #
        # tabPage1
        #
        self._tabPage1.Controls.Add(self._PB1)
        self._tabPage1.Controls.Add(self._labelLanguage)
        self._tabPage1.Controls.Add(self._radioENG)
        self._tabPage1.Controls.Add(self._radioFRE)
        self._tabPage1.Controls.Add(self._ARTICLES)
        self._tabPage1.Controls.Add(self._labelArticles)
        self._tabPage1.Controls.Add(self._TITLEIT)
        self._tabPage1.Controls.Add(self._FORMATARTICLES)
        self._tabPage1.Controls.Add(self._PopUpEditionForm)
        self._tabPage1.Controls.Add(self._AlwaysChooseSerie)
        self._tabPage1.Controls.Add(self._TIMEOUT)
        self._tabPage1.Controls.Add(self._TIMEOUTS)
        self._labelChoice.Controls.Add(self._TIMEPOPUP)
        self._labelChoice.Controls.Add(self._labelTIMEPOPUP)
        self._tabPage1.Controls.Add(self._labelTIMEOUT)
        self._tabPage1.Controls.Add(self._labelTIMEOUTS)
        self._tabPage1.Controls.Add(self._CBRescrape)
        self._tabPage1.Controls.Add(self._labelChoice)
        self._labelChoice.Controls.Add(self._radioChoiceSkip)
        self._labelChoice.Controls.Add(self._radioChoiceUser)
        self._tabPage1.Location = System.Drawing.Point(4, 22)
        self._tabPage1.Name = "tabPage1"
        self._tabPage1.Padding = System.Windows.Forms.Padding(3)
        self._tabPage1.Size = System.Drawing.Size(600, 350)
        self._tabPage1.TabIndex = 0
        self._tabPage1.Text = Trans(95)
        self._tabPage1.UseVisualStyleBackColor = True
        self._tabPage1.Tag = "Tab"
        #
        # tabPage2
        #
        self._tabPage2.Controls.Add(self._ButtonCheckNone)
        self._tabPage2.Controls.Add(self._ButtonCheckAll)
        self._tabPage2.Controls.Add(self._labelTags)
        self._tabPage2.Controls.Add(self._TBTags)
        self._tabPage2.Controls.Add(self._CBDefault)
        self._tabPage2.Controls.Add(self._OneShotFormat)
        self._tabPage2.Controls.Add(self._ScrapedDataCheckedListBox)
        self._tabPage2.Controls.Add(self._ShortWebLink)
        self._tabPage2.Controls.Add(self._COUNTOF)
        self._tabPage2.Controls.Add(self._COUNTFINIE)
        self._tabPage2.Controls.Add(self._SerieResumeEverywhere)
        self._tabPage2.Controls.Add(self._AcceptGenericArtists)
        self._tabPage2.Controls.Add(self._SUBPATT)
        self._tabPage2.Controls.Add(self._labelSUBPATT)
        self._tabPage2.Controls.Add(self._PadNumber)
        self._tabPage2.Controls.Add(self._labelPadNumber)
        self._tabPage2.Location = System.Drawing.Point(4, 22)
        self._tabPage2.Name = "tabPage2"
        self._tabPage2.Padding = System.Windows.Forms.Padding(3)
        self._tabPage2.Size = System.Drawing.Size(600, 350)
        self._tabPage2.TabIndex = 1
        self._tabPage2.Text = Trans(96)
        self._tabPage2.UseVisualStyleBackColor = True
        self._tabPage2.Tag = "Tab"
        #
        # tabPage3
        #
        self._tabPage3.Controls.Add(self._labelRENLOGMAX)
        self._tabPage3.Controls.Add(self._RENLOGMAX)
        self._tabPage3.Controls.Add(self._labelDBGLOGMAX)
        self._tabPage3.Controls.Add(self._DBGLOGMAX)
        self._tabPage3.Controls.Add(self._DBGONOFF)
        self._tabPage3.Controls.Add(self._SHOWDBGLOG)
        self._tabPage3.Controls.Add(self._SHOWRENLOG)
        self._tabPage3.Location = System.Drawing.Point(4, 22)
        self._tabPage3.Name = "tabPage3"
        self._tabPage3.Padding = System.Windows.Forms.Padding(3)
        self._tabPage3.Size = System.Drawing.Size(600, 350)
        self._tabPage3.TabIndex = 1
        self._tabPage3.Text = Trans(47)
        self._tabPage3.UseVisualStyleBackColor = True
        self._tabPage3.Tag = "Tab"
        #
        # ScrapedDataCheckedListBox
        #
        self._ScrapedDataCheckedListBox.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._ScrapedDataCheckedListBox.Location = System.Drawing.Point(8, 8)
        self._ScrapedDataCheckedListBox.Size = System.Drawing.Size(250, 300)
        self._ScrapedDataCheckedListBox.Name = "ScrapedDataCheckedListBox"
        self._ScrapedDataCheckedListBox.TabIndex = 10
        self._ScrapedDataCheckedListBox.CheckOnClick = True
        self._ScrapedDataCheckedListBox.ItemCheck += self.ScrapedDataCheckedListBox_CheckItem
        for key, item in self._scrapedData.items():
            self._ScrapedDataCheckedListBox.Items.Add(self._scrapedData[key]['label'], self._scrapedData[key]['state'])
        #
        # labelTags
        #
        self._labelTags.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._labelTags.Location = System.Drawing.Point(268, 176)
        self._labelTags.Name = "labelTags"
        self._labelTags.Size = System.Drawing.Size(120, 24)
        self._labelTags.TabIndex = 99
        self._labelTags.Text = Trans(91)
        self._labelTags.Tag = "Label"
        self._labelTags.TextAlign = System.Drawing.ContentAlignment.MiddleLeft
        #
        # TBTags
        #
        self._TBTags.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
        self._TBTags.Location = System.Drawing.Point(396, 180)
        self._TBTags.MaxLength = 255
        self._TBTags.Name = "TBTags"
        self._TBTags.Size = System.Drawing.Size(200, 20)
        self._TBTags.TabIndex = 40
        self._TBTags.Text = TBTags
        #
        # ShortWebLink
        #
        self._ShortWebLink.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._ShortWebLink.Location = System.Drawing.Point(268, 148)
        self._ShortWebLink.Name = "ShortWebLink"
        self._ShortWebLink.Size = System.Drawing.Size(350, 24)
        self._ShortWebLink.Text = Trans(48)
        self._ShortWebLink.UseVisualStyleBackColor = True
        self._ShortWebLink.CheckState = if_else(ShortWebLink, CheckState.Checked, CheckState.Unchecked)
        #
        # CBDefault
        #
        self._CBDefault.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._CBDefault.Location = System.Drawing.Point(268, 36)
        self._CBDefault.Name = "CBDefault"
        self._CBDefault.Size = System.Drawing.Size(350, 24)
        self._CBDefault.TabIndex = 38
        self._CBDefault.Text = Trans(136)
        self._CBDefault.UseVisualStyleBackColor = True
        self._CBDefault.CheckState = if_else(CBDefault, CheckState.Checked, CheckState.Unchecked)
        #
        # CancelButton
        #
        self._CancelButton.BackColor = System.Drawing.Color.Red
        self._CancelButton.DialogResult = System.Windows.Forms.DialogResult.Cancel
        self._CancelButton.Font = System.Drawing.Font("Microsoft Sans Serif", 9, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, 0)
        self._CancelButton.Location = System.Drawing.Point(520, 370)
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
        self._OKButton.Location = System.Drawing.Point(16, 370)
        self._OKButton.Name = "OKButton"
        self._OKButton.Size = System.Drawing.Size(75, 32)
        self._OKButton.TabIndex = 29
        self._OKButton.Text = Trans(92)
        self._OKButton.UseVisualStyleBackColor = False
        self._OKButton.Click += self.button_Click
        #
        # ButtonCheckNone
        #
        self._ButtonCheckNone.BackColor = System.Drawing.Color.FromArgb(255, 192, 128)
        self._ButtonCheckNone.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._ButtonCheckNone.Location = System.Drawing.Point(8, 300)
        self._ButtonCheckNone.Name = "ButtonCheckNone"
        self._ButtonCheckNone.Size = System.Drawing.Size(120, 28)
        self._ButtonCheckNone.TabIndex = 53
        self._ButtonCheckNone.Text = Trans(94)
        self._ButtonCheckNone.UseVisualStyleBackColor = False
        self._ButtonCheckNone.Tag = "Button"
        self._ButtonCheckNone.Click += self.button_Click
        #
        # ButtonCheckAll
        #
        self._ButtonCheckAll.BackColor = System.Drawing.Color.FromArgb(255, 192, 128)
        self._ButtonCheckAll.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._ButtonCheckAll.Location = System.Drawing.Point(132, 300)
        self._ButtonCheckAll.Name = "ButtonCheckAll"
        self._ButtonCheckAll.Size = System.Drawing.Size(120, 28)
        self._ButtonCheckAll.TabIndex = 52
        self._ButtonCheckAll.Text = Trans(117)
        self._ButtonCheckAll.UseVisualStyleBackColor = False
        self._ButtonCheckAll.Tag = "Button"
        self._ButtonCheckAll.Click += self.button_Click
        #
        # labelVersion
        #
        self._labelVersion.Font = System.Drawing.Font("Microsoft Sans Serif", 6.75, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
        self._labelVersion.ImageAlign = System.Drawing.ContentAlignment.BottomCenter
        self._labelVersion.Location = System.Drawing.Point(162, 380)
        self._labelVersion.Name = "labelVersion"
        self._labelVersion.Size = System.Drawing.Size(264, 16)
        self._labelVersion.TabIndex = 19
        self._labelVersion.Text = "Version " + VERSION + " (c) 2021 kiwi13 && maforget"
        self._labelVersion.TextAlign = System.Drawing.ContentAlignment.BottomCenter
        #
        # labelDBGLOGMAX
        #
        self._labelDBGLOGMAX.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._labelDBGLOGMAX.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
        self._labelDBGLOGMAX.Location = System.Drawing.Point(8, 124)
        self._labelDBGLOGMAX.Name = "labelDBGLOGMAX"
        self._labelDBGLOGMAX.Size = System.Drawing.Size(270, 21)
        self._labelDBGLOGMAX.TabIndex = 16
        self._labelDBGLOGMAX.Text = Trans(69)
        #
        # DBGLOGMAX
        #
        self._DBGLOGMAX.Location = System.Drawing.Point(300, 122)
        self._DBGLOGMAX.Name = "DBGLOGMAX"
        self._DBGLOGMAX.Size = System.Drawing.Size(40, 23)
        self._DBGLOGMAX.TabIndex = 4
        self._DBGLOGMAX.TextAlign = HorizontalAlignment.Center
        self._DBGLOGMAX.Text = "{:.2f}".format(float(DBGLOGMAX) / (1024 * 1024))
        #
        # labelArticles
        #
        self._labelArticles.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._labelArticles.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
        self._labelArticles.Location = System.Drawing.Point(8, 72)
        self._labelArticles.Name = "labelArticles"
        self._labelArticles.Size = System.Drawing.Size(110, 24)
        self._labelArticles.TabIndex = 18
        self._labelArticles.Text = Trans(109)
        #
        # ARTICLES
        #
        self._ARTICLES.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
        self._ARTICLES.Location = System.Drawing.Point(118, 70)
        self._ARTICLES.Name = "ARTICLES"
        self._ARTICLES.Size = System.Drawing.Size(200, 20)
        self._ARTICLES.TabIndex = 19
        self._ARTICLES.Text = ARTICLES
        #
        # label chaine à supp
        #
        self._labelSUBPATT.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._labelSUBPATT.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
        self._labelSUBPATT.Location = System.Drawing.Point(268, 208)
        self._labelSUBPATT.Name = "labelSubPatt"
        self._labelSUBPATT.Size = System.Drawing.Size(250, 24)
        self._labelSUBPATT.TabIndex = 100
        self._labelSUBPATT.Text = Trans(37)
        #
        # Pattern a supp
        #
        self._SUBPATT.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
        self._SUBPATT.Location = System.Drawing.Point(480, 206)
        self._SUBPATT.Name = "PATTSUB"
        self._SUBPATT.Size = System.Drawing.Size(116, 24)
        self._SUBPATT.TabIndex = 101
        self._SUBPATT.Text = SUBPATT
        #
        # CB time out popup
        #
        self._labelTIMEPOPUP.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._labelTIMEPOPUP.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
        self._labelTIMEPOPUP.Location = System.Drawing.Point(16, 52)
        self._labelTIMEPOPUP.Name = "labelTimePopup"
        self._labelTIMEPOPUP.Size = System.Drawing.Size(310, 23)
        self._labelTIMEPOPUP.TabIndex = 102
        self._labelTIMEPOPUP.UseVisualStyleBackColor = True
        self._labelTIMEPOPUP.Text = Trans(44)
        self._labelTIMEPOPUP.CheckState = if_else(AllowUserChoice == "2", CheckState.Checked, CheckState.Unchecked)
        #
        # time out popup
        #
        self._TIMEPOPUP.Location = System.Drawing.Point(330, 54)
        self._TIMEPOPUP.Name = "TIMEPOPUP"
        self._TIMEPOPUP.Size = System.Drawing.Size(40, 20)
        self._TIMEPOPUP.TabIndex = 103
        self._TIMEPOPUP.MaxLength = 3
        self._TIMEPOPUP.TextAlign = HorizontalAlignment.Center
        self._TIMEPOPUP.Text = TIMEPOPUP
        #
        # label pad number
        #
        self._labelPadNumber.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._labelPadNumber.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
        self._labelPadNumber.Location = System.Drawing.Point(268, 240)
        self._labelPadNumber.Name = "labelPadNumber"
        self._labelPadNumber.Size = System.Drawing.Size(300, 24)
        self._labelPadNumber.TabIndex = 104
        self._labelPadNumber.Text = Trans(148)
        #
        # pad number
        #
        self._PadNumber.Location = System.Drawing.Point(572, 238)
        self._PadNumber.Name = "PadNumber"
        self._PadNumber.Size = System.Drawing.Size(20, 24)
        self._PadNumber.TabIndex = 105
        self._PadNumber.MaxLength = 1
        self._PadNumber.TextAlign = HorizontalAlignment.Center
        self._PadNumber.Text = PadNumber
        #
        # labelRENLOGMAX
        #
        self._labelRENLOGMAX.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._labelRENLOGMAX.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
        self._labelRENLOGMAX.Location = System.Drawing.Point(8, 96)
        self._labelRENLOGMAX.Name = "labelRENLOGMAX"
        self._labelRENLOGMAX.Size = System.Drawing.Size(270, 21)
        self._labelRENLOGMAX.TabIndex = 20
        self._labelRENLOGMAX.Text = Trans(70)
        #
        # RENLOGMAX
        #
        self._RENLOGMAX.Location = System.Drawing.Point(300, 94)
        self._RENLOGMAX.Name = "RENLOGMAX"
        self._RENLOGMAX.Size = System.Drawing.Size(40, 23)
        self._RENLOGMAX.TabIndex = 5
        self._RENLOGMAX.TextAlign = HorizontalAlignment.Center
        self._RENLOGMAX.Text = "{:.2f}".format(float(RENLOGMAX) / (1024 * 1024))
        #
        # CBRescrape
        #
        self._CBRescrape.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._CBRescrape.Location = System.Drawing.Point(8, 310)
        self._CBRescrape.Name = "CBRescrape"
        self._CBRescrape.Size = System.Drawing.Size(400, 20)
        self._CBRescrape.TabIndex = 21
        self._CBRescrape.Text = Trans(137)
        self._CBRescrape.UseVisualStyleBackColor = True
        self._CBRescrape.CheckState = if_else(CBRescrape, CheckState.Checked, CheckState.Unchecked)
        #
        # COUNTOF
        #
        self._COUNTOF.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._COUNTOF.Location = System.Drawing.Point(268, 64)
        self._COUNTOF.Name = "COUNTOF"
        self._COUNTOF.Size = System.Drawing.Size(350, 20)
        self._COUNTOF.TabIndex = 22
        self._COUNTOF.Text = Trans(110)
        self._COUNTOF.UseVisualStyleBackColor = True
        self._COUNTOF.CheckState = if_else(COUNTOF, CheckState.Checked, CheckState.Unchecked)
        #
        # COUNTFINIE
        #
        self._COUNTFINIE.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._COUNTFINIE.Location = System.Drawing.Point(268, 92)
        self._COUNTFINIE.Name = "COUNTFINIE"
        self._COUNTFINIE.Size = System.Drawing.Size(350, 20)
        self._COUNTFINIE.TabIndex = 23
        self._COUNTFINIE.Text = Trans(126)
        self._COUNTFINIE.UseVisualStyleBackColor = True
        self._COUNTFINIE.CheckState = if_else(COUNTFINIE, CheckState.Checked, CheckState.Unchecked)
        #
        # TITLEIT
        #
        self._TITLEIT.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._TITLEIT.Location = System.Drawing.Point(8, 96)
        self._TITLEIT.Name = "TITLEIT"
        self._TITLEIT.Size = System.Drawing.Size(350, 24)
        self._TITLEIT.TabIndex = 24
        self._TITLEIT.Text = Trans(127)
        self._TITLEIT.UseVisualStyleBackColor = True
        self._TITLEIT.CheckState = if_else(TITLEIT, CheckState.Checked, CheckState.Unchecked)
        #
        # FORMATARTICLES
        #
        self._FORMATARTICLES.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._FORMATARTICLES.Location = System.Drawing.Point(8, 40)
        self._FORMATARTICLES.Name = "FORMATARTICLES"
        self._FORMATARTICLES.Size = System.Drawing.Size(320, 24)
        self._FORMATARTICLES.TabIndex = 25
        self._FORMATARTICLES.Text = Trans(144)
        self._FORMATARTICLES.UseVisualStyleBackColor = True
        self._FORMATARTICLES.CheckState = if_else(FORMATARTICLES, CheckState.Checked, CheckState.Unchecked)
        #
        # PopUpEditionForm
        #
        self._PopUpEditionForm.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._PopUpEditionForm.Location = System.Drawing.Point(8, 160)
        self._PopUpEditionForm.Name = "PopUpEditionForm"
        self._PopUpEditionForm.Size = System.Drawing.Size(320, 20)
        self._PopUpEditionForm.TabIndex = 26
        self._PopUpEditionForm.Text = Trans(147)
        self._PopUpEditionForm.UseVisualStyleBackColor = True
        self._PopUpEditionForm.CheckState = if_else(PopUpEditionForm, CheckState.Unchecked, CheckState.Checked)
        #
        # SerieResumeEverywhere
        #
        self._SerieResumeEverywhere.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._SerieResumeEverywhere.Location = System.Drawing.Point(268, 120)
        self._SerieResumeEverywhere.Name = "SerieResumeEverywhere"
        self._SerieResumeEverywhere.Size = System.Drawing.Size(350, 20)
        self._SerieResumeEverywhere.TabIndex = 27
        self._SerieResumeEverywhere.Text = Trans(149)
        self._SerieResumeEverywhere.UseVisualStyleBackColor = True
        self._SerieResumeEverywhere.CheckState = if_else(SerieResumeEverywhere, CheckState.Unchecked, CheckState.Checked)
        #
        # AcceptGenericArtists
        #
        self._AcceptGenericArtists.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._AcceptGenericArtists.Location = System.Drawing.Point(268, 268)
        self._AcceptGenericArtists.Name = "AcceptGenericArtists"
        self._AcceptGenericArtists.Size = System.Drawing.Size(350, 24)
        self._AcceptGenericArtists.Text = Trans(74)
        self._AcceptGenericArtists.UseVisualStyleBackColor = True
        self._AcceptGenericArtists.CheckState = if_else(AcceptGenericArtists, CheckState.Checked, CheckState.Unchecked)
        #
        # labelChoice (Decision in case of multiple choices when scraping)
        #
        self._labelChoice.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._labelChoice.Location = System.Drawing.Point(8, 192)
        self._labelChoice.Name = "labelChoice"
        self._labelChoice.Size = System.Drawing.Size(590, 82)
        self._labelChoice.Text = Trans(141)
        self._labelChoice.Tag = "Label"
        #
        # radioChoiceSkip (no user choice allowed)
        #
        self._radioChoiceSkip.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._radioChoiceSkip.Location = System.Drawing.Point(16, 20)
        self._radioChoiceSkip.Name = "radioChoiceSkip"
        self._radioChoiceSkip.Size = System.Drawing.Size(200, 24)
        self._radioChoiceSkip.Text = Trans(45)
        self._radioChoiceSkip.UseVisualStyleBackColor = True
        self._radioChoiceSkip.CheckedChanged += self.radioChoiceSkip_CheckedChanged
        #
        # radioChoiceUser (user choice allowed)
        #
        self._radioChoiceUser.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._radioChoiceUser.Location = System.Drawing.Point(220, 20)
        self._radioChoiceUser.Name = "radioChoiceUser"
        self._radioChoiceUser.Size = System.Drawing.Size(200, 24)
        self._radioChoiceUser.Text = Trans(46)
        self._radioChoiceUser.UseVisualStyleBackColor = True
        if AllowUserChoice:
            self._radioChoiceUser.Checked = True
            self._radioChoiceSkip.Checked = False
        else:
            self._radioChoiceSkip.Checked = True
            self._radioChoiceUser.Checked = False
        #
        # AlwaysChooseSerie
        #
        self._AlwaysChooseSerie.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._AlwaysChooseSerie.Location = System.Drawing.Point(8, 128)
        self._AlwaysChooseSerie.Name = "AlwaysChooseSerie"
        self._AlwaysChooseSerie.Size = System.Drawing.Size(320, 20)
        self._AlwaysChooseSerie.TabIndex = 28
        self._AlwaysChooseSerie.Text = Trans(151)
        self._AlwaysChooseSerie.UseVisualStyleBackColor = True
        self._AlwaysChooseSerie.CheckState = if_else(AlwaysChooseSerie, CheckState.Checked, CheckState.Unchecked)
        #
        # One Shot in Format
        #
        self._OneShotFormat.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._OneShotFormat.Location = System.Drawing.Point(268, 8)
        self._OneShotFormat.Name = "OneShotFormat"
        self._OneShotFormat.Size = System.Drawing.Size(350, 24)
        self._OneShotFormat.TabIndex = 29
        self._OneShotFormat.Text = Trans(150)
        self._OneShotFormat.UseVisualStyleBackColor = True
        self._OneShotFormat.CheckState = if_else(ONESHOTFORMAT, CheckState.Checked, CheckState.Unchecked)
        #
        # TIMEOUT Label
        #
        self._labelTIMEOUT.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._labelTIMEOUT.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
        self._labelTIMEOUT.Location = System.Drawing.Point(320, 282)
        self._labelTIMEOUT.Name = "labelTIMEOUT"
        self._labelTIMEOUT.Size = System.Drawing.Size(200, 23)
        self._labelTIMEOUT.TabIndex = 99
        self._labelTIMEOUT.Text = Trans(128)
        #
        # TIMEOUT
        #
        self._TIMEOUT.Location = System.Drawing.Point(550, 280)
        self._TIMEOUT.Name = "TIMEOUT"
        self._TIMEOUT.Size = System.Drawing.Size(40, 20)
        self._TIMEOUT.TabIndex = 29
        self._TIMEOUT.TextAlign = HorizontalAlignment.Center
        self._TIMEOUT.Text = TIMEOUT
        #
        # TIMEOUTS Label
        #
        self._labelTIMEOUTS.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._labelTIMEOUTS.ImageAlign = System.Drawing.ContentAlignment.MiddleLeft
        self._labelTIMEOUTS.Location = System.Drawing.Point(8, 282)
        self._labelTIMEOUTS.Name = "labelTIMEOUTS"
        self._labelTIMEOUTS.Size = System.Drawing.Size(260, 23)
        self._labelTIMEOUTS.TabIndex = 99
        self._labelTIMEOUTS.Text = Trans(129)
        #
        # TIMEOUTS
        #
        self._TIMEOUTS.Location = System.Drawing.Point(268, 280)
        self._TIMEOUTS.Name = "TIMEOUTS"
        self._TIMEOUTS.Size = System.Drawing.Size(40, 20)
        self._TIMEOUTS.TabIndex = 30
        self._TIMEOUTS.TextAlign = HorizontalAlignment.Center
        self._TIMEOUTS.MaxLength = 3
        self._TIMEOUTS.Text = TIMEOUTS
        #
        # DBGONOFF
        #
        self._DBGONOFF.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._DBGONOFF.Location = System.Drawing.Point(8, 36)
        self._DBGONOFF.Name = "DBGONOFF"
        self._DBGONOFF.Size = System.Drawing.Size(200, 20)
        self._DBGONOFF.TabIndex = 3
        self._DBGONOFF.Text = Trans(68)
        self._DBGONOFF.UseVisualStyleBackColor = True
        self._DBGONOFF.CheckState = if_else(DBGONOFF, CheckState.Checked, CheckState.Unchecked)
        #
        # SHOWDBGLOG
        #
        self._SHOWDBGLOG.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._SHOWDBGLOG.Location = System.Drawing.Point(8, 64)
        self._SHOWDBGLOG.Name = "SHOWDBGLOG"
        self._SHOWDBGLOG.Size = System.Drawing.Size(300, 20)
        self._SHOWDBGLOG.TabIndex = 2
        self._SHOWDBGLOG.Text = Trans(67)
        self._SHOWDBGLOG.UseVisualStyleBackColor = True
        self._SHOWDBGLOG.CheckState = if_else(SHOWDBGLOG, CheckState.Checked, CheckState.Unchecked)
        #
        # SHOWRENLOG
        #
        self._SHOWRENLOG.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._SHOWRENLOG.Location = System.Drawing.Point(8, 8)
        self._SHOWRENLOG.Name = "SHOWRENLOG"
        self._SHOWRENLOG.Size = System.Drawing.Size(300, 20)
        self._SHOWRENLOG.TabIndex = 1
        self._SHOWRENLOG.Text = Trans(66)
        self._SHOWRENLOG.UseVisualStyleBackColor = True
        self._SHOWRENLOG.CheckState = if_else(SHOWRENLOG, CheckState.Checked, CheckState.Unchecked)
        #
        # labelLanguage
        #
        self._labelLanguage.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._labelLanguage.Location = System.Drawing.Point(8, 8)
        self._labelLanguage.Name = "labelLanguage"
        self._labelLanguage.Size = System.Drawing.Size(120, 24)
        self._labelLanguage.TabIndex = 31
        self._labelLanguage.Text = Trans(112)
        self._labelLanguage.Tag = "Label"
        self._labelLanguage.TextAlign = System.Drawing.ContentAlignment.MiddleLeft
        #
        # radioENG
        #
        self._radioENG.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._radioENG.Location = System.Drawing.Point(128, 8)
        self._radioENG.Name = "radioENG"
        self._radioENG.Size = System.Drawing.Size(104, 24)
        self._radioENG.TabIndex = 6
        self._radioENG.Text = "English"
        self._radioENG.UseVisualStyleBackColor = True
        #
        # radioFRE
        #
        self._radioFRE.Checked = True
        self._radioFRE.Font = System.Drawing.Font("Microsoft Sans Serif", 8.25, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._radioFRE.Location = System.Drawing.Point(240, 8)
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
        self._PB1.Location = System.Drawing.Point(520, 4)
        self._PB1.Name = "PB1"
        self._PB1.Size = System.Drawing.Size(72, 64)
        self._PB1.TabIndex = 35
        self._PB1.TabStop = False
        self._PB1.SizeMode = PictureBoxSizeMode.Zoom

        #
        # ConfigForm
        #
        self.ClientSize = System.Drawing.Size(612, 412)
        self.Controls.Add(self._TabData)
        self.Controls.Add(self._labelVersion)
        self.Controls.Add(self._CancelButton)
        self.Controls.Add(self._OKButton)

        self._TabData.ResumeLayout(False)
        self._tabPage1.ResumeLayout(False)
        self._tabPage1.PerformLayout()
        self._tabPage2.ResumeLayout(False)
        self._tabPage2.PerformLayout()
        self._tabPage3.ResumeLayout(False)
        self._tabPage3.PerformLayout()
        self.AcceptButton = self._OKButton
        self.CancelButton = self._CancelButton
        self.KeyPreview = True

        # Adjust DPI scaling in this form
        HighDpiHelper.AdjustControlImagesDpiScale(self)

        self.ResumeLayout(False)


    def button_Click(self, sender, e):

        global SHOWRENLOG, SHOWDBGLOG, DBGONOFF, DBGLOGMAX, RENLOGMAX, LANGENFR, aWord, ONESHOTFORMAT
        global TBTags, CBCover, CBStatus, CBGenre, CBNotes, CBWeb, CBCount, CBSynopsys, CBImprint, CBLetterer, CBInker, CBPrinted, CBRating, CBISBN, CBDefault, CBRescrape, AllowUserChoice, PopUpEditionForm, SerieResumeEverywhere, AcceptGenericArtists
        global CBLanguage, CBEditor, CBFormat, CBColorist, CBPenciller, CBWriter, CBTitle, CBSeries, ARTICLES, SUBPATT, COUNTOF, CBCouverture, COUNTFINIE, TITLEIT, TIMEOUT, TIMEOUTS, TIMEPOPUP, FORMATARTICLES, PadNumber, AlwaysChooseSerie, ShortWebLink

        if sender.Name.CompareTo(self._OKButton.Name) == 0:
            SHOWRENLOG = if_else(self._SHOWRENLOG.CheckState == CheckState.Checked, True, False)
            SHOWDBGLOG = if_else(self._SHOWDBGLOG.CheckState == CheckState.Checked, True, False)
            DBGONOFF = if_else(self._DBGONOFF.CheckState == CheckState.Checked, True, False)
            DBGLOGMAX = int(float(self._DBGLOGMAX.Text)*1024*1024)
            RENLOGMAX = int(float(self._RENLOGMAX.Text)*1024*1024)
            LANGENFR = if_else(self._radioENG.Checked,"EN", "FR")
            TBTags = self._TBTags.Text
            ShortWebLink = if_else(self._ShortWebLink.CheckState == CheckState.Checked, True, False)
            CBCover = if_else(self._scrapedData['Cover']['state'] == CheckState.Checked, True, False)
            CBCouverture = if_else(self._scrapedData['CoverArtist']['state'] == CheckState.Checked, True, False)
            CBStatus = if_else(self._scrapedData['SerieStatus']['state'] == CheckState.Checked, True, False)
            CBGenre = if_else(self._scrapedData['Genre']['state'] == CheckState.Checked, True, False)
            CBNotes = if_else(self._scrapedData['Notes']['state'] == CheckState.Checked, True, False)
            CBWeb = if_else(self._scrapedData['Web']['state'] == CheckState.Checked, True, False)
            CBCount = if_else(self._scrapedData['Count']['state'] == CheckState.Checked, True, False)
            CBSynopsys = if_else(self._scrapedData['Synopsys']['state'] == CheckState.Checked, True, False)
            CBImprint = if_else(self._scrapedData['Imprint']['state'] == CheckState.Checked, True, False)
            CBLetterer = if_else(self._scrapedData['Letterer']['state'] == CheckState.Checked, True, False)
            CBInker = if_else(self._scrapedData['Inker']['state'] == CheckState.Checked, True, False)
            CBPrinted = if_else(self._scrapedData['Printed']['state'] == CheckState.Checked, True, False)
            CBRating = if_else(self._scrapedData['Rating']['state'] == CheckState.Checked, True, False)
            CBISBN = if_else(self._scrapedData['ISBN']['state'] == CheckState.Checked, True, False)
            CBLanguage = if_else(self._scrapedData['Language']['state'] == CheckState.Checked, True, False)
            CBEditor = if_else(self._scrapedData['Publisher']['state'] == CheckState.Checked, True, False)
            CBFormat = if_else(self._scrapedData['Format']['state'] == CheckState.Checked, if_else(self._OneShotFormat.CheckState == CheckState.Checked, False, True), False)
            CBColorist = if_else(self._scrapedData['Colorist']['state'] == CheckState.Checked, True, False)
            CBPenciller = if_else(self._scrapedData['Penciller']['state'] == CheckState.Checked, True, False)
            CBWriter = if_else(self._scrapedData['Writer']['state'] == CheckState.Checked, True, False)
            CBTitle = if_else(self._scrapedData['Title']['state'] == CheckState.Checked, True, False)
            CBSeries = if_else(self._scrapedData['Series']['state'] == CheckState.Checked, True, False)
            CBDefault = if_else(self._CBDefault.CheckState == CheckState.Checked, True, False)
            CBRescrape = if_else(self._CBRescrape.CheckState == CheckState.Checked, True, False)
            AllowUserChoice = if_else(self._radioChoiceUser.Checked, True, False)
            if self._radioChoiceUser.Checked:
                if self._labelTIMEPOPUP.CheckState == CheckState.Checked:
                    AllowUserChoice = "2"
                else:
                    AllowUserChoice = True
            else:
                AllowUserChoice = False

            ARTICLES = self._ARTICLES.Text
            SUBPATT = self._SUBPATT.Text
            COUNTOF = if_else(self._COUNTOF.CheckState == CheckState.Checked, True, False)
            COUNTFINIE = if_else(self._COUNTFINIE.CheckState == CheckState.Checked, True, False)
            TITLEIT = if_else(self._TITLEIT.CheckState == CheckState.Checked, True, False)
            FORMATARTICLES = if_else(self._FORMATARTICLES.CheckState == CheckState.Checked, True, False)
            ONESHOTFORMAT = if_else(self._OneShotFormat.CheckState == CheckState.Checked, True, False)
            PopUpEditionForm = if_else(self._PopUpEditionForm.CheckState == CheckState.Checked, False, True)
            SerieResumeEverywhere = if_else(self._SerieResumeEverywhere.CheckState == CheckState.Checked, False, True)
            AlwaysChooseSerie = if_else(self._AlwaysChooseSerie.CheckState == CheckState.Checked, True, False)
            AcceptGenericArtists = if_else(self._AcceptGenericArtists.CheckState == CheckState.Checked, True, False)

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

        elif sender.Name.CompareTo(self._ButtonCheckNone.Name) == 0:
            for index in range(self._ScrapedDataCheckedListBox.Items.Count):
                self._ScrapedDataCheckedListBox.SetItemCheckState(index, CheckState.Unchecked)
        elif sender.Name.CompareTo(self._ButtonCheckAll.Name) == 0:
            for index in range(self._ScrapedDataCheckedListBox.Items.Count):
                self._ScrapedDataCheckedListBox.SetItemCheckState(index, CheckState.Checked)

    def ScrapedDataCheckedListBox_CheckItem(self, sender, e):
        self._scrapedData[self._scrapedData.keys()[e.Index]]['state'] = e.NewValue

    def radioChoiceSkip_CheckedChanged(self, sender, e):
        if sender.Checked == True:
            self._TIMEPOPUP.Enabled = False
            self._labelTIMEPOPUP.Enabled = False
        else:
            self._TIMEPOPUP.Enabled = True
            self._labelTIMEPOPUP.Enabled = True



def Translate():

    global aWord

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

    tText = aWord[nWord-1]

    return tText

def cleanARTICLES(s):

    ns = re.search(r"^(" + ARTICLES.replace(',','|') + ")\s*(?<=['\s])((?=[^/\r\n\(:\,!]*(?:\s[-–]\s))[^-–\r\n]*|.[^/\r\n\(:\,!]*)", s, re.IGNORECASE)
    if ns:
        s = ns.group(2).strip()
    ns2 = re.search(r"^[#]*(.(?=[^/\r\n\(:\,!]*(?:\s[-–]\s))[^-–\r\n]*|.[^/\r\n\(:\,!]*)", s, re.IGNORECASE)
    if ns2:
        s = ns2.group(1).strip()

    return s

def formatARTICLES(s):

    ns = re.sub(r"^(" + ARTICLES.replace(',','|') + ")\s*(?<=['\s])((?=[^(]*(?:\s[-–:]\s))[^-–:\r\n]*|[^\(/\r\n]*)(?![-–:/\(])\s*([^\r\n]*)", r"\2 (\1) \3", s, re.IGNORECASE)
    if ns:
        s = Capitalize(ns.strip())

    return s

def titlize(s, formatArticles = False):

    if formatArticles and FORMATARTICLES:
        s = formatARTICLES(s)

    if TITLEIT:
        NewString = ""
        Ucase = False
        for i in range(len(s.strip())):
            if Ucase or i == 0:
                NewString += s[i:i + 1].upper()
            else:
                NewString += s[i:i + 1]

            if not (s[i:i + 1]).isalnum() and s[i:i + 2].lower() != "'s":
                Ucase = True
            else:
                Ucase = False
        test = s.title()
        return NewString
    else:
        return s

def Capitalize(s):

    ns = s[0:1].upper() + s[1:]
    return ns

class FormType():
    SERIE = 1
    ALBUM = 2
    EDITION = 3

class SeriesForm(BaseForm):

    def __init__(self, serie, listItems, formType = FormType.SERIE):

        self.List = listItems
        self.list_filtered_index = []
        self.formType = formType
        self.InitializeComponent(serie)

    def InitializeComponent(self, serie):

        global TimerExpired

        self.Load += self.MainForm_Load
        self._ListSeries = System.Windows.Forms.ListBox()
        self._CancelButton = System.Windows.Forms.Button()
        self._OKButton = System.Windows.Forms.Button()
        self._ClearButton = System.Windows.Forms.Button()

        if AllowUserChoice == "2":
            TimerExpired = False
            self._timer1 = System.Windows.Forms.Timer()
            self._timer1.Interval = int(TIMEPOPUP) * 1000
            self._timer1.Enabled = True
            self._timer1.Tick += self.CloseForm

        # 
        # ListSeries
        # 
        self._ListSeries.Font = System.Drawing.Font("Microsoft Sans Serif", 9, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._ListSeries.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right | System.Windows.Forms.AnchorStyles.Bottom
        self._ListSeries.FormattingEnabled = True
        self._ListSeries.ItemHeight = 15
        self._ListSeries.Location = System.Drawing.Point(8, 30)
        self._ListSeries.Name = "ListSeries"
        self._ListSeries.Size = System.Drawing.Size(374, 258)
        self._ListSeries.Sorted = True
        self._ListSeries.TabIndex = 3
        self._ListSeries.DoubleClick += self.DoubleClick
        # 
        # CancelButton
        # 
        self._CancelButton.BackColor = System.Drawing.Color.Red
        self._CancelButton.Anchor = System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right
        self._CancelButton.DialogResult = System.Windows.Forms.DialogResult.Cancel
        self._CancelButton.Font = System.Drawing.Font("Microsoft Sans Serif", 9, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, 0)
        self._CancelButton.Location = System.Drawing.Point(301, 290)
        self._CancelButton.Name = "CancelButton"
        self._CancelButton.Size = System.Drawing.Size(75, 30)
        self._CancelButton.TabIndex = 4
        self._CancelButton.Text = Trans(93)
        self._CancelButton.UseVisualStyleBackColor = False
        self._CancelButton.DialogResult = DialogResult.Cancel
        # 
        # OKButton
        # 
        self._OKButton.BackColor = System.Drawing.Color.FromArgb(128, 255, 128)
        self._OKButton.Anchor = System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left
        self._OKButton.DialogResult = System.Windows.Forms.DialogResult.OK
        self._OKButton.Font = System.Drawing.Font("Microsoft Sans Serif", 9, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, 0)
        self._OKButton.ForeColor = System.Drawing.Color.Black
        self._OKButton.Location = System.Drawing.Point(8, 290)
        self._OKButton.Name = "OKButton"
        self._OKButton.Size = System.Drawing.Size(75, 30)
        self._OKButton.TabIndex = 5
        self._OKButton.Text = Trans(92)
        self._OKButton.UseVisualStyleBackColor = False
        self._OKButton.Click += self.button_Click
        self._OKButton.DialogResult = DialogResult.OK
        
        self._Filter = System.Windows.Forms.TextBox()
        self._Filter.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left | System.Windows.Forms.AnchorStyles.Right
        self._Filter.Font = System.Drawing.Font("Microsoft Sans Serif", 9, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, 0)
        self._Filter.Location = System.Drawing.Point(30, 8)
        self._Filter.Name = "Filter"
        self._Filter.Size = System.Drawing.Size(352, 20)
        self._Filter.TabIndex = 1
        self._Filter.Text = ""
        self._Filter.TextChanged += self.onTextChanged
        self._Filter.WordWrap = False
        # 
        # ClearButton
        # 
        self._ClearButton.Anchor = System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left
        self._ClearButton.Font = System.Drawing.Font("Microsoft Sans Serif", 8, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, 0)
        self._ClearButton.Location = System.Drawing.Point(8, 8)
        self._ClearButton.Name = "ClearButton"
        self._ClearButton.Size = System.Drawing.Size(20, 20)
        self._ClearButton.TabIndex = 2
        self._ClearButton.Text = "X"
        self._ClearButton.UseVisualStyleBackColor = True
        self._ClearButton.Click += self.ClearButton_Click
            
        self.ClientSize = System.Drawing.Size(390, 325)
        self.MinimumSize = System.Drawing.Size(180, 180)
        self.Controls.Add(self._Filter)
        self.Controls.Add(self._ListSeries)
        self.Controls.Add(self._OKButton)
        self.Controls.Add(self._CancelButton)
        self.Controls.Add(self._ClearButton)
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

        self.fillList()

        # Adjust DPI scaling in this form
        HighDpiHelper.AdjustControlImagesDpiScale(self)

        if AllowUserChoice == "2":
            self._timer1.Start()

    def fillList(self, ):
        self._ListSeries.Items.Clear()
        del self.list_filtered_index[:]
        filter = self._Filter.Text.strip().lower()
        for x in range(len(self.List)):
            if self.List[x]:
                title = ""
                if self.formType == FormType.EDITION: 
                    title = self.List[x][1].Title
                else: 
                    title = self.List[x][1]
                
                display = "(" + self.List[x][2] + ") - " + title + if_else(self.List[x][0], "   (", "") + self.List[x][0] + if_else(self.List[x][0], ")", "")
                if filter and filter not in display.lower():
                    continue
                self._ListSeries.Items.Add(display)
                self.list_filtered_index.append(x)

    def onTextChanged(self, sender, e):
        self.fillList()

    def button_Click(self, sender, e):

        global NewLink, NewSeries

        sel = self.list_filtered_index[self._ListSeries.SelectedIndex]
        if sender.Name.CompareTo(self._OKButton.Name) == 0 and self.List[sel][1]:
            NewLink = self.List[sel][0]
            NewSeries = self.List[sel][1]
            self.Hide()

    def ClearButton_Click(self, sender, e):
        self._Filter.Text = ""
        self.fillList()
        self._Filter.Focus()

    def CloseForm(self, sender, e):

        global TimerExpired

        debuglog("Timer Expired")
        TimerExpired = True
        self._timer1.Stop()
        self.Hide()

    def DoubleClick(self, sender, e):

        global NewLink, NewSeries

        title = ""
        link = ""
        sel = self.list_filtered_index[self._ListSeries.SelectedIndex]
        if self.formType == FormType.SERIE: 
            title = self.List[sel][1]
            link = "https://www.bedetheque.com/" + self.List[sel][0]
        elif self.formType == FormType.EDITION: 
            title = self.List[sel][1].Title + " (" + self.List[sel][1].A + ")"
            link = self.List[sel][1].URL
        elif self.formType == FormType.ALBUM:
            title = self.List[sel][1]
            link = self.List[sel][0]

        if title:
            NewLink = link
            NewSeries = self.List[sel][1]
            Start(NewLink)

    def MainForm_Load(self, sender, e):
        self.Left += 365

#@Key Bedetheque2
#@Hook ConfigScript
#@Name Configurer BD2
def ConfigureBD2Quick():

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

    global LinkBD2, Numero, AlbumNumNum, dlgNumber, dlgName, nRenamed, nIgnored, dlgAltNumber, Shadow1, Shadow2, RenameSeries

    RetAlb = False

    if not cLink:
        if not LoadSetting():
            return False

    RenameSeries = False

    if not books:
        Result = MessageBox.Show(ComicRack.MainWindow, Trans(1),Trans(2), MessageBoxButtons.OK, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button1)
        return False

    LinkBD2 = ""

    if not cLink:
        nRenamed = 0
        nIgnored = 0
    cError = False
    MyBooks = []

    try:

        if books:
            if cLink:
                MyBooks.append(book)
            else:
                MyBooks = books
                f = ProgressBarDialog(books.Count)
                if books.Count > 1:
                    f.Show(ComicRack.MainWindow)

            log_BD(Trans(7) + str(MyBooks.Count) +  Trans(8), "\n============ " + str(datetime.now().strftime("%A %d %B %Y %H:%M:%S")) + " ===========", 0)

            for MyBook in MyBooks:

                if cLink:
                    Numero = ""
                    serieUrl = cLink
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
                    mPos = re.search(r'([.,\\/-])', dlgNumber)

                    if not isnumeric(dlgNumber):
                        albumNum = dlgNumber
                        AlbumNumNum = False
                    elif isnumeric(dlgNumber) and not re.search(r'[.,\\/-]', dlgNumber):
                        dlgNumber = str(int(dlgNumber))
                        albumNum = str(int(dlgNumber))
                        AlbumNumNum = True
                    elif mPos:
                        nPos = mPos.start(1)
                        albumNum = dlgNumber[:nPos]
                        dlgAltNumber = dlgNumber[nPos:]
                        dlgNumber = albumNum
                        AlbumNumNum = True

                    f.Update(dlgName + if_else(dlgNumber != "", " - " + dlgNumber, " ") + if_else(dlgAltNumber == '', '', ' AltNo.[' + dlgAltNumber + ']') + " - " + titlize(MyBook.Title), 1, MyBook)
                    f.Refresh()

                    scrape = DirectScrape()
                    result = scrape.ShowDialog()

                    if result == DialogResult.Cancel or (LinkBD2 == ""):
                        return False

                    if LinkBD2:
                        serieUrl = GetFullURL(LinkBD2)

                if LinkBD2:
                    debuglog(Trans(104), LinkBD2)

                RetVal = serieUrl
                if "/serie-" in serieUrl or '/revue-' in serieUrl: 
                    serieUrl = serieUrl if "__10000.html" in serieUrl or '/revue-' in serieUrl else serieUrl.lower().replace(".html", u'__10000.html')                   
                    RetVal = parseSerieInfo(MyBook, serieUrl, True)

                if RetVal and not '/revue-' in serieUrl:
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
            debuglog(Trans(15) +"\n")
            log_BD(Trans(15), "", 1)
            return False

    except:
        cError = debuglogOnError()
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

class DirectScrape(BaseForm):

    def __init__(self):

        self.InitializeComponent()

    def InitializeComponent(self):

        try:
            # BD
            self._LinkBD2 = System.Windows.Forms.TextBox()
            self._labelPasteLink = System.Windows.Forms.Label()
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
            # labelPasteLink
            #
            self._labelPasteLink.Font = System.Drawing.Font("Microsoft Sans Serif", 11.25, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, 0)
            self._labelPasteLink.Location = System.Drawing.Point(104, 8)
            self._labelPasteLink.Name = "labelPasteLink"
            self._labelPasteLink.Size = System.Drawing.Size(450, 20)
            self._labelPasteLink.TabIndex = 99
            self._labelPasteLink.Text = Trans(102)
            self._labelPasteLink.TextAlign = System.Drawing.ContentAlignment.MiddleCenter
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
            self.Controls.Add(self._labelPasteLink)
            self.Controls.Add(self._LinkBD2)
            #
            self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
            self.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen
            self.Name = "ScrapeLink"
            self.Text = Trans(103)
            pIcon = (__file__[:-len('BedethequeScraper2.py')] + "BD2.ico")
            self.Icon = System.Drawing.Icon(pIcon)
            self.KeyPreview = True

            # Adjust DPI scaling in this form
            HighDpiHelper.AdjustControlImagesDpiScale(self)

            self.ResumeLayout(False)
            self.PerformLayout()

        except:
            cError = debuglogOnError()

    def button_Click(self, sender, e):

        if sender.Name.CompareTo(self._OKScrape.Name) == 0:

            global LinkBD2

            if not self._LinkBD2.Text:
                self.Hide()
                LinkBD2 = ""
            else:
                LinkBD2 = self._LinkBD2.Text

class HighDpiHelper:
    @staticmethod
    def AdjustControlImagesDpiScale(container):

        dpiScale = HighDpiHelper.GetDpiScale(container)
        if HighDpiHelper.CloseToOne(dpiScale):
            return

        # DPI Scaling Aware
        container.AutoScaleDimensions = System.Drawing.Size(96, 96)
        container.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Dpi

        HighDpiHelper.AdjustControlImagesDpiScale_Internal(container.Controls, dpiScale)

    @staticmethod
    def AdjustButtonImageDpiScale(button, dpiScale):
        image = button.Image
        if image is None:
            return

        button.Image = HighDpiHelper.ScaleImage(image, dpiScale)

    @staticmethod
    def AdjustControlImagesDpiScale_Internal(controls, dpiScale):
        for control in controls:
            if isinstance(control, ButtonBase):
                HighDpiHelper.AdjustButtonImageDpiScale(control, dpiScale)
            elif isinstance(control, PictureBox):
                HighDpiHelper.AdjustPictureBoxDpiScale(control, dpiScale)

            HighDpiHelper.AdjustControlImagesDpiScale_Internal(control.Controls, dpiScale)

    @staticmethod
    def AdjustPictureBoxDpiScale(pictureBox, dpiScale):
        image = pictureBox.Image
        if image is None:
            return

        if pictureBox.SizeMode == PictureBoxSizeMode.CenterImage:
            pictureBox.Image = HighDpiHelper.ScaleImage(image, dpiScale)

    @staticmethod
    def CloseToOne(dpiScale):
        return Math.Abs(dpiScale - 1) < 0.001

    @staticmethod
    def GetDpiScale(control):
        def calculateDpiScale():
            try:
                with control.CreateGraphics() as graphics:
                    return graphics.DpiX / 96.0
            except:
                cError = debuglogOnError()
                log_BD("   [error]", cError, 1)
                return 1.0

        return calculateDpiScale()

    @staticmethod
    def ScaleImage(image, dpiScale):
        if HighDpiHelper.CloseToOne(dpiScale):
            return

        newSize = HighDpiHelper.ScaleSize(image.Size, dpiScale)
        newBitmap = Bitmap(newSize.Width, newSize.Height)

        with Graphics.FromImage(newBitmap) as g:
            interpolationMode = System.Drawing.Drawing2D.InterpolationMode.HighQualityBicubic
            if dpiScale >= 2.0:
                interpolationMode = System.Drawing.Drawing2D.InterpolationMode.NearestNeighbor

            g.InterpolationMode = interpolationMode
            g.DrawImage(image, Rectangle(Point.Empty, newSize))

        return newBitmap

    @staticmethod
    def ScaleSize(size, scale):
        return Size(int(size.Width * scale), int(size.Height * scale))
