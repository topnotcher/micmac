#!/usr/bin/python

class MicMacException(Exception):
	pass

class MacException(MicMacException):
	pass

class NamespaceException(MacException):
	pass

class UndefinedLabelException(MacException):
	pass

class MacAssemblerException(MacException):
	pass

class UndefinedOperationException(MacException):
	pass

class MicException(MicMacException):
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

class ParseError(MacException):
	pass


class Mac(object):
	OPERATIONS = {
			'LODD' : 0b00000000, 

			 # placeholder for defining variables
			'DEFN' : 0b00000000,
			'STOD' : 0b00010000,
			'LOCO' : 0b01110000,
			'ADDD' : 0b00100000,
			'SUBD' : 0b00110000,
			'JUMP' : 0b01100000,
			'JZER' : 0b01010000,
			'JNEG' : 0b11000000,
			'LODL' : 0b10000000,
			'STOL' : 0b10010000,
			'ADDL' : 0b10100000,
			'SUBL' : 0b10110000,
			'JPOS' : 0b01000000,
			'JNZE' : 0b11010000,
			'CALL' : 0b11100000,
			'RETN' : 0b11111000,
			'PUSH' : 0b11110100,
			'POP'  : 0b11110110,
			'PSHI' : 0b11110000,
			'POPI' : 0b11110010,
			'SWAP' : 0b11111010,
			'INSP' : 0b11111100,
			'DESP' : 0b11111110
	}

	def get_name(op) :
		for name in Mac.OPERATIONS:
			if op == Mac.OPERATIONS[name]:
				return name

		return None

	def get_code(name):
		if name not in Mac.OPERATIONS:
			raise UndefinedOperationException("Undefined operation: %s" % (name))

		return Mac.OPERATIONS[name]

	def asm_op(op,arg):

		# stack operations. The op is 1 8 bits, arg 8.
		if (op >> 4) == 0b1111:		
			return (op&0xff)<<8 | (arg&0xff)

		# other opartions. The op is 4 bits, arg 12.
		else:
			# dont mask arg because in the case of a defined constant,
			# the data is the whole thing. 
			return (op&0xf0)<<8 | (arg)

	
	def dasm_op(instruction):
		# stack op.
		if ((instruction & 0xf000) >> 12) == 0b1111:
			return ( (instruction&0xff00)>>8, instruction&0xff )

		# other op
		else:
			return ( (instruction&0xf000)>>8, instruction&0xfff )


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
			raise AddressOutOfBoundsException("memory adress out of bounds 0x%04x >= 0x%04x " % (addr, MicMemory.MEM_SIZE))

		if addr in self.overlay:
			return self.overlay[addr]
		else:
			return self.data[addr]

	def __setitem__(self,addr,data):

		if addr >= MicMemory.MEM_SIZE:
			raise AddressOutofBoundsException("memory address out of bounds. 0x%04x >= 0x%04x " % (addr, MicMemory.MEM_SIZE) )

		if data > 0xffff:
			raise NumberOverflowException("M[0x%04x] = %d: value %d is out of bounds." % (addr,data,data)) 

		# create a backup.
		self.overlay[addr] = data

		
class Mic(object):

	# prevent the stack from growing beyond this address...
	MAX_STACK_SIZE = 2048

	# prevent nesting beyond this level...
	MAX_CALL_DEPTH = 100

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

		#self.pc += 1
		pc =  self.pc

		try:
			instruction = self.data[pc]
		except AddressOutOfBoundsException as e:
			raise AddressOutOfBoundsException("Address out of bounds while trying to fetch next instruction: \n > " % (str(e)))

		(op,arg) = Mac.dasm_op(instruction)
 		
		# try to get the textual version of the oepration:
		
		op_name = Mac.get_name(op)

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
			self.depth += 1

			if self.depth >= Mic.MAX_CALL_DEPTH:
				raise InfiniteRecursionException("Infinite recursion detected: depth(%d) >= MAX_DEPTH()." % (self.depth, Mic.MAX_CALL_DEPTH))

			self.desp()
			self.data[self.sp] = self.pc+1
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


		# wasn't a jump instruction
		if self.pc == pc:
			self.pc += 1

class MicProgramLine(object):

	def __init__(self, n, txt = '', op = None, dbg_op = None):
		self.n = n
		self.op = op
		self.txt = txt
		self.dbg_op = dbg_op

	def __str__(self):
		return "%4d: %s" % (self.n, self.txt)

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
			raise UndefinedLabelException("undefined label '%s'" % name)

		return self.syms[name]
	
	def sym_lookup_reverse(self,addr):
		for name in self.syms:
			if self.syms[name] == addr:
				return name
		return None

	def add_line(self,line):
		self.lines.append(line)
		
		# there's an asm op in the line
		if line.op is not None:
			# map the address to the line #.
			self.mmap.append( len(self.lines) - 1 )

			# if there was program data, 
			# we return the allocated memory address
			return len(self.mmap)-1

		# othwise, return none
		return None

	def line_addr_lookup(self,line):
		return self.mmap.index(line.n - 1)


	def get_line(self,line):
		return self.lines[line]

	def get_line_by_addr(self,addr):
		return self.lines[ self.mmap[addr] ]

	def iter_lines(self):
		for line in self.lines:
			yield line

	def __getitem__(self,addr):
		return self.lines[ self.mmap[addr] ].op
		
	def __setitem__(self,addr,value):
		raise Exception("MicProgram memory is immutable. Use a fucking overlay [beacuse I mother-fucking said so.]")

	def __len__(self):
		return len(self.mmap)

