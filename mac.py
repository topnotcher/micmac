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



class Mic(object):

	def __init__(self):
		self.reset()

	def reset(self):
			self.pc = 0
			self.sp = 0
			self.ac = None
			self.data = None
			self.stack = []

	def load(self,data):

		# @todo out of memory
		self.data = data

	
	def get_mem_data(self,addr):
		if addr >= len(self.data):
			raise Exception("memory location out-of-bounds")

		return self.data[addr]

	def set_mem_data(self,addr,data):
		if  addr > 4095:
			raise Exception("Memory adress out of bounds")

		self.data[addr] = data

	def run(self):
		pc = self.pc

		# in the default case, increment  pc by 1.
		self.pc += 1

		
		instruction = self.get_mem_data(pc)

		arg = instruction&0xff
		op = (instruction>>8)&0xff

		# no operation in this cell...
		if op == 0:
			raise Exception("No-Op")

		
		# try to get the textual version of the oepration:
		
		op_name = None

		for ins_name in OPERATIONS:
			if OPERATIONS[ins_name] == op:
				op_name = ins_name
				break

		if op_name is None:
			raise Exception("undefined operation: " + str(op))


		
		if op_name == 'LODD':
			self.ac = self.get_mem_data(arg)

		elif op_name == 'STOD':
			if self.ac is  None:
				raise Exception("Trying to STOD with a null AC???")

			
			self.set_mem_data(arg,self.ac)

		elif op_name == 'LOCO':
			self.ac = arg

		elif op_name == 'ADDD':
			self.ac += self.get_mem_data(arg)

		elif op_name == 'SUBD':
			self.ac -= self.get_mem_data(arg)

			
		elif op_name == 'JUMP':
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
			self.ac = self.stack[arg-1]

		elif op_name == 'STOL':
			self.stack[arg-1] = self.ac
	
		elif op_name == 'ADDL':
			self.ac += self.stack[arg-1]

		elif op_name == 'SUBL':
			self.ac -= self.stack[arg-1]


		elif op_name == 'CALL':
			self.stack.append(self.pc)
			self.sp += 1
			self.pc = arg

		elif op_name == 'RETN':
			self.sp -= 1
			self.pc = self.stack.pop()

		elif op_name == 'PUSH':
			self.stack.append(self.ac)
			self.sp += 1

		elif op_name == 'POP':
			self.ac = self.stack.pop()
			self.sp -= 1

		elif op_name == 'PSHI':
				pass

		elif op_name == 'POPI':
			pass

		elif op_name == 'SWAP':
			tmp = self.sp 
			self.sp = self.ac
			self.ac = tmp



		elif op_name == 'INSP':
			#TODO bounds check

			self.sp += arg

		elif op_name == 'DESP':
			self.sp -= arg




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

"""ins_no_val = [
		'RETN', 
		'PUSH',
		'POP',
"""

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

	print "%3d     %s" % (N,line),

	#comments and blanks...
	if line.strip().startswith(';') or len(line.strip()) == 0:
		lines.append(Line(Line.TYPE_CMT, line.strip()))
		continue

	try:
		# else it is an instruction
		(label,ins,arg) = line.split("\t")
	except (ValueError):
		print "Epic fail parsing line: "
		print line
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


print "-----------------------------------------"
#print labels
data = []
for line in lines:

	if line.type in (Line.TYPE_CMT, Line.TYPE_WHT):
		print line.data

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

print mic.data[0x23], mic.ac

