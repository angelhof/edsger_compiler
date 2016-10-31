from llvmlite import ir
import ctypes

'''
So the final ir module will look like this

# Instantiate an outside module and func
# Recursively run the ast and make code

##
# Have a general temporary variable counter and save every side expression result to them "_temp1"
# Every sub-expression will save its result to keyed-value with the corresponding temporary name, 
	-> then the next expression that needed it gets one argument from it and so on
# The __generate__ function in every expression class will return the name of the result so the calling function can find it
 
### First of all
##  Find how to compile the resulting ir code so that we can test all the time the correctness of the programm

### Important thing to consider??? 
##  Because of all the checks we have already made there is no need to check anything else , except for the dynamic ones.
##  So we just generate code with all the functions in the same place with the only thing differentiating them be their signature
'''
class Extended_DoubleType(ir.DoubleType):
	null = '0.0'
	intrinsic_name = 'fp80'

	def __str__(self):
		return 'x86_fp80'

	def format_constant(self, value):
		return string_to_Expanded_DoubleType(value)

def python_strtold(strn):
	libstrtold = ctypes.CDLL("./obj/libstrtold.so")
	strtoddler = libstrtold.strtolden
	p = ctypes.pointer(ctypes.c_char()) 
	strtoddler.restype = ctypes.c_char_p
	result = strtoddler(str(strn))
	return result

def string_to_Expanded_DoubleType(strn):
	number = python_strtold(strn)
	if ("-" in number.split("x")[0]):
		sign = "0x8000"
	else:
		sign = "0x0000"
	fraction = number.split("x")[1]
	exponent = int(fraction.split("p")[1])
	fraction = fraction.split("p")[0].replace(".","")

	exponent = hex(int(sign,16) 
					+ int("0x4000", 16)
					+ exponent+2)
	result = (str(exponent).split("0x")[1]+ fraction)
	result = result + (20-len(result))*"0"
	result = "0xK" + result 
	return result


'''
A class that holds the bit size of its type
TODO:
- Bool needs to be 8 but then we have to change code
- Double number is never used ( Have to check official docs)
- Pointer type is never used
'''
class TypeSizes(object):
	int = 16
	char = 8
	bool = 1
	double = 80
	pointer = 64


