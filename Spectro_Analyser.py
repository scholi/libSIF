#!/usr/bin/python2
#-------------------------------------------------------------------------------
# Name:		GUI for SPectral Analysis
# Purpose:
#
# Author:	  scholi
#
# Created:	 06.05.2012
# Copyright:   (c) scholi 2012
# Licence:	 GPL
#-------------------------------------------------------------------------------

import sys
import os
from PyQt4 import QtCore, QtGui
from Spectro import Ui_MainWindow

import numpy as np

import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.mlab as mlab

class SpectroGUI(QtGui.QMainWindow):
	def __init__(self, filename=None, arg=None, parent=None, debug=False):
		QtGui.QMainWindow.__init__(self, parent)
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		self.debug=debug

		self.dpi = 100
		self.fig = Figure((5.0, 4.0), dpi=self.dpi)
		self.canvas = FigureCanvas(self.fig)
		self.canvas.setParent(self.ui.widget)

		# Since we have only one plot, we can use add_axes
		# instead of add_subplot, but then the subplot
		# configuration tool in the navigation toolbar wouldn't
		# work.
		#
		self.axes = self.fig.add_subplot(411)
		self.raw = self.fig.add_subplot(412)
		self.plt = self.fig.add_subplot(413)
		self.ref = self.fig.add_subplot(414)
