#!/usr/bin/python

import sys

OPERATIONS = {
		'LODD' : 0b00000000 , 
		'STOD' : 0b00010000 ,
		'LOCO' : 0b01110000 ,
		'ADDD' : 0b00100000 ,
		'SUBD' : 0b00110000 ,
		'JUMP' : 0b01100000 ,
		'JZER' : 0b01010000 ,
		'JNEG' : 0b11000000 ,
		'LODL' : 0b10000000 ,
		'STOL' : 0b10010000 ,
		'ADDL' : 0b10100000 ,
		'SUBL' : 0b10110000 ,
		'JPOS' : 0b01000000 ,
		'JNZE' : 0b11010000 ,
		'CALL' : 0b11100000 ,
		'RETN' : 0b11111000,
		'PUSH' : 0b11110100,
		'POP'  : 0b11110110,
		'PSHI' : 0b11110000,
		'POPI' : 0b11110010,
		'SWAP' : 0b11111010,
		'INSP' : 0b11111010,
		'DESP' : 0b11111110
}

class MicException(Exception):
	pass

class AddressOutOfBoundsException(MicException):
	pass


# basic object to represent the memory in the MIC
class MicMemory(object):
	MEM_SIZE = 4096

	def __init__(self,data):
		if len(data) > MicMemory.MEM_SIZE:
			raise AddressOutOfBoundsException("Size exceeds available memory of the Mic")

		# data that is loaded in "by default"
		self.data = data

		self.original = {}


	def reset(self):
		
		for addr in self.original:
			self.data[addr] = self.original[addr]

		# overlay is things we have changed 
		# this prevents modification of the memory itself
		# so we can start over without reloading anything.
		self.original = {}

	def __getitem__(self,addr):
		if addr >= MicMemory.MEM_SIZE:
			raise AddressOutOfBoundsException("memory adress out of bounds")

		return self.data[addr]

	def __setitem__(self,addr,data):

		if addr >= MicMemory.MEM_SIZE:
			raise AddressOutofBoundsException("memory address out of bounds")

		# create a backup.
		self.original[addr] = self.data[addr]

		
		self.data[addr] = data

		
class Mic(object):

	def __init__(self):
		self.data = None
		self.reset()

	def reset(self):
			# program entry point is always addr 0
			self.pc = 0

			#start the stack pointer below the bottom of memory.
			self.sp = MicMemory.MEM_SIZE

			self.ac = None

			if self.data is not None:
				self.data.reset()
			else:
				self.data = None

			#has the proram terminated?
			self.end = False

	def load(self,data):

		# @todo out of memory
		self.data = MicMemory(data)

	
	def run(self, limit = None)	:

		if self.end:
			raise Exception("Program completed")
		
			# Todo limit.
		while self.end is False:
			self.step()

	def step(self):

		if self.end:
			raise Exception("Program completed")

		pc = self.pc

		# in the default case, increment  pc by 1.
		self.pc += 1

		try:
			instruction = self.data[pc]
		except AddressOutOfBoundsException :
			raise AddresOutOfBoundsException("Memory address PC = %04x out of bounds while trying to fetch next instruction." % pc)

		arg = instruction&0xff
		op = (instruction>>8)&0xff
	
		# try to get the textual version of the oepration:
		
		op_name = None

		for ins_name in OPERATIONS:
			if OPERATIONS[ins_name] == op:
				op_name = ins_name
				break

		if op_name is None:
			raise Exception("undefined operation: " + str(op))


		if op_name == 'LODD':
			self.ac = self.data[arg]

		elif op_name == 'STOD':
			if self.ac is  None:
				raise Exception("Trying to STOD with a null AC???")

			
			self.data[arg] = self.ac

		elif op_name == 'LOCO':
			self.ac = arg

		elif op_name == 'ADDD':
			self.ac += self.data[arg]

		elif op_name == 'SUBD':
			self.ac -= self.data[arg]

			
		elif op_name == 'JUMP':
				
			#trying to jump to current instruction = stop
			if self.pc == arg:
				self.end = True
				
			self.pc = arg
	

		elif op_name == 'JZER':
			if self.ac == 0:
				self.pc = arg

		elif op_name == 'JNEG':
			if self.ac < 0:
				self.pc = arg

		elif op_name == 'JPOS':
			if self.ac >= 0:
				self.pc = arg
				
		elif op_name == 'JNZE':
			if self.ac != 0:
				self.pc = arg

		elif op_name == 'LODL':
			#todo handle bounds better
			self.ac = self.data[self.sp + arg]

		elif op_name == 'STOL':
			self.data[self.sp + arg] = self.ac
	
		elif op_name == 'ADDL':
			self.ac += self.data[self.sp + arg]

		elif op_name == 'SUBL':
			self.ac -= self.data[self.sp + arg]

		elif op_name == 'CALL':
			self.sp -= 1
			self.data[self.sp] = self.pc
			self.pc = arg

		elif op_name == 'RETN':
			self.pc = self.data[self.sp]
			self.sp += 1

		elif op_name == 'PUSH':
			self.sp -= 1
			self.data[self.sp] = self.ac

		elif op_name == 'POP':
			self.ac = self.data[self.sp]
			self.sp += 1

		elif op_name == 'PSHI':
			self.sp -= 1
			self.data[self.sp] = self.data[arg]

		elif op_name == 'POPI':
			self.data[arg] = self.data[self.sp]
			self.sp += 1

		elif op_name == 'SWAP':
			tmp = self.sp 
			self.sp = self.ac
			self.ac = tmp

		elif op_name == 'INSP':
			#TODO bounds check

			self.sp += arg

		elif op_name == 'DESP':
			self.sp -= arg


