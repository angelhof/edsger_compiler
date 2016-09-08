from llvmlite import ir
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
	func = ir.Function(module, ir.FunctionType(ir.IntType(32), []), name="_global_decs_func")
	# Insert an unreachable block, and the main block
	block = func.append_basic_block(name="_global_decs")
	block_map["_global_decs"] = block
	# Basic IR module, the builder
	builder = ir.IRBuilder(block)
	@classmethod
	def rec_code_generation(cls, head):

		if(type(head) is list):
			for element in head:
				cls.rec_code_generation(element)
		else:
			head.code_gen()
	@classmethod
	def code_generation(cls, head):
		cls.rec_code_generation(head)
		
		with cls.builder.goto_block(cls.block):
			ret_result = ir.Constant(ir.IntType(32), 0)
			cls.builder.ret(ret_result)

		cls.terminate_blocks()

		print cls.module

		fp = open("test_asm", "w")
		fp.write(str(cls.module))	
	@classmethod
	def terminate_blocks(cls):
		array = [x for x in cls.unreachable_array if not x.is_terminated]
		for block in array:
			IR_State.builder.position_at_end(block)
			IR_State.builder.branch(block)
	##
	# The following set of 4 functions offer
	# the basic functionality for the stack of function maps
	# The function_stack_map is a stack with its top being the last list element
	##
	@classmethod
	def push_level_function_map(cls):
		print cls.function_map
		cls.function_map.insert(0, {})	
	@classmethod
	def pop_level_function_map(cls):
		print cls.function_map
		cls.function_map.pop(0)
	@classmethod
	def get_from_function_map(cls, name):
		# Check from the top to the bottom of the stack
		for stack_level in cls.function_map:
			if name in  stack_level:
				return stack_level[name]
		# TODO: Fix this error print
		print "Function with name: " + name + " was not found in the map"
		exit(1)
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
		print cls.eds_var_map
		print cls.eds_var_map[0].keys()
		cls.eds_var_map.insert(0, {})	
	@classmethod
	def pop_level_eds_var_map(cls):
		print cls.eds_var_map
		print cls.eds_var_map[0].keys()
		cls.eds_var_map.pop(0)
	@classmethod
	def get_from_eds_var_map(cls, name):
		# Check from the top to the bottom of the stack
		for stack_level in cls.eds_var_map:
			if name in  stack_level:
				return stack_level[name]
		# TODO: Fix this error print
		print "Variable with name: " + name + " was not found in the map"
		return None
	@classmethod
	def add_to_eds_var_map(cls, name, value):
		cls.eds_var_map[0][name] = value
	@classmethod
	def add_if_not_to_eds_var_map(cls, name, value):
		if not name in cls.eds_var_map[0]:
			 cls.eds_var_map[0][name] = value
	@classmethod
	def get_curr_level_of_eds_var_map(cls):
		return cls.eds_var_map[0]
		
	


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