class MacAsm(object):

	def __init__(self,data):
		self.data = data

	def get_pgm(self):
		return self.pgm

	def assemble(self):

		# line : symbol
		# each time we find a reference toa symbol during phase 1 (tokenizing),
		# we add the line/symbol to this list.
		# during phase 2, we look through the list to resolve the references.
		self.sym_lookups = {}

		self.pgm = MicProgram()


		self.line = 0
		self.next_label = None

		self.parse_asm()

		self.resolve_labels()
	

	def parse_asm(self):
		# pass 1: we go through and tokenize every line.
		for line in self.data:

			try:
				self.assemble_line(line)
			except MacException as e:
				raise MacAssemblerException( "%s: parse error on line %d: \n > error: %s\n%s" % 
						( e.__class__.__name__, self.line+1, str(e), line.rstrip() )
					)

			self.line += 1


	def resolve_labels(self):

		# pass 2: resolve references to symbols.
		for line_n in self.sym_lookups:
			sym = self.sym_lookups[line_n]

			try:
				sym_val = self.pgm.sym_lookup(sym)
			except MacException as e:
				# long cat is long.
				raise MacAssemblerException( "%s: Error looking up symbol '%s' on line %d:\n > error: %s\n%s" % 
						( e.__class__.__name__, sym, line_n+1, str(e), self.pgm.get_line(line_n) ) 
					)
			
			# now we have a symbol value, so get the line/op to update.
			pgm_line = self.pgm.get_line(line_n)
			(op,arg) = Mac.dasm_op(pgm_line.op)

			pgm_line.op = Mac.asm_op(op,sym_val)


	def strip_comment(self,line,pgm_line):
			
		pcs = line.split(';',1)
		
		# any code will be before the ;
		code = pcs[0].strip()

		# there is a comment.
		if len(pcs) == 2:
			# see if there's a dbg command in the comment.
			pcs = pcs[1].split('dbg_',1)
			
			# there is a dbg command.
			if len(pcs) == 2:
				pgm_line.dbg_op = pcs[1].strip()

		if len(code) > 0:
			return code

		else:
			return None

	def tokenize_code(self,code,pgm_line):
	
		# none = default of all whitespace.
		# yeah, tht's fucking stupid and cryptic of me.
		toks = code.split(None,2)
			
		i = 0

		op = None
		arg = None

		for tok in toks:

			# a label 
			if tok.endswith(':'):

				if i != 0:
					raise ParseError("Unexpected label.  There can only be one label per line and it must be the first token.")
		
				# assign this label to the next op (this line, or next line with an op)
				self.next_label = tok[0:-1]

			# it's not a label, it's not a whitespace/comment and there's no op yet.
			elif op is None:
				op = Mac.get_code(tok)


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
				# queue symbol for lookup in phase 2.
				self.sym_lookups[self.line] = arg

				# set it to 0 for now
				arg = 0


			else:
				arg = int(arg)

			# now we can assemble the op, update the line.
			pgm_line.op = Mac.asm_op(op,arg)


	def assemble_line(self,line):

		line = line.rstrip()

		pgm_line = MicProgramLine(self.line+1, line)

		# do this after to preserve indenting.
		line = line.lstrip()

		code = self.strip_comment(line,pgm_line)

		# each line has the form:
		#label: OP ARG whitsp/comment.

		if code is not None:
			self.tokenize_code(code,pgm_line)

		# now add the line to the program.
		addr = self.pgm.add_line(pgm_line)

		# this line or a line above it(with no op) had a label.
		# now we have an address for the label, so we add it to the symbol table.
		if addr is not None and self.next_label is not None:
			self.pgm.add_sym(self.next_label, addr)
			self.next_label = None



def baudet_remove_label(txt):
		# see large note below regarding labels
		pcs = txt.strip().split(None,2)
		
		# it's a label
		if len(pcs) >= 1 and len(pcs[0]) >= 1 and pcs[0][-1] == ':':
			pcs[0] = ''

		return ' '.join(pcs).strip()
	
def print_line_baudet(pgm,line):
		if line.op is None:
			txt = baudet_remove_label(line.txt)

			if len(txt) > 0:
				print(txt)
		else:
			addr = pgm.line_addr_lookup(line)
			sym = pgm.sym_lookup_reverse(addr) 

			if sym == None:
				sym = ''
			else: 
				sym += ':'
			
			# my assembler allows me to put the labels on their own lines
			# but baudet format has them inline with the "next" instruction
			# for consistent formatting, I need to see if the line being output
			# has a label.. etc

			txt = baudet_remove_label(line.txt)

			# disaseembly can be sketchy, so we just add the text to the end.
			print("%03x %04x %-20s %s" % (addr, line.op, sym, txt))

