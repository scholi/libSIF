#!/usr/bin/python2
#*-* coding: utf-8 *-*

import sys
import array
import struct
import numpy as np
import matplotlib.pyplot as plt
from optparse import OptionParser


def uformat(val,index=0):
	pexp="kMGTPE"
	nexp="mμnpfa"
	if val>=1000:
		return uformat(val/1000.0,index+1)
	elif val<=0.001:
		return uformat(val*1000.0,index-1)
	if index<0:
		return (val,nexp[-1-index])
	elif index>0:
		return (val,pexp[index-1])
	return (val,"")	

class SIF:
	def __init__(self,filename):
		try:
			f=open(filename,"rb")
		except:
			print("Fail to open file %s"%(filename))
			sys.exit(1)
		o = f.readline().strip()
		if o!= b'Andor Technology Multi-Channel File':
			print("Invalid File Format!")
			f.close()
			sys.exit(1)
		f.readline()
		self.sig=self.SImage(f)
		if self.sig._next==1:
			self.bck=self.SImage(f)
			if self.bck._next==2:
				self.ref=self.SImage(f)
			else:
				self.ref=None
		else:
			self.ref=None
			self.bck=None
		f.close()
	def get(self, s):
		if s=='s-b':
			return self.sig.imageData-self.bck.imageData
		elif s=='sig':
			return self.sig.imageData
		elif s=='bck':
			return self.bck.imageData

	def show(self, s):
		if s=='s-b':
			if self.bck!=None:
				print("Signal\n======\n")
				self.sig.show()
				print("\n\nBackground\n======\n")
				self.bck.show()
				if self.sig.size['w']!=self.bck.size['w'] or self.sig.size['h']!=self.bck.size['h']:
					print("Plotting abortion. Signal and Background don't have the same size")
				else:
					data=self.sig.imageData-self.bck.imageData
					if self.sig.size['h']==1:
						plt.plot(self.sig.imageData[0],color="red")
						plt.plot(self.bck.imageData[0],color="green")
						plt.plot(data[0],color="blue")
					else:
						plt.imshow(data)
					plt.show()
		elif s=='sig':
			print("Plot signal")
			self.sig.show()
			self.sig.plot()
		elif s=='bck':
			if self.bck!=None:
				self.bck.show()
				self.bck.plot()
		elif s=='ref':
			if self.ref!=None:
				self.ref.show()
				self.ref.plot()

	class SImage:
		def __init__(self, f):
			dbg=True
			o=f.readline().split()
			if dbg: print(o)
			self.temp=float(o[5])
			if dbg: print("Temp: %f"%(self.temp))
			self.ExpTime=float(o[12])
			if dbg: print("Exp. Time: %f"%(self.ExpTime))
			self.CycleTime=float(o[13])
			if dbg: print("Cycle Time: %f"%(self.CycleTime))
			self.AccCycleTime=float(o[14])
			if dbg: print("Accumulated Cycle Time: %f"%(self.AccCycleTime))
			self.AccCycles=int(o[15])
			if dbg: print("Accumulated Cycles: %i"%(self.AccCycles))
			self.CameraType=f.readline().split()[0]
			if dbg: print("Camera Type: %s"%(self.CameraType))
			self.CameraSize=[int(x) for x in f.readline().split()]
			if dbg: print("Camera Size: %ix%i"%(self.CameraSize[0],self.CameraSize[1]))
			self.FileName=f.readline().strip()
			if dbg: print("FileName: %s"%(self.FileName))
			f.readline()
			f.read(2049)
			f.readline()
			o=f.readline().split()
			if dbg: print(o)
			self.CenterWavelength=float(o[3])
			if dbg: print("Central Wavelenmgth: %f"%(self.CenterWavelength))
			self.GratingBlaze=float(o[7])
			if dbg: print("Grating Blaze: %f"%(self.GratingBlaze))
			self.GratingG=int(o[6])
			if dbg: print("Grating Grade: %f"%(self.GratingG))
			self.ShutterTime=[float(x) for x in o[4:6]]
			if dbg: print("Shutter Time: %f,%f"%tuple(self.ShutterTime))
			f.readline()
			oo=f.readline()
			o=oo.split()
			di=sum([len(x)+1 for x in o[:5]])
			if dbg: print("Filter Name's length: %i"%(int(o[4])))
			self.Filter={'Name':oo[di:di+int(o[4])],'Number':int(o[3])}

			if dbg: print("Filter #%i: %s"%(self.Filter['Number'],self.Filter['Name']))
			o=f.readline().split()
			self.SpectrometerType=o[1]
			if dbg: print("SpectroType: %s"%(o[1]))
			while True:
				o=f.readline()
				if dbg: print("Skip:",o)
				if o[:5]=='65539':
					break
			o=f.readline().split()
			self.poly=[float(x) for x in o]
			if dbg: print("Polynome:",self.poly)
			for i in range(5):
				o=f.readline()
				if dbg: print("Skip:",o)


			self.frameAxis = f.read(int(f.readline()))
			self.dataType = f.read(int(f.readline()))
			self.ImageAxis = f.read(int(f.readline()))
			oo=[int(x) for x in f.readline().split()]
			self.imageArea=[[oo[1], oo[4], oo[6]], [oo[3],oo[2], oo[5]]]
			o=[int(x) for x in f.readline().split()]
			self.frameArea=[[o[1], o[4]], [o[3],o[2]]]
			self.frameBins=[o[6],o[5]]
			w=(1.0+(self.frameArea[1][0]-self.frameArea[0][0]))/self.frameBins[0]
			h=(1.0+(self.frameArea[1][1]-self.frameArea[0][1]))/self.frameBins[1]
			s=int(w*h)
			z=1+(self.imageArea[1][2] - self.imageArea[0][2])
			self.size={'h':h,'w':w,'z':z,'s':s}
			if s!=oo[8] or oo[8]*z != oo[7]:
				f.close()
				print("Image Size Dimension Error in Header")
				sys.exit(1)
			for i in range(z):
				f.readline()
			self.TimeStamp=struct.unpack("h",f.read(2))
			o=array.array('f')
			o.fromfile(f, s*z)
			self.imageData=np.array(o.tolist()).reshape(h,w)
			f.read(int(f.readline()))
			o=f.readline().split()
			self._next=int(o[0])
		
		def show(self):
			print("Temperature = %.02f°C"%(self.temp))
			print("Exposition Time = %.02f%ss"%uformat(self.ExpTime))
			print("Cycle Time = %.02f%ss"%uformat(self.CycleTime))
			print("Accumulated Cycle Time = %.02f%ss"%uformat(self.AccCycleTime))
			print("Accumulated Cycles  = %i"%(self.AccCycles))
			print("Camera Type: %s"%(bytes.decode(self.CameraType)))
			print("Camera Size: %i x %i (%i)"%tuple(self.CameraSize))
			print("Original Filename: %s"%(bytes.decode(self.FileName)))
			print("Shutter Times: %.02f - %.02f"%tuple(self.ShutterTime))
			print("Filter: #%i : %s"%(self.Filter['Number'],bytes.decode(self.Filter['Name'])))
			print("Spectrometer Type: %s"%(bytes.decode(self.SpectrometerType)))
			print("Center Wavelength: %.02f"%(self.CenterWavelength))
			print("Grating: %i g/mm Blaze @ %.02f"%(self.GratingG,self.GratingBlaze))
			print("Frame Axis: %s"%(bytes.decode(self.frameAxis)))
			print("Data Type: %s"%(bytes.decode(self.dataType)))
			print("Image Axis: %s"%(bytes.decode(self.ImageAxis)))
			o=self.frameArea
			print("Frame Area: (%i,%i) -> (%i,%i)"%(o[0][0],o[0][1],o[1][0],o[1][1]))
			o=self.imageArea
			print("Image Area: (%i,%i) -> (%i,%i)"%(o[0][0],o[0][1],o[1][0],o[1][1]))
			print("Frame Bins: %i -> %i"%tuple(self.frameBins))
		def plot(self):
			if self.size['h']==1:
				plt.plot(self.imageData[0])
			else:
				plt.imshow(self.imageData)
			plt.show()

