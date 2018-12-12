#!/usr/bin/env python3

#for Youtube-dl
from __future__ import unicode_literals
import youtube_dl

#import _thread
import threading
import time 

import gi
gi.require_version('Gtk', '3.0') 
from gi.repository import GLib, Gtk, GObject

import os,sys, signal, shutil, subprocess
import gettext,locale


class MainWindow (Gtk.Builder):
	
	win=None
	status=None
	progressBar=None
	entryUrl=None
	btDownload=None
	btAbort=None
	Continue=True
	chkOnlyAudio=None
	OnlyAudio=False
	destFolder=None
	tdwn=None
	outFilename=None
	
	#AboutDialog
	aboutDialog=None
	
	
	def my_hook(d):
		print (d['status'])
		MainWindow.outFilename=d['filename']
		
		if d['status'] == 'finished':
			print('Scaricamento flusso terminato, codifico ...')
			if ('total_bytes' in d and 'downloaded_bytes' in d):
				GLib.idle_add(MainWindow.updateStatus, _("Download finished"),d['downloaded_bytes'],d['total_bytes'])
			
		
		if d['status'] == 'downloading':
			if ('total_bytes' in d and 'downloaded_bytes' in d):
				print('Scaricamento in corso (%s) di %s...' % (d['downloaded_bytes'] , d['total_bytes']))
				msg= _("Download in progress ")+d['filename']
				GLib.idle_add(MainWindow.updateStatus, msg,d['downloaded_bytes'],d['total_bytes'])
			else:
				GLib.idle_add(MainWindow.pulsateBar, _("Scaricamento in corso")+ " ("+str(d['downloaded_bytes'])+" bytes)...")	
		
		
	
	def download(self,url):
		
		class ytLogger(object):
			def debug(self, msg):
				pass

			def warning(self, msg):
				print(msg)
				GLib.idle_add(MainWindow.updateStatus, msg,"Err","Err")

			def error(self, msg):
				print(msg)
				GLib.idle_add(MainWindow.updateStatus, msg,"Err","Err")
		
				
		filetmpl="%(title)s.%(ext)s"
		output_template=os.path.join(MainWindow.destFolder,filetmpl)
		
		if (MainWindow.OnlyAudio==False):
			ydl_opts = {'logger': ytLogger(),'nocheckcertificate': True,'nooverwrites': True , 'outtmpl': output_template , 'progress_hooks': [MainWindow.my_hook]}
		else:
			ydl_opts = {
					'logger': ytLogger(),
					'nocheckcertificate': True ,
					'nooverwrites': True ,
					'outtmpl': output_template ,
					'format': 'bestaudio',
					'extract-audio': True , 
					'audio-format': 'mp3',      
					'noplaylist' : True,        
					'progress_hooks': [MainWindow.my_hook],  
				}
		
		with youtube_dl.YoutubeDL(ydl_opts) as ydl:
			ydl.download([url])
			
		if (MainWindow.OnlyAudio==True):
			GLib.idle_add(MainWindow.updateStatus, _("Saving in progress..."),100,100)
			GLib.idle_add(MainWindow.status.set_text,_("I code the audio file..."))
			
			if (sys.platform == "win32"):
				ffmpeg="ffmpeg.exe"	
			else:
				ffmpeg = shutil.which("ffmpeg")
						
			if (ffmpeg!=None):
				#ffmpeg -i input.mp4 -vn -ab 128k outputfile.mp3
				try:
					cmd=ffmpeg+" -y -i \""+MainWindow.outFilename+"\" -vn -ab 128k \""+os.path.splitext(MainWindow.outFilename)[0]+".mp3\""
					print("Cmd: %s" % cmd)
					os.system(cmd)
					os.remove(MainWindow.outFilename)
				except subprocess.CalledProcessError as e:
					print (e.output)
					GLib.idle_add(MainWindow.updateStatus, _("Something went wrong with the encoding of the file: ")+e.output,100,100)	
			
		GLib.idle_add(MainWindow.updateStatus, _("Done."),100,100)
		GLib.idle_add(MainWindow.setWindowSensitive,True)
	
	
	def updateStatus(msg,downloaded,total):
		if (downloaded=="Err"): 
			MainWindow.progressBar.set_fraction(0.0)
			MainWindow.status.set_text(msg)
			MainWindow.setWindowSensitive(True)
			return	
		
		if(total>0 and downloaded>0):
			MainWindow.status.set_text(msg)
			fraction=downloaded/total
			MainWindow.progressBar.set_fraction(fraction)	
	
	def pulsateBar(msg):		
		MainWindow.progressBar.pulse()
		MainWindow.status.set_text(msg)
		
		
		
	def setWindowSensitive(flag):	
		if (flag==True):
			MainWindow.entryUrl.set_sensitive(True)
			MainWindow.btDownload.set_sensitive(True)
			MainWindow.chkOnlyAudio.set_sensitive(True)
			MainWindow.btAbort.set_sensitive(False)
		else:
			MainWindow.entryUrl.set_sensitive(False)
			MainWindow.btDownload.set_sensitive(False)
			MainWindow.chkOnlyAudio.set_sensitive(False)
			MainWindow.btAbort.set_sensitive(True)
	
	def on_button_clicked(self,entryUrl):
		MainWindow.Continue=True
		print ('Inizio download...%s' % entryUrl.get_text())
		MainWindow.progressBar.set_fraction(0.0)
		MainWindow.status.set_text(_("Download started..."))
		GLib.idle_add(MainWindow.setWindowSensitive,False)
		
		url=entryUrl.get_text()
		MainWindow.tdwn = threading.Thread(target=MainWindow.download, args=(self,url,))
		MainWindow.tdwn.daemon = True
		MainWindow.tdwn.start()
	
	def on_abort_clicked(self):
		MainWindow.Continue=False
		MainWindow.quit(self,MainWindow.win)
 
	def on_toggled_chkOnlyAudio(self):
		if (MainWindow.OnlyAudio==False): 
			MainWindow.OnlyAudio=True
		else:
			MainWindow.OnlyAudio=False
	
	def folderSet(self,folderChoser):
		MainWindow.destFolder=folderChoser.get_filename()
		print("Dest folder: "+MainWindow.destFolder)
		
	def quit(self,win):
		print ("Exit!")
		Gtk.main_quit(win)		
		
	def get_download_folder():
		downloads_dir = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD)
		return downloads_dir
	
	def show_about_dialog(self,dialog):
		dialog.present()
	
	def hide_about_dialog(self,dialog):
		dialog.hide()	
 
	def __init__(self):
		self = Gtk.Builder()
		self.set_translation_domain("pobtube")
		self.add_from_file("builder.ui")
		
		if getattr(sys, 'frozen', False):
			# frozen
			iconfile= os.path.join(os.path.dirname(sys.executable),"icons","play.png")
		else:
			# unfrozen
			iconfile=os.path.join(os.path.dirname(os.path.realpath(__file__)),"icons","play.png")
				
		
		#Main Window
		MainWindow.win = self.get_object("win0")
		MainWindow.win.set_icon_from_file("icons/play.png")
		MainWindow.win.set_title(_("Download a video from the web"))
		MainWindow.entryUrl = self.get_object("entryUrl")
		MainWindow.chkOnlyAudio = self.get_object("chkOnlyAudio")
		MainWindow.chkOnlyAudio.set_label(_("only audio"))
		MainWindow.btDownload = self.get_object("btDownload")
		MainWindow.btAbort = self.get_object("btAbort")
		MainWindow.btAbort.set_sensitive(False)
		MainWindow.progressBar= self.get_object("progressBar")
		MainWindow.status= self.get_object("status")
		folderChoser=self.get_object("folderChoser")
		mainLabel=self.get_object("mainLabel")
		mainLabel.set_text(_("Paste the link to the video here:"))
		#About Dialog
		MainWindow.aboutDialog=self.get_object("aboutDialog")
		btCloseAboutDialog=self.get_object("btCloseAboutDialog")
		btCloseAboutDialog.connect("clicked", MainWindow.hide_about_dialog, MainWindow.aboutDialog )
		
		#menu
		mnuQuit= self.get_object("mnuQuit")
		mnuAboutDialog= self.get_object("mnuAboutDialog")
		mnuAboutDialog.connect("activate",MainWindow.show_about_dialog, MainWindow.aboutDialog)
		mnuQuit.connect("activate",MainWindow.quit, MainWindow.win)
			
		#Default download folder
		MainWindow.destFolder=MainWindow.get_download_folder()
		folderChoser.set_filename(MainWindow.get_download_folder())
		
		MainWindow.win.show_all()
 
		MainWindow.win.connect("delete-event", MainWindow.quit)
		MainWindow.btDownload.connect("clicked", MainWindow.on_button_clicked,MainWindow.entryUrl)
		MainWindow.btAbort.connect("clicked", MainWindow.on_abort_clicked)
		MainWindow.chkOnlyAudio.connect("toggled",MainWindow.on_toggled_chkOnlyAudio)
		folderChoser.connect("file-set",MainWindow.folderSet,folderChoser )
		
		
#Gettext
try:
	current_locale, encoding = locale.getdefaultlocale()
	locale_path = 'languages'
	language = gettext.translation ('pobtube', locale_path, [current_locale] )
	language.install()
except:
	print("Locale not foud")
	_ = gettext.gettext		

 
print (_("Loading, please wait...")) 
if (sys.platform == "win32"):
		
	if getattr(sys, 'frozen', False):
		# frozen
		splash= os.path.join(os.path.dirname(sys.executable),"splash-pobtube.exe")
	else:
		# unfrozen
		splash=os.path.join(os.path.dirname(os.path.realpath(__file__)),"splash-pobtube.exe")

	process = subprocess.Popen(splash, shell=True)
	



myWindow =  MainWindow()

if (sys.platform == "win32"): 
	try:
		#subprocess.check_output("TASKKILL /F /IM splash-pobtube.exe", shell=True)
		subprocess.Popen("TASKKILL /F /PID {pid} /T".format(pid=process.pid), shell=False)
	except subprocess.CalledProcessError as e:
		print (e.output)

Gtk.main()