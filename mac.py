#!/usr/bin/python

import sys

class Mac(object):
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

	def get_name(op) :
		for name in Mac.OPERATIONS:
			if op == Mac.OPERATIONS[name]:
				return name

		return None

	def get_code(name):
		if name not in Mac.OPERATIONS:
			return None

		return Mac.OPERATIONS[name]

	def asm_op(op,arg):

		# stack operations. The op is 1 8 bits, arg 8.
		if (op >> 4) == 0b1111:		
			return (op&0xff)<<8 | (arg&0xff)

		# other opartions. The op is 4 bits, arg 12.
		else:
			return (op&0xf)<<8 | (arg&0xfff)

	
	def dasm_op(instruction):

		# stack op.
		if ((instruction & 0xf000) >> 12) == 0b1111:
			return ( (instruction&0xff00)>>8, instruction&0xff )

		# other op
		else:
			return ( (instruction&0xf000)>>8, instruction&0xfff )

class MicException(Exception):
	pass

class NumberOverflowException(MicException):
	pass

class AddressOutOfBoundsException(MicException):
	pass

class StackOverflowException(MicException):
	pass

class StackUnderflowException(MicException):
	pass

class InfiniteRecursionException(MicException):
	pass


# basic object to represent the memory in the MIC
# This just handles the "frontend" of the memory.
#  when MicMemory is instantiated, it must be passed some
# subscriptable object to back it.
class MicMemory(object):
	MEM_SIZE = 4096

	def __init__(self,data):
		if len(data) > MicMemory.MEM_SIZE:
			raise AddressOutOfBoundsException("Size exceeds available memory of the Mic")

		# data that is loaded in "by default"
		self.data = data

		self.overlay = {}


	def reset(self):
		
		# overlay is things we have changed 
		# this prevents modification of the memory itself
		# so we can start over without reloading anything.
		self.overlay = {}

	def __getitem__(self,addr):
		if addr >= MicMemory.MEM_SIZE:
			raise AddressOutOfBoundsException("memory adress out of bounds")

		if addr in self.overlay:
			return self.overlay[addr]
		else:
			return self.data[addr]

	def __setitem__(self,addr,data):

		if addr >= MicMemory.MEM_SIZE:
			raise AddressOutofBoundsException("memory address out of bounds")

		if data > 0xffff:
			raise NumberOverflowException("M[%d] = %d: value %d is out of bounds." % (addr,data,data)) 

		# create a backup.
		self.overlay[addr] = data

		
class Mic(object):

	# prevent the stack from growing beyond this address...
	MAX_SATCK_SIZE = 2048

	# prevent nesting beyond this level...
	MAX_CALL_DEPTH = 100

	def __init__(self):
		self.data = None
		self.reset()

	def reset(self):
			# program entry point is always addr 0
			self.pc = -1

			#start the stack pointer below the bottom of memory.
			self.sp = MicMemory.MEM_SIZE

			self.ac = None

			if self.data is not None:
				self.data.reset()
			else:
				self.data = None

			# how many CALL()s deep are we?
			self.depth = 0

			#has the proram terminated?
			self.end = False

	def load(self,data):

		# @todo out of memory
		self.data = MicMemory(data)


	# increment stack pointer
	def insp(self,amt = 1):

		if (self.sp+amt) >= MicMemory.MEM_SIZE:
			raise StackUnderflowException("SP(%04x) += %d underflows the stack" % (self.sp, amt))

		self.sp += amt

	def desp(self,amt = 1):

		if (self.sp-amt) < MicMemory.MEM_SIZE - Mic.MAX_STACK_SIZE:
			raise StackOverflowException("SP(%04x) -= %d overflows the stack. MAX_STACK_SIZE = %d" % (self.sp, amt, Mic.MAX_STACK_SIZE))

		self.sp -= amt

	def run(self, limit = None)	:

		if self.end:
			raise Exception("Program completed")
		
			# Todo limit.
		while self.end is False:
			self.step()

	def step(self):

		if self.end:
			raise Exception("Program completed")

		# in the default case, increment  pc by 1.
		self.pc += 1
		pc =  self.pc

		try:
			instruction = self.data[pc]
		except AddressOutOfBoundsException :
			raise AddresOutOfBoundsException("Memory address PC = %04x out of bounds while trying to fetch next instruction." % pc)

		(op,arg) = Mac.dasm_op(instruction)
	
		# try to get the textual version of the oepration:
		
		op_name = Mac.get_name(op)

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

			if self.depth >= Mic.MAX_CALL_DEPTH:
				raise InfiniteRecursionException("Infinite recursion detected: depth(%d) >= MAX_DEPTH()." % (self.depth, Mic.MAX_CALL_DEPTH))

			self.desp()
			self.data[self.sp] = self.pc
			self.pc = arg



		elif op_name == 'RETN':
			self.depth -= 1

			if self.depth < 0:
				raise StackUnderflowException("Tried to return from too many calls...")

			self.pc = self.data[self.sp]

			self.insp()

		elif op_name == 'PUSH':
			self.desp()
			self.data[self.sp] = self.ac

		elif op_name == 'POP':
			self.ac = self.data[self.sp]
			self.insp()

		elif op_name == 'PSHI':
			self.desp()
			self.data[self.sp] = self.data[arg]

		elif op_name == 'POPI':
			self.data[arg] = self.data[self.sp]
			self.insp()

		elif op_name == 'SWAP':
			tmp = self.sp 
			self.sp = self.ac
			self.ac = tmp

		elif op_name == 'INSP':
			self.insp(arg)

		elif op_name == 'DESP':
			self.desp(arg)

