#!/usr/bin/python

import sys

ins_set = {
		'LODD' : 0b0000 << 12, 
		'STOD' : 0b0001 << 12,
		'LOCO' : 0b0111 << 12,
		'ADDD' : 0b0010 << 12,
		'SUBD' : 0b0011 << 12,
		'JUMP' : 0b0110 << 12,
		'JZER' : 0b0101 << 12,
		'JNEG' : 0b1100 << 12,
		'LODL' : 0b1000 << 12,
		'STOL' : 0b1001 << 12,
		'ADDL' : 0b1010 << 12,
		'SUBL' : 0b1011 << 12,
		'JPOS' : 0b0100 << 12,
		'JNZE' : 0b1101 << 12,
		'CALL' : 0b1110 << 12,

		'RETN' : 0b11111000 << 8,
		'PUSH' : 0b11110100 << 8,
		'POP'  : 0b11110110 << 8,
		'PSHI' : 0b11110000 << 8,
		'POPI' : 0b11110010 << 8,
		'SWAP' : 0b11111010 << 8,
		'INSP' : 0b11111010 << 8,
		'DESP' : 0b11111110 << 8
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

	if ins not in ins_set:
		raise Exception("Unknown instruction: '" + ins + "'")

	
	lines.append( Line(Line.TYPE_INS, Instruction(i,label,ins,arg) ))

	#addr, instruction, label, instruction, arg
#	print("%03x %1x%03x %-20s %4s %s" % (i, ins_set[ins], 0, label, ins, arg));


	i += 1
#	label = ''


print "-----------------------------------------"
#print labels

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

		ins_enc = (ins_set[ins.ins]&0xFF00) | (argN&0xFF);

		print("%03x %04x %-20s %4s %s" % (ins.n, ins_enc, label, ins.ins, ins.arg))
			