if __name__=="__main__":

	def error(num, txt):
		sys.stderr.write("\033[31mError #%i: \033[0m%s\n"%(num,txt))
		sys.exit(num)
	def info(txt):
		print("\033[32mInfo: \033[0m%s\n"%(txt))
	parser=OptionParser()
	parser.add_option("-s","--sig",dest="sig",help="Specify the file used to read the signal")
	parser.add_option("-B","--sig-bg",action="store_const",dest="sigC",help="Use the background of the signal file as raw signal",const="bg",default="sig")
	parser.add_option("-R","--sig-ref",action="store_const",dest="sigC",help="Use the reference of the signal file as raw signal",const="ref")

	parser.add_option("-b","--bg",dest="bg",help="Specify the file used for the background")
	parser.add_option("-c","--bg-bg",action="store_const",dest="bgC",help="Use the background of the signal file as raw signal",const="bg",default="sig")
	parser.add_option("-d","--bg-ref",action="store_const",dest="bgC",help="Use the reference of the signal file as raw signal",const="ref")

	parser.add_option("-e","--bg-from-sig",action="store_true",dest="bgfromsig",default=False,help="Specify to use the background channel from the signal file as background")
	parser.add_option("-f","--bg-from-ref",action="store_true",dest="bgfromref",default=False,help="Specify to use the background channel from the reference file as background")


	parser.add_option("-r","--ref",dest="ref",help="Specify the file used for the reference")
	parser.add_option("-g","--ref-bg",action="store_const",dest="refC",help="Use the background of the reference file as raw signal",const="bg",default="sig")
	parser.add_option("-i","--ref-ref",action="store_const",dest="refC",help="Use the reference of the reference file as reference signal",const="ref")

	parser.add_option("-j","--ref-from-sig",action="store_true",dest="reffromsig",default=False,help="Specify to use the reference channel from the signal file as reference")
	parser.add_option("-k","--ref-from-bg",action="store_true",dest="reffrombg",default=False,help="Specify to use the background channel from the signal file as reference")
	(options,args) = parser.parse_args()
	if options.sig==None:
		error(1,"No signal file specified. Signal file argument mendatory")
	s=SIF(options.sig)
	if options.bg==None:
		info("No background file specified. No background will be subtracted")
	else:
		b=SIF(options.bg)