class IR_State(object):
	# Counter that keeps the next variable number
	var_counter = 0
	# Maps the variable index to real python variables 
	var_map = []
	# Block counter used to make the block names
	block_counter = 0
	# Maps the block index to a block 
	# VERY IMPORTANT
	#   -> we cannot keep the if blocks here because they are generated automatically
	block_map = {}
	# variable map for mapping the variables in the functions FIX ME!!!!!!!!!!!! REAL VARIABLES
	eds_var_map = [{}]
	# state of informing whether we are on the right or the left side of the code
	left_side = False
	# Maps the function name to a function (Maybe stack of maps)
	# Remember to go to its enty block like this -> IRBuilder.goto_entry_block()
	function_map = [{}]
	# It exists so that we give unique names to every current_scope register
	current_scope_cnt = 0
	# Unreachable array so that we go and make sure all unreachable blocks get terminated
	unreachable_array =[]
	# Empty Module
	module = ir.Module(name=__file__)
	# Create a function inside the module
	func = ir.Function(module, ir.FunctionType(ir.IntType(TypeSizes.int), []), name="main")
	# Insert an unreachable block, and the main block
	block = func.append_basic_block(name="main")
	# Basic IR module, the builder
	builder = ir.IRBuilder(block)
	# Function Unique Identifier
	function_unique_identifiers = {}
	# main pointer steady
	main_anchor = None
	Extended_DoubleType._create_instance()
	# Function main will be saved here so that we know
	possibly_unterminated_blocks = []

	@classmethod
	def rec_code_generation(cls, head):

		# Globally exoume mono declarations ara sta
		# head tha kanoume code_gen_decl()
		if(type(head) is list):
			for element in head:
				cls.rec_code_generation(element)
		else:
			head.code_gen_decl()
		# Debug only
		# print cls.module
	''' Old method
	@classmethod
	def code_generation(cls, head):
		cls.rec_code_generation(head)

		cls.terminate_blocks()

		print cls.module

		fp = open("test_asm", "w")
		fp.write(str(cls.module))
	'''	
	@classmethod
	def all_code_generation(cls, head_list):

		# Initialize all the string constants
		cls.initialize_string_constants()

		# Import the new and delete functions
		cls.import_new_and_delete()

		for code_head in head_list[1:]:
			cls.rec_code_generation(code_head)
		cls.rec_code_generation(head_list[0])
		
		'''
		It is deleted because main now is compiler named
		main that handels the main output and returns it
		with cls.builder.goto_block(cls.block):
			ret_result = ir.Constant(ir.IntType(16), 0)
			cls.builder.ret(ret_result)
		'''

		cls.terminate_blocks()

		#print cls.module

		return cls.module

		
	@classmethod
	def terminate_blocks(cls):
		# Call the main function from the global main
		#print IR_State.main_anchor
		main_function = cls.get_from_function_map(IR_State.main_anchor).function
		with cls.builder.goto_block(cls.block):
			dest = IR_State.builder.call(main_function, 
						[], name="_main_value")
			if isinstance(main_function.ftype.return_type, ir.types.VoidType):
				cls.builder.ret(ir.Constant(ir.IntType(TypeSizes.int), 0))
			else:	
				cls.builder.ret(dest)

		# Terminate the blocks that have no termination
		array = [x for x in cls.unreachable_array if not x.is_terminated]
		for block in array:
			if(not block.is_terminated):
				IR_State.builder.position_at_end(block)
				#IR_State.builder.branch(block)
				IR_State.builder.unreachable()

		#print dir(IR_State.builder)
	@classmethod
	def initialize_string_constants(cls):
		i = 0
		for string_constant in StringConstants.strings:
			
			string_decoded_value = (string_constant[1:-1]+'\0').decode('string_escape')
			string_value = [ord(c) for c in string_decoded_value]
			'''Debug
			print len(string_constant)
			print string_constant
			print len(string_decoded_value)
			print string_decoded_value
			print len(string_value)
			print string_value
			'''
			string_type = ir.ArrayType( \
						ir.IntType( \
							TypeSizes.char \
						), len(string_value))
			string_ir_const_value = ir.Constant(string_type,
						string_value)
			string_ir_value = ir.GlobalVariable(cls.module, 
							string_type, "_string-"+str(i))
			string_ir_value.global_constant = True
			string_ir_value.initializer = string_ir_const_value 
			StringConstants.strings[string_constant] = string_ir_value

			i+=1
	@classmethod
	def import_new_and_delete(cls):
		'''
		Warning: I used generic int pointers 
			(Might need to change that)
		'''
		# Declare _new
		IR_State.new_function = ir.Function(cls.module,
			ir.FunctionType( \
				ir.PointerType(ir.IntType(TypeSizes.int)), 
				[ir.IntType(TypeSizes.int)]), "new")
		# Declare _dispose
		IR_State.dispose_function = ir.Function(cls.module,
			ir.FunctionType( \
				ir.VoidType(), 
				[ir.PointerType(ir.IntType(TypeSizes.int))]), 
				"dispose")

		# Declare add_pointer_to_list
		IR_State.add_to_new_list_function = ir.Function(cls.module,
			ir.FunctionType( \
				ir.IntType(TypeSizes.int), 
				[ir.PointerType(ir.IntType(TypeSizes.int))]), 
				"add_to_list")

		# Declare delete_pointer_from_list
		IR_State.delete_from_list_function = ir.Function(cls.module,
			ir.FunctionType( \
				ir.IntType(TypeSizes.int), 
				[ir.PointerType(ir.IntType(TypeSizes.int))]), 
				"delete_from_list")

		# Declare pointers_in_the_same
		IR_State.check_compared_pointers_function = ir.Function(cls.module,
			ir.FunctionType( \
				ir.IntType(TypeSizes.int), 
				[ir.PointerType(ir.IntType(TypeSizes.int)), 
					ir.PointerType(ir.IntType(TypeSizes.int))]), 
				"pointers_in_the_same_matrix")

		# Declare delete_pointer_from_list
		IR_State.matrix_add_to_list_function = ir.Function(cls.module,
			ir.FunctionType( \
				ir.IntType(TypeSizes.int), 
				[ir.PointerType(ir.IntType(TypeSizes.int)), 
					ir.IntType(TypeSizes.int)]), 
				"Matrix_add_to_list")		
		
		# Declare delete_pointer_from_list
		IR_State.matrix_delete_from_list_function = ir.Function(cls.module,
			ir.FunctionType( \
				ir.IntType(TypeSizes.int), 
				[ir.PointerType(ir.IntType(TypeSizes.int))]), 
				"Matrix_delete_from_list")		
	##
	# The following set of 4 functions offer
	# the basic functionality for the stack of function maps
	# The function_stack_map is a stack with its top being the last list element
	##
	@classmethod
	def push_level_function_map(cls):
		#print cls.function_map
		cls.function_map.insert(0, {})	
	@classmethod
	def pop_level_function_map(cls):
		#print cls.function_map
		cls.function_map.pop(0)
	@classmethod
	def get_from_function_map(cls, name):
		# Check from the top to the bottom of the stack
		for stack_level in cls.function_map:
			if name in  stack_level:
				return stack_level[name]
		# TODO: Fix this error print
		return None
	@classmethod
	def add_to_function_map(cls, name, value):
		cls.function_map[0][name] = value	
	##
	# The following set of 4 functions offer
	# the basic functionality for the stack of eds_var_map
	# The eds_var_map is a stack with its top being the last list element
	##
	@classmethod
	def push_level_eds_var_map(cls):
		#print cls.eds_var_map
		#print cls.eds_var_map[0].keys()
		cls.eds_var_map.insert(0, {})	
	@classmethod
	def pop_level_eds_var_map(cls):
		#print cls.eds_var_map
		#print cls.eds_var_map[0].keys()
		cls.eds_var_map.pop(0)
	@classmethod
	def get_from_eds_var_map(cls, name):
		# Check from the top to the bottom of the stack
		for stack_level in cls.eds_var_map:
			if name in  stack_level:
				return stack_level[name][0]
		# TODO: Fix this error print
		#print "Variable with name: " + name + " was not found in the map"
		return None
	@classmethod
	def get_from_eds_var_map_ext(cls, name):
		# Check from the top to the bottom of the stack
		for stack_level in cls.eds_var_map:
			if name in  stack_level:
				return stack_level[name]
		# TODO: Fix this error print
		#print "Variable with name: " + name + " was not found in the map"
		return None
	@classmethod
	def add_to_eds_var_map(cls, name, value, depth):
		cls.eds_var_map[0][name] = [value, depth, -1]
	@classmethod
	def add_if_not_to_eds_var_map(cls, name, value, depth):
		#print "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
		#print "Depth: " + str(depth)
		#print "Length of stack: " + str(len(cls.eds_var_map))
		gep_index = -1
		if(depth < len(cls.eds_var_map)):
			gep_index = cls.eds_var_map[len(cls.eds_var_map) - depth][name][2]
		if not name in cls.eds_var_map[0]:
			 cls.eds_var_map[0][name] = [value, depth, gep_index]
	@classmethod
	def get_curr_level_of_eds_var_map(cls):
		new_dict = {}
		for key, val in cls.eds_var_map[0].iteritems():
			new_dict[key] = val[0]
		return new_dict
	@classmethod
	def get_curr_level_of_eds_var_map_ext(cls):
		return cls.eds_var_map[0]

	@classmethod 
	def update_function_unique_identifier(cls, sig):
		if (sig in cls.function_unique_identifiers):
			cls.function_unique_identifiers[sig] += 1
		else:
			cls.function_unique_identifiers[sig] = 0
		return cls.function_unique_identifiers[sig]
		
'''
A class that keeps all string constants so that they can
be referenced in the code_gen step
'''
class StringConstants(object):
	strings = {}


##
# Object that populates function_map
# It contains the function object and a metadata hash for any
# more information that we might need to store for development purposes
##
class Function_With_Metadata():
	def __init__(self, function):
		self.function = function
		self.metadata = {}
		self.scope_struct = None
	def set_metadata(self, name, data):
		self.metadata[name] = data
	def get_metadata(self, name):
		return self.metadata[name]
	def set_scope_struct(self, scope_struct):
		self.scope_struct = scope_struct
	def get_scope_struct(self):
		return self.scope_struct