class MacException(Exception):
	pass

class NamespaceException(MacException):
	pass

class UndefinedLabelException(MacException):
	pass

class MacAssemblerException(MacException):
	pass

class MicProgramLine(object):

	def __init__(self, n, txt = '', op = None, dbg_op = None):
		self.n = n
		self.op = op
		self.txt = txt
		self.dbg_op = dbg_op

# Acts as a backing class for MicMemory, but
# additionally parses every line of the source file, storing the 
# source alongside the binary instructions to facilitate debugging
class MicProgram(object):

	def __init__(self):

		# symbol table; label: mem_addr
		self.syms = {}

		self.mmap = []

		self.lines = []

	def add_sym(self, name, addr):

		if name in self.syms:
			raise NamespaceException("Duplicate definition of label %s." % name)

		self.syms[name] = addr

	def sym_lookup(self,name):
		if name not in self.syms:
			raise UndefinedLabelException("Reference to undefined label %s" % name)

		return self.syms[name]
	
	def add_line(self,line):
		self.lines.append(line)
		
		# there's an asm op in the line
		if line.op is not None:
			# map the address to the line #.
			self.mmap.append( len(self.lines) - 1 )

			# if there was program data, 
			# we return the allocated memory address
			return len(self.mmap-1)

		# othwise, return none
		return None

	def get_line(self,line):
		return self.lines[line]

	def __getitem__(self,addr):
		return self.lines[ self.mmap[addr] ].op
		
	def __setitem__(self,addr,value):
		raise Exception("MicProgram memory is immutable. Use a fucking overlay [beacuse I mother-fucking said so.]")


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


class MacAsm(object):

	def __init__(self,data):
		self.data = data

		self.line = 0

		self.next_label = None

		self.pgm = MicProgram()

		# line : symbol
		# each time we find a reference toa symbol during phase 1 (tokenizing),
		# we add the line/symbol to this list.
		# during phase 2, we look through the list to resolve the references.
		self.sym_lookups = {}

	def assemble(self):

		self.sym_lookups = {}

		# pass 1: we go through and tokenize every line.
		for line in self.data:

			try:
				self.assemble_line(line)
			except Exception as e:
				raise MacAssemblerException( "%s: parse error on line %d: \n > error: %s\n%s" % ( e.__class__.__name__, line_n, str(e), self.pgm.get_line(line_n) ) )

			self.line += 1

		# pass 2: resolve references to symbols.
		
		for line_n, sym in self.sym_lookups:

			try:
				sym_val = self.pgm.sym_lookup(sym)
			except Exception as e:
				# long cat is long.
				raise MacAssemblerException( "%s: Error looking up symbol '%s' on line %d:\n > error: %s\n%s" % ( e.__class__.__name__, sym, line_n, str(e), self.pgm.get_line(line_n) ) )
				

		self.sym_lookups = {}

	def assemble_line(self,line):

		line = line.rstrip()

		pgm_line = MicProgramLine(self.line+1, line)

		line = line.lstrip()


		# each line has the form:
		#label: OP ARG whitsp/comment.

		toks = line.split(None,3)
			
		i = 0

		op = None
		arg = None

		for tok in toks:

			# the rest of the line is a comment.
			if tok.startswith(';'):
				# TODO: handle dbg_op
				break

			elif tok.endswith(':'):

				if i != 0:
					raise Exception("Unexpected label at pos %d" % i)
		
				self.next_label = tok[0:-1]

			# it's not a label, it's not a whitespace/comment and there's no op yet.
			elif op is None:
				op = Mac.get_code(tok)

				if op is None:
					raise Exception("Undefined operation, %s" % tok)

			# it must be an arg!
			elif arg is None:
				arg = tok

			else:
				break


			i += 1

		if op is not None:

			if arg is None:
				arg = 0

			# not none, not numeric... label!
			elif not arg.isnumeric():
				arg = 0

				# queue symbol for lookup in phase 2.
				self.sym_lookups[line] = arg

			# now we can assemble the op, update the line.
			pgm_line.op = Mac.op_asm(op,arg)


		# now add the line to the program.
		addr = self.pgm.add_line(line)

		# this line or a line above it(with no op) had a label.
		# now we have an address for the label, so we add it to the symbol table.
		if addr is not None and self.next_label is not None:
			self.pgm.add_sym(self.next_label, addr)
			self.next_label = None


				

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

	if ins not in Mac.OPERATIONS:
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

		ins_enc = ((Mac.OPERATIONS[ins.ins]&0xFF) << 8) | (argN&0xFF);

		data.append(ins_enc)

		print("%03x %04x %-20s %4s %s" % (ins.n, ins_enc, label, ins.ins, ins.arg))
			

mic = Mic()

mic.load(data)

mic.run()

print(mic.data[0x23], mic.ac)