class Instruction(object):
	def __init__(self,n,label,ins,arg):
		self.n = n
		self.label = label
		self.ins = ins
		self.arg = arg

	
class Line(object):
	TYPE_INS = 0
	TYPE_WHT = 1
	TYPE_CMT = 2

	def __init__(self,type,data):
		self.type = type
		self.data = data


	

lines = []

labels = {}

N = 0;
i = 0
label = None

for line in sys.stdin:
	N += 1
#	line = line.strip()

	print("%3d     %s" % (N,line)),

	#comments and blanks...
	if line.strip().startswith(';') or len(line.strip()) == 0:
		lines.append(Line(Line.TYPE_CMT, line.strip()))
		continue

	try:
		# else it is an instruction
		(label,ins,arg) = line.split("\t")
	except (ValueError):
		print("Epic fail parsing line: ")
		print(line)
		exit();
		

	arg = arg.strip();

	if len(label) > 1 and label[-1] == ':':
		label = label[0:-1]
		labels[label] = i
	else:
		label = None

	if ins not in OPERATIONS:
		raise Exception("Unknown instruction: '" + ins + "'")

	
	lines.append( Line(Line.TYPE_INS, Instruction(i,label,ins,arg) ))

	#addr, instruction, label, instruction, arg
#	print("%03x %1x%03x %-20s %4s %s" % (i, OPERATIONS[ins], 0, label, ins, arg));


	i += 1
#	label = ''


print("-----------------------------------------")
#print labels
data = []
for line in lines:

	if line.type in (Line.TYPE_CMT, Line.TYPE_WHT):
		print(line.data)

	elif line.type == Line.TYPE_INS:
		ins = line.data
		label = ''
		if ins.label is not None:
			label = ins.label + ':'
		
		if not ins.arg.isdigit():
			argN = labels[ins.arg]
		else:
			argN = int(ins.arg)

		ins_enc = ((OPERATIONS[ins.ins]&0xFF) << 8) | (argN&0xFF);

		data.append(ins_enc)

		print("%03x %04x %-20s %4s %s" % (ins.n, ins_enc, label, ins.ins, ins.arg))
			

mic = Mic()

mic.load(data)

mic.run()

print(mic.data[0x23], mic.ac)