#		self.vari = self.fig.add_subplot(515)


		# Bind the 'pick' event for clicking on one of the bars
		#
		self.canvas.mpl_connect('pick_event', self.on_pick)

		# Create the navigation toolbar, tied to the canvas
		#
		self.mpl_toolbar = NavigationToolbar(self.canvas, self.ui.widget)

		vbox = QtGui.QVBoxLayout()
		vbox.addWidget(self.canvas)
		vbox.addWidget(self.mpl_toolbar)
		self.ui.widget.setLayout(vbox)

		# Signals/Slots
		self.connect(self.ui.actionOpen, QtCore.SIGNAL('triggered()'), self.loadSpec)
		self.connect(self.ui.sigTop, QtCore.SIGNAL('valueChanged(int)'), self.on_draw)
		self.connect(self.ui.Smin, QtCore.SIGNAL('valueChanged(int)'), self.on_draw)
		self.connect(self.ui.Smax, QtCore.SIGNAL('valueChanged(int)'), self.on_draw)
		self.connect(self.ui.sigBottom, QtCore.SIGNAL('valueChanged(int)'), self.on_draw)
		self.connect(self.ui.ref1Top, QtCore.SIGNAL('valueChanged(int)'), self.on_draw)
		self.connect(self.ui.ref1Bottom, QtCore.SIGNAL('valueChanged(int)'), self.on_draw)
		self.connect(self.ui.rawsigStdDev, QtCore.SIGNAL('stateChanged(int)'), self.on_draw)
		self.connect(self.ui.sigStdDev, QtCore.SIGNAL('stateChanged(int)'), self.on_draw)
		self.connect(self.ui.refStdDev, QtCore.SIGNAL('stateChanged(int)'), self.on_draw)
		self.connect(self.ui.NumSignals, QtCore.SIGNAL('valueChanged(int)'), self.on_draw)
		self.connect(self.ui.SigSpacing, QtCore.SIGNAL('valueChanged(double)'), self.on_draw)
		self.connect(self.ui.actionClose, QtCore.SIGNAL('triggered()'), self.closeEvent)
		self.connect(self.ui.AlignTop, QtCore.SIGNAL('clicked()'), self.AlignRefTop)
		self.connect(self.ui.AlignBottom, QtCore.SIGNAL('clicked()'), self.AlignRefBottom)
		self.connect(self.ui.BTFindAntenna, QtCore.SIGNAL('clicked()'), self.FindAntennas)
		self.connect(self, QtCore.SIGNAL('triggered()'), self.closeEvent)
		self.connect(self.ui.multisig, QtCore.SIGNAL("toggled(bool)"), self.on_draw)
		self.connect(self.ui.MultiRef, QtCore.SIGNAL("toggled(bool)"), self.on_draw)

		if filename!=None:
			self.loadSpec(filename)
	def FindAntennas(self):
		self.ref.clear()
		s=self.data["sig"][:,512]
		s=s/max(s)
		d=s[1:]-s[:-1]
		d=d/max(d)
		i=np.where(d>0.2)[0]
		l=0
		ids=[]
		for x in range(len(i)-2):
			if i[x+1]==i[l]+1:
				l=x
			else:
				ids.append(i[x])
				l=x+1
		if(i[-1]<230): ids.append(i[-1])
	
		self.ui.sigTop.setValue(ids[-1]-1)
		self.ui.sigBottom.setValue(ids[-1]+3)
		self.ui.multisig.setCheckState(2)
		self.ui.NumSignals.setValue(10)
		self.ui.SigSpacing.setValue(12.6)
		self.ui.MultiRef.setCheckState(2)
		self.AlignRefBottom()
		self.ref.plot(s)
		self.ref.plot(d)
		self.canvas.draw()
		
	def AlignRefBottom(self):
		self.ui.ref1Top.setSliderPosition(self.ui.sigBottom.value()+1)
		self.ui.ref1Bottom.setSliderPosition(2*self.ui.sigBottom.value()-self.ui.sigTop.value()+1)
	def AlignRefTop(self):
		self.ui.ref1Bottom.setSliderPosition(self.ui.sigTop.value())
		self.ui.ref1Top.setSliderPosition(2*self.ui.sigTop.value()-self.ui.sigBottom.value())

	def loadSpec(self, filename=None):
		if filename==None:
			fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file', ".", "NumpyArray (*.npz)")
		else:
			fname=filename
		if not os.path.exists(fname):
			 QtGui.QMessageBox.warning(self, "Warning", "The file \"%s\" cannot be accessed!"%(fname))
		self.data=np.load(str(fname))
		mmin=0
		mmax=1000
		self.ui.Smin.setRange(mmin,mmax)
		self.ui.Smax.setRange(mmin,mmax)
		self.ui.Smax.setSliderPosition(int(mmax)+1)
		self.ui.Smin.setSliderPosition(int(mmin))
		self.ds=self.data['sig'].shape[::-1]

		# Creating Wavelength Axis
		x=np.arange(0,self.ds[0])
		self.wavelength=np.polyval(self.data["poly"][::-1],x)

		self.fname=fname
		mmin=np.min(self.data["sig"])
		mmax=np.max(self.data["sig"])
		md=mmax-mmin
		dd=(self.ui.Smin.maximum()-self.ui.Smin.minimum())
		self.lmin=self.ui.Smin.value()
		self.lmax=self.ui.Smax.value()
		cmin=mmin+(md*self.lmin)/dd
		cmax=mmin+(md*self.lmax)/dd
	
		self.axes.imshow(self.data["sig"],vmin=cmin,vmax=cmax)

		self.lup = [mpl.lines.Line2D([0,self.ds[0]],[0,0],color="red")]
		self.ldown = [mpl.lines.Line2D([0,self.ds[0]],[self.ds[1],self.ds[1]],color="red")]
		self.axes.add_line(self.lup[0])
		self.axes.add_line(self.ldown[0])

		self.lref1up = [mpl.lines.Line2D([0,self.ds[0]],[0,0],color="green")]
		self.lref1down = [mpl.lines.Line2D([0,self.ds[0]],[0,0],color="green")]
		self.lref2up = mpl.lines.Line2D([0,self.ds[0]],[0,0],color="green")
		self.lref2down = mpl.lines.Line2D([0,self.ds[0]],[0,0],color="green")
		self.axes.add_line(self.lref1up[0])
		self.axes.add_line(self.lref1down[0])
		self.axes.add_line(self.lref2up)
		self.axes.add_line(self.lref2down)

		self.ui.sigBottom.setRange(1,self.ds[1])
		self.ui.sigTop.setRange(1,self.ds[1])
		self.ui.ref1Bottom.setRange(1,self.ds[1])
		self.ui.ref1Top.setRange(1,self.ds[1])
		self.ui.ref2Top.setRange(1,self.ds[1])
		self.ui.ref2Bottom.setRange(1,self.ds[1])
		trd={
			"SignalUp":self.ui.sigTop,
			"SignalDown":self.ui.sigBottom,
			"Ref1Up":self.ui.ref1Top,
			"Ref1Down":self.ui.ref1Bottom,
			"Ref2Up":self.ui.ref2Top,
			"Ref2Down":self.ui.ref2Bottom,
			"NumSignals":self.ui.NumSignals,
			"RangeUp":self.ui.Smax,
			"RangeDown":self.ui.Smin
			}
			
		if os.path.exists(fname[:-4]+".txt"):
			ff=open(fname[:-4]+".txt","r")
			inf={}
			for x in ff.readlines():
				c=x.split()
				inf[c[0]]=c[1]
			for x in trd:
				if x in inf:
					trd[x].setValue(int(inf[x]))
			if "SignalSpacing" in inf:
				self.ui.multisig.setCheckState(QtCore.Qt.Checked)
				self.ui.SigSpacing.setValue(float(inf["SignalSpacing"]))
			if "MultiRef" in inf:
				self.ui.MultiRef.setCheckState(int(inf["MultiRef"]))

	def on_pick(self):
		pass
	def closeEvent(self, event=None):
		if self.debug: print("Closing...")
		yup = self.ui.sigTop.value()
		ydown = self.ui.sigBottom.value()
		yrefup= self.ui.ref1Top.value()
		yrefdown = self.ui.ref1Bottom.value()
		yref2up = self.ui.ref2Top.value()
		yref2down = self.ui.ref2Bottom.value()
		n=self.ui.NumSignals.value()
		rup=self.ui.Smax.value()
		rdown=self.ui.Smin.value()
		mref=self.ui.MultiRef.checkState()
		if n==0: n=1
		dh=self.ui.SigSpacing.value()
		fname=str(self.fname)
		if os.path.exists(fname):
			# Write Infos
			ff=open(fname[:-4]+".txt","w")	
			ff.write("SignalUp\t%i\nSignalDown\t%i\nRef1Up\t%i\nRef1Down\t%i\nRef2Up\t%i\nRef2Down\t%i\nNumSignals\t%i\nSignalSpacing\t%f\nRangeUp\t%i\nRangeDown\t%i\nMultiRef\t%i"%(yup,ydown,yrefup,yrefdown,yref2up,yref2down,n,dh,rup,rdown,mref))
			ff.close()
			# Write Data
			# prepare Data
			ff=open(fname[:-4]+".dat","w")
			ffr=open(fname[:-4]+"_raw.dat","w")	
			if self.debug: print("Saving...")
			if yrefup!=yrefdown:
				ref=[np.mean(self.data["sig"][yrefup:yrefdown],0)]
				if mref:
					for i in range(1,n):
						ref.append(np.mean(self.data["sig"][yrefup-i*dh:yrefdown-i*dh],0))
			w=self.wavelength
			data=[np.mean(self.data["sig"][yup-i*dh:ydown-i*dh],0) for i in range(n)]
			rawdata=[np.mean(self.data["sig"][yup-i*dh:ydown-i*dh],0) for i in range(n)]
			ff.write("# wavelength[nm]")
			ffr.write("# wavelength[nm]")
			for i in range(n):
				ff.write("\tIntensity_antenna_%i[-]"%(i))
				ffr.write("\tIntensity_antenna_%i[-]"%(i))
			if yrefup!=yrefdown:
				if mref:
					for i in range(n):
						ffr.write("\tReference%i[-]"%(i))
				else:
					ffr.write("\tReference[-]")
			ffr.write("\n")
			if yrefup!=yrefdown:
				for i in range(n):
					if mref:
						data[i]=data[i]-ref[i]
					else:
						data[i]=data[i]-ref[0]
			for x in range(len(rawdata[0])):
				ff.write("%f"%(w[x]))
				ffr.write("%f"%(w[x]))
				for i in range(n):
					ff.write("\t%f"%(data[i][x]))
					ffr.write("\t%f"%(rawdata[i][x]))
				if yrefup!=yrefdown:
					if mref:
						for i in range(n):
							ffr.write("\t%f"%(ref[i][x]))
					else:
						ffr.write("\t%f"%(ref[0][x]))
				ff.write("\n")
				ffr.write("\n")
			ff.close()
			ffr.close()
		self.destroy()
		sys.exit(0)

	def on_draw(self):
		yup = self.ui.sigTop.value()
		ydown = self.ui.sigBottom.value()
		yrefup= self.ui.ref1Top.value()
		yrefdown = self.ui.ref1Bottom.value()
		yref2up = self.ui.ref2Top.value()
		yref2down = self.ui.ref2Bottom.value()
		n=self.ui.NumSignals.value()
		if n==0: n=1
		dh=self.ui.SigSpacing.value()
		
		if self.ui.Smin.value()!=self.lmin or self.ui.Smax.value()!=self.lmax:
			mmin=np.min(self.data["sig"])
			mmax=np.max(self.data["sig"])
			md=mmax-mmin
			dd=(self.ui.Smin.maximum()-self.ui.Smin.minimum())
			self.lmin=self.ui.Smin.value()
			self.lmax=self.ui.Smax.value()
			cmin=mmin+(md*self.lmin)/dd
			cmax=mmin+(md*self.lmax)/dd
			self.axes.imshow(self.data["sig"],vmin=cmin,vmax=cmax)

		self.lup[0].set_data([0,self.ds[0]],[yup,yup])
		self.ldown[0].set_data([0,self.ds[0]],[ydown,ydown])
		self.lref1up[0].set_data([0,self.ds[0]],[yrefup,yrefup])
		self.lref1down[0].set_data([0,self.ds[0]],[yrefdown,yrefdown])
		self.lref2up.set_data([0,self.ds[0]],[yref2up,yref2up])
		self.lref2down.set_data([0,self.ds[0]],[yref2down,yref2down])
			

		self.plt.clear()
		self.ref.clear()
		self.raw.clear()
		self.ref.clear()

	# Signals
		data=[np.mean(self.data["sig"][yup:ydown],0)]
		self.raw.plot(self.wavelength,data[0],color="black")
		if self.ui.multisig.checkState()==QtCore.Qt.Checked:
			if len(self.lup)>n:
				for i in range(n+1,len(self.lup)):
					del self.lup[i]
					del self.ldown[i]
				self.lup=self.lup[:n]
				self.ldown=self.ldown[:n]
			if n>1:
				if len(self.lup)>n:
					for i in range(n,len(self.lup)):
						del self.lup[i]
						del self.ldown[i]
				if len(self.lup)<n:
					for i in range(len(self.lup),n):
						self.lup.append(mpl.lines.Line2D([0,self.ds[0]],[0,0],color="red"))
						self.ldown.append(mpl.lines.Line2D([0,self.ds[0]],[0,0],color="red"))
						self.axes.add_line(self.lup[i])
						self.axes.add_line(self.ldown[i])
				for i in range(1,n):
					data.append(np.mean(self.data["sig"][int(yup-dh*i):int(ydown-dh*i)],0))
					self.raw.plot(self.wavelength,data[i])
					self.lup[i].set_data([0,self.ds[0]],[int(yup-dh*i),int(yup-dh*i)])
					self.ldown[i].set_data([0,self.ds[0]],[int(ydown-dh*i),int(ydown-dh*i)])
	
		# Sig StdDev
		DS2=0
		drs=np.sqrt(np.var(self.data["sig"][yup:ydown],0))
		if self.ui.rawsigStdDev.checkState()==QtCore.Qt.Checked:
				vx,vy = mlab.poly_between(self.wavelength,data[0]-drs,data[0]+drs)
				self.raw.fill(vx,vy,color="red")
				DS2+=(drs)**2

		# Reference Signal
		if yrefup!=yrefdown:
			ref=[np.mean(self.data["sig"][yrefup:yrefdown],0)]
			self.ref.plot(self.wavelength,ref[0],color="black")
			# Std Dev
			delta=np.sqrt(np.var(self.data["sig"][yrefup:yrefdown],0))
			if self.ui.refStdDev.checkState()==QtCore.Qt.Checked:
				vx,vy = mlab.poly_between(self.wavelength,ref[0]-delta,ref[0]+delta)
				self.ref.fill(vx,vy,color="blue")
				DS2+=(delta)**2
				DS=np.sqrt(DS2)
				data[0]=data[0]-ref[0]
				self.plt.plot(self.wavelength,data[0],color="black")
			if self.ui.multisig.checkState()==QtCore.Qt.Checked:
				if n>1:
					if self.ui.MultiRef.checkState()==QtCore.Qt.Checked:
						if len(self.lref1up)>n:
							for i in range(n,len(self.lref1up)):
								del self.lref1up[i]
								del self.lref1down[i]
						if len(self.lref1up)<n:
							for i in range(len(self.lref1up),n):
								self.lref1up.append(mpl.lines.Line2D([0,self.ds[0]],[0,0],color="green"))
								self.lref1down.append(mpl.lines.Line2D([0,self.ds[0]],[0,0],color="green"))
								self.axes.add_line(self.lref1up[i])
								self.axes.add_line(self.lref1down[i])
								if self.debug: print "++",i
						for i in range(1,n):
							ref.append(np.mean(self.data["sig"][int(yrefup-dh*i):int(yrefdown-dh*i)],0))
							data[i]=data[i]-ref[i]
							self.lref1up[i].set_data([0,self.ds[0]],[int(yrefup-dh*i),int(yrefup-dh*i)])
							self.lref1down[i].set_data([0,self.ds[0]],[int(yrefdown-dh*i),int(yrefdown-dh*i)])
					else:
						if len(self.lref1up)>1:
							for i in range(len(self.lref1up)-1,0,-1):
								if self.debug: print "-",i
								self.lref1up[i].set_data([0,self.ds[0]],[0,0])
								self.lref1down[i].set_data([0,self.ds[0]],[0,0])
								del self.lref1up[i]
								del self.lref1down[i]
						for i in range(1,n):
							data[i]=data[i]-ref[0]
					for i in range(1,n):
						self.plt.plot(self.wavelength,data[i])
			if self.ui.sigStdDev.checkState()==QtCore.Qt.Checked:
					vx,vy = mlab.poly_between(self.wavelength,data[0]-DS,data[0]+DS)
					self.plt.fill(vx,vy)
		self.canvas.draw()

if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	arg=None
	if len(sys.argv)>2:
		arg=sys.argv[2]
	if len(sys.argv)>1:
		myapp = SpectroGUI(sys.argv[1],arg)
	else:	
		myapp = SpectroGUI(None,arg)
	myapp.show()
	sys.exit(app.exec_())
