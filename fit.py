#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
import sys,os
import re

class Stack:
	def __init__(self):
		self.stack=[]
		self.debug=False
	def push(self, obj):
		if self.debug: print("PUSH %s"%(str(obj)))
		self.stack.append(obj)
	def pop(self):
		if self.debug: print("POP %s"%(str(self.stack[-1])))
		return self.stack.pop()
	def swap(self):
		if self.debug: print("SWAP")
		a=self.stack.pop()
		b=self.stack.pop()
		self.push(a)
		self.push(b)
	def add(self):
		if self.debug: print("ADD")
		a=self.stack.pop()
		b=self.stack.pop()
		self.push(a+b)
	def sub(self):
		if self.debug: print("SUB")
		a=self.stack.pop()
		b=self.stack.pop()
		self.push(b-a)
	def mul(self):
		if self.debug: print("MUL")
		a=self.stack.pop()
		b=self.stack.pop()
		self.push(a*b)
	def div(self):
		if self.debug: print("DIV")
		a=self.stack.pop()
		b=self.stack.pop()
		self.push(b/a)

class Curve:
	def __init__(self,filename=None):
		self.filename=filename
		self.data=None
		self.stack=Stack()
		if filename!=None: self.load(filename)
	def load(self, filename):	
		if not os.path.exists(filename):
			self.error(1,"Filename %s do not exist"%(filename))
		else:
			self.filename=filename
			self.data=np.genfromtxt(filename)
	def getCol(self,col=0):
		if self.data==None:
			self.error(2,"No data loaded")
			return np.nan
		else:
			return self.data[:,col]
	def error(self, errid, errtxt):
		sys.stderr.write("\033[1;31mError #%i\033[0m: %s\n"%(errid,errtxt))
	def parseData(self, expr):
		par=expr.split(" ")
		for x in par:
			m=re.match(r'^\$([0-9]+)$',x)
			if m:
				self.stack.push(self.getCol(int(m.group(1))))
			m=re.match(r'^[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?$',x)
			if m:
				self.stack.push(float(m.group(0)))
			if x=="+": self.stack.add()
			elif x=="-": self.stack.sub()
			elif x=="*": self.stack.mul()
			elif x=="/": self.stack.div()
		return self.stack.pop()
	def plot(self, X,Y):
		plt.plot(self.parseData(X),self.parseData(Y))
		plt.show()

	def fitPoly(self, x, y, deg, xa, xb):
		i=(x>=xa)*(x<=xb)
		return np.polyfit(x[i],y[i],deg)
	def fit(self, X, Y):
		x=self.parseData(X)
		y=self.parseData(Y)
		x0=x[np.argmax(y)]
		xa=min(x)
		xb=max(x)
		dx=min([x0-xa,xb-x0])
		xa=x0-dx
		xb=x0+dx
		for i in range(7):
			p=self.fitPoly(x,y,2,xa,xb)
			x0=-p[1]/(2*p[0])
			if x0<xa or x0>xb: break
			yy=np.poly1d(p)
			xx=x[(x>=xa)*(x<=xb)]
			plt.plot(xx,yy(xx))
			dx/=1.5
			xa=x0-dx
			xb=x0+dx
		print(x0)
		plt.plot(x,y)
		plt.show()


if __name__=="__main__":
	C=[]
	for i in range(1,len(sys.argv)):
		print("Loading file \"%s\"..."%(sys.argv[i]))
		C.append(Curve(sys.argv[i]))
		for a in range(1,6):
			C[-1].fit("$0","$%i $6 -"%(a))
