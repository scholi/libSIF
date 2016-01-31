#!/usr/bin/env python
# *-* coding: utf-8 *-*

import sys
import os
from PyQt4 import QtCore, QtGui
from calc import Ui_MainWindow

from SIF import SIF

import numpy as np

class BGcorrGUI(QtGui.QMainWindow):
	def __init__(self, filename=None, arg=None, parent=None):
		QtGui.QMainWindow.__init__(self, parent)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)
		self.lsig=None
		self.lbg=None
		self.dfsig=None
		self.dfbg=None
		self.filters=[]
		for x in os.listdir(os.path.expanduser("~/filters")):
			if x[-4:]==".npz":
				print("Found a filter:",x)
				self.filters.append(x)
				n=self.ui.filters.rowCount()+1
				self.ui.filters.setRowCount(n)
				self.ui.filters.setItem(n-1,0,QtGui.QTableWidgetItem(x[:-4]))
				self.ui.filters.setItem(n-1,1,QtGui.QTableWidgetItem(x))
				self.ui.filterL.addItem(x[:-4])
				self.ui.filterS.addItem(x[:-4])
		# Signals / Slots
		self.connect(self.ui.LL,QtCore.SIGNAL('clicked()'),self.loadL)
		self.connect(self.ui.LLBG,QtCore.SIGNAL('clicked()'),self.loadLBG)
		self.connect(self.ui.LS,QtCore.SIGNAL('clicked()'),self.loadDF)
		self.connect(self.ui.LSBG,QtCore.SIGNAL('clicked()'),self.loadDFBG)
		self.connect(self.ui.BTsave,QtCore.SIGNAL('clicked()'),self.save)
	def loadL(self, fname=None):
		if fname==None:
			fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '.')
		if os.path.exists(fname):
			print("Loading \"%s\" as Light reference"%(fname))
			self.lsig=SIF(fname)
			rfn=bytes.decode(self.lsig.sig.Filter['Name'])
			efn=rfn.replace(".","").replace(" ","")
			for i in range(self.ui.filters.rowCount()):
				if self.ui.filters.item(i,0).text()==efn:
					self.ui.filterL.setCurrentIndex(i+1)
					break
			self.ui.LL.setText("OK")
			path=os.path.split(str(fname))
			pbg=path[0]+"/BG_"+path[1]
			print("Probe file %s"%(pbg))
			if os.path.exists(pbg):
				print("Found!")
				self.loadLBG(pbg)

	def loadLBG(self, fname=None):
		if fname==None:
			fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '.')
		if os.path.exists(fname):
			print("Loading \"%s\" as Light reference Background"%(fname))
			self.lbg=SIF(fname)
			self.ui.LLBG.setText("OK")
	def loadDF(self, fname=None):
		if fname==None:
			fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '.')
		if os.path.exists(fname):
			self.fsig=fname
			print("Loading \"%s\" Structure"%(fname))
			self.dfsig=SIF(fname)
			self.ui.LS.setText("OK")
			path=os.path.split(str(fname))
			pbg=path[0]+"/BG_"+path[1]
			if os.path.exists(pbg):
				self.loadDFBG(pbg)
	def loadDFBG(self, fname=None):
		if fname==None:
			fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '.')
		if os.path.exists(fname):
			print("Loading \"%s\" Structure Background"%(fname))
			self.dfbg=SIF(fname)
			self.ui.LSBG.setText("OK")
	def save(self):
		Light=self.lsig.sig.imageData-self.lbg.sig.imageData
		Signal=self.dfsig.sig.imageData-self.dfbg.sig.imageData
		ifl=self.ui.filterL.currentIndex()
		if ifl>0:
			# FIX
			path=os.path.expanduser("~/filters/%s"%(self.ui.filters.item(ifl-1,1).text()))
			print(path)
			fL=np.load(path)["sig"]
			Light/=fL#.sig.imageData
		ifs=self.ui.filterS.currentIndex()
		if ifs>0:
			path=os.path.expanduser("~/filters/%s"%(self.ui.filters.item(ifs-1,1).text()))
			fS=np.load(path)["sig"]
			Signal/=fS#.sig.imageData

		fname = QtGui.QFileDialog.getSaveFileName(self, 'Save file', self.fsig[:-4]+".npz")
		if self.dfsig.sig.CenterWavelength>0 and (self.dfsig.sig.poly==np.array([0,1,0,0])).all():
			self.error(101,"Polynome seems to be wrong...")
			if self.dfsig.sig.CenterWavelength==699.98:
				self.info("Fortunately we can correct it")
				self.dfsig.sig.poly=np.array([  4.14274195e+02,   5.58106514e-01,   9.53039510e-07,-2.19417467e-09])
		np.savez(str(fname),sig=Signal/Light,cw=self.dfsig.sig.CenterWavelength,poly=self.dfsig.sig.poly)
	def error(self, errid, errtxt):
		sys.stderr.write("\033[31;1mError #%i:\033[0m %s\n"%(errid,errtxt))

	def info(self,txt):
		sys.stdout.write("\033[32;1mInfo:\033[0m %s\n"%(txt))

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	arg=None
	if len(sys.argv)>2:
		arg=sys.argv[2]
	if len(sys.argv)>1:
		myapp = BGcorrGUI(sys.argv[1],arg)
	else:	
		myapp = BGcorrGUI(None,arg)
	myapp.show()
	sys.exit(app.exec_())