def print_baudet(pgm):
	for line in pgm.iter_lines():

		print_line_baudet(pgm, line)
	

def print_numbered(pgm):
	for line in pgm.iter_lines():
		print(line)


# break 
# jump 
# view registers: ac, pc, sp.
# view stack.
# run arbitrary code?

class ConsoleDebugger(object):
	import sys

	def __init__(self,pgm,echo = False):

		self.mic =  Mic()
		self.mic.load(pgm)
		self.pgm = pgm
		self.echo = echo
		self.paused = False

	def run(self):
		
		last_line = -1

		while not self.mic.end: 
			# this is the next line with an instruction in it.
			# 	- also the line being executed this iteration.
			next_line = self.pgm.get_line_by_addr(self.mic.pc)

			for i in range(last_line+1, next_line.n):
				pgm_line = self.pgm.get_line(i)
			
				if pgm_line.dbg_op is not None:
					self.dbg_op(pgm_line.dbg_op, pgm_line)

				if self.echo:
					print(pgm_line)

			#print(next_line)

			last_line = next_line.n-1

			try:
				pc = self.mic.pc 
				
				if self.paused:
					self.console()

				self.mic.step()
				
				# sort of hackish way to detect a jump.
				if self.mic.pc - pc != 1:
					# if there's a jump, reset the last line printed...
					last_line = self.pgm.get_line_by_addr(self.mic.pc).n-2

			except MicMacException as e:
				print("%s[%d]: %s" % (e.__class__.__name__,next_line.n,str(e)) ,file=sys.stderr)
				exit(1)

	def console(self):

		while True:
			print('> ',end='')
			sys.stdout.flush()
			
			if self.dbg_op( sys.stdin.readline() ):
				return

			if  not self.paused:
				return

	def dbg_op(self,cmd_line,pgm_line = None):

		toks = cmd_line.split()

		if len(toks) < 1:
			return False

		cmd = toks[0]

		if len(toks) > 1:
			args = tuple(toks[1:])
		else:
			args = ()
	
		if pgm_line is not None:
			print('DEBUG[%d]: %s' % (pgm_line.n, pgm_line.dbg_op))

		if cmd == 'break':
			self.paused = True

		elif cmd == 'run':
			self.paused = False
			return True

		elif cmd == 'step':
			return True
	
		elif cmd == 'print':
			if len(args) != 1:
				print("print requires exactly 1 argument")

			# a label....
			if not args[0].isnumeric():
				try: 
					addr = self.pgm.sym_lookup(args[0])
				except UndefinedLabelException:
					print("*** symbol '%s' not found" % args[0])
					return
				
			else:
				addr = int(args[0])

			try:
				value = self.mic.data[addr]
			except AddressOutOfBoundsException:
				print("*** address %d out of bounds" % (addr))
				return

			print('M[{:s}, 0x{:04x}] = {:5d}, 0x{:04x}, 0b{:016b}'.format(args[0],addr,value,value,value))


		elif cmd == 'exit':
			exit(0)
		return False
			

def main():

	import argparse,sys


	parser = argparse.ArgumentParser(description='Assemble, debug, simulate programs written in the Mac assembly language for Mic.')

	parser.add_argument('-o', help="Reformat code into specified output format.", action='append', choices=['baudet','numbered'],default=[] )

	parser.add_argument('-r', '--run', help="Default behavior. Run the program. Cannot be mixed with -o.", action='store_true', default=True)
	parser.add_argument('-e', '--echo', help="With --run, echo the lines being executed.", action='store_true')

	parser.add_argument('file', type=argparse.FileType('r'), help="Input file for assembler. - for stdin.")

	args = parser.parse_args()
	asm = MacAsm(args.file)
 
	# in every case, we need to assemble the damn thing.
	try: 
		asm.assemble()

	except MacAssemblerException as e:
		print("Assembly failed: %s" % (str(e)), file=sys.stderr)
		exit(1)

	pgm = asm.get_pgm()

	if 'numbered' in args.o:
		print_numbered(pgm)

	if 'baudet' in args.o:
		print_baudet(pgm)

	#dont invoke the debugger if 
	if not args.run or len(args.o) > 0:
		exit(0)
	
	dbg = ConsoleDebugger(pgm, echo=args.echo)


	dbg.run()

	#run the debugger
#	print(mic.data[0x23])


if __name__ == '__main__':
	import traceback,sys

	try:
		main()

	#at leat this looks like I handled the exception...
	except Exception as e: 
		print(file=sys.stderr)
		print('***** MicMac crashed. Python exception follows.',file=sys.stderr)
		print('--------------------------------------------',file=sys.stderr)
		print('Type:', e.__class__.__name__,file=sys.stderr)
		print('Message:', str(e),file=sys.stderr)
		print(file=sys.stderr)
		print(traceback.format_exc(),file=sys.stderr)
		print(file=sys.stderr)
		exit(1)

