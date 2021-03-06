import warning_messages
import itertools
import operator
from copy import deepcopy
from llvmlite import ir
from edsger_ir import IR_State, \
					  Function_With_Metadata, \
					  StringConstants, \
					  TypeSizes, \
					  Extended_DoubleType

############
## Useful ##
############


def find_function_signature(identifier, type_list, extended_id = -1):
	'''
	Commented this because main will be 
	a compiler made function
	if(identifier == "main"):
		return identifier
	'''

	signature = identifier + "-" + str(len(type_list)) + reduce(operator.concat, map(lambda x: "-" + str(x), type_list) , "")
	if (not extended_id == -1):
		signature += "-"  + str(extended_id)
	return signature

'''
This function creates a binary operation node
that will then be code_gen()-ed
'''
def create_bin_op_for_whole_ass(whole_assignment):

	old_op = whole_assignment.operator
	old_exp1 = whole_assignment.exp1
	old_exp2 = whole_assignment.exp2
	
	new_operator = Operator(old_op.lineno, old_op.operator[0], True)
	new_binary_operation = Node_binary_operation(new_operator, 
			old_exp1, old_exp2, old_op.lineno)
	
	return new_binary_operation


def unflatten_previous_scope():
	tuples = [(x, y[0], y[1], y[2]) for x,y in IR_State.eds_var_map[1].iteritems()]
	# Debug
	#print "GAMW"
	#print tuples
	result_dict = {}
	for tuple in [x for x in tuples if not x[0][:len("_current_scope_")] ==
								"_current_scope_"]:
		if tuple[2] not in result_dict:
			result_dict[tuple[2]] = [(tuple[0], tuple[1], tuple[3])]
		else:
			result_dict[tuple[2]].append((tuple[0], tuple[1], tuple[3]))
	for scope in result_dict:
		result_dict[scope].sort()
	return result_dict

def create_unreachable():
	unreachable = IR_State.builder.append_basic_block("_unreachable")
	IR_State.unreachable_array.append(unreachable)
	IR_State.builder.position_at_start(unreachable)



def enlist(element):
	if(not element):
		return []
	if not (type(element) is list):
		return [element]
	return element


'''
Checks if the expression on the left is an L-Val
'''
def new_l_val_check(head):
	# Debug
	#print head
	if(isinstance(head, Variable)):
		if(head.array_expr is not None):
			return False
		else:
			return True
	elif(isinstance(head, Parenthesial_expression)):
		return new_l_val_check(head.expr)
	elif (isinstance(head, Array_Deref)):
		if(head.left_expression.type.pointer > 0):
			return True
	elif (isinstance(head, Node_unary_operation)):
		if( head.operator.operator == "u*"):
			if(head.exp.type.pointer > 0):
				return True
	# Catcher False
	return False

'''
Transforms our type instance in LLVM IR type
'''
def transform_type_basic(our_type):
	our_type_name = our_type.type
	our_type_pointer = our_type.pointer
	
	


	# If the variable is primitive
	var_size = 0
	if our_type.isGenBool():
		var_size = TypeSizes.bool
		var_type = ir.IntType(var_size)
	elif our_type.isGenChar():
		var_size = TypeSizes.char
		var_type = ir.IntType(var_size)
	elif our_type.isGenInt():
		var_size = TypeSizes.int
		var_type = ir.IntType(var_size)
	elif our_type.isGenDouble():
		var_size = TypeSizes.double
		var_type = Extended_DoubleType()
	else:
		var_type = ir.VoidType()

	# If it is not primitive
	if not our_type.isPrimitive():
		# If its an array , declare it as one less pointer
		pointer_number = our_type_pointer
		
		for i in range(pointer_number):
			var_type = ir.PointerType(var_type) 

		# It could be a function or a variable

	return var_type


'''
Transforms the variable type into an LLVM type instance and it returns
Returns (LLVM_Type, Array_Size (Only useful for allocation))
'''
def transform_type(var):

	array_size = 1

	our_type = var.type
	
	var_type = transform_type_basic(our_type)   

	if(isinstance(var, Variable)):
		# If it is an array
		if var.array_expr is not None:
			# Evaluate the expression 
			# TODO: For now it only works for constant
			array_size = int(var.array_expr.value)


	return (var_type, array_size)
'''
'''
def retrieve_previous_scope_structs(llvm_scope_struct, scope_structs_names):
	#print "Retrieve function"
	#print llvm_scope_struct
	#print scope_structs_names
	if( len(scope_structs_names) == 0):
		return
	else:
		curr_name = scope_structs_names[-1]
		names_tail = scope_structs_names[:-1]



		curr_struct = 	IR_State.builder.gep(
						llvm_scope_struct ,
						[ ir.Constant(ir.IntType(32), 0)
						#, ir.Constant(ir.IntType(32), 0)
						] ,
						name=curr_name)

		next_struct = None
		if(len(names_tail) > 0):
			next_struct_temp = 	IR_State.builder.gep(
							llvm_scope_struct ,
							[ ir.Constant(ir.IntType(32), 0)
							, ir.Constant(ir.IntType(32), 0)
							] ,
							name=curr_name+"_next_ptr")
			next_struct = 	IR_State.builder.load(
							next_struct_temp ,
							name=curr_name+"_next")
			'''
			OLD FKIN WRONG WAY OF DOING THIS :')
			next_struct = 	IR_State.builder.gep(
							llvm_scope_struct ,
							[ ir.Constant(ir.IntType(32), 0)
							, ir.Constant(ir.IntType(32), 0)
							, ir.Constant(ir.IntType(32), 0)
							] ,
							name=curr_name+"_next")
			'''

		'''
		Used to debug this shit
		print "============Arazoume edw ola popa============"
		print curr_name
		print names_tail
		print "--Current: " + str(curr_struct.type)
		try:
			print "--Next: " + str(next_struct.type)
		except:
			pass
		print "--Previous: " + str(llvm_scope_struct.type)
		print "============================================="
		'''

		IR_State.add_to_eds_var_map(curr_name, curr_struct, 
					len(IR_State.eds_var_map))

		retrieve_previous_scope_structs(next_struct, names_tail)

'''
Creates the scope struct, allocates space, and gives the pointers
the variable addresses
'''
def create_scope_struct():
	'''
		TODO:
		- Meta to declaration olwn twn metablhtwn 
		  exoume th dunatothta na dhmiourghsoume kai
		  to scope struct tou epipedou
		- Briskoume ton tupo tou
		- To kanoume allocate
		- Dinoume stous deiktes tou tis theseis twn metablitwn
		- To kalo einai oti an den uparxoun alles sunarthseis
		  pio mesa pou an to kaloun feugei sta optimizations
		  ara den mas endiaferei h apodosh tou
	'''
	#print "Ti theloume apo edw"
	#print IR_State.eds_var_map
	# We sort them so that they have some kind of order
	current_scope = IR_State.get_curr_level_of_eds_var_map()
	current_scope_keys = 	[x for x in sorted(
						 	current_scope.keys()) 
								if not x[:len("_current_scope_")] ==
								"_current_scope_"]
	#print current_scope_keys

	all_previous_scope_keys = 	[x for x in 
						 		current_scope.keys() 
									if x[:len("_current_scope_")] ==
									"_current_scope_"]

	# Pernoume ton arithmo tou teleutaiou scope
	try:
		previous_scope_key = str(sorted(map(lambda x: int(x.split("_")[-1]) , 
				all_previous_scope_keys))[-1])
	except:
		previous_scope_key = None

	#print previous_scope_key

	current_scope_types = []
	# Prosthese ton tupo tou prohgoumenou struct
	if previous_scope_key is not None:
		#print current_scope["_current_scope_"+previous_scope_key].type
		current_scope_types.append(current_scope["_current_scope_"+previous_scope_key].type)

	# Prosthese tous tupous twn metablhtwn tou twrinou scope
	for var_in_curr_scope_key in current_scope_keys:
		var_in_curr_scope = current_scope[var_in_curr_scope_key]
		current_scope_types.append(var_in_curr_scope.type)
	'''
	TODO: 7/10/2016
	Oxi append ta keys alla append to prohgoumeno scope
	kai ta twrina variables kai arguments 
	'''

	
	scope_depth = len(IR_State.eds_var_map)
	# Add the scope struct as the last argument of the function
	scope_struct_type = ir.LiteralStructType(current_scope_types)
	allocated_scope_struct = IR_State.builder.alloca( 
				scope_struct_type,  
				name="_current_scope_"+str(scope_depth) )
	IR_State.add_to_eds_var_map("_current_scope_"+str(scope_depth)
				, allocated_scope_struct, scope_depth)
	#print allocated_scope_struct
	'''
	Note: Check that the IntType indice below is 32 
		  not regarding the int size because of llvm
		  limitation
		  ! To idio sumbainei kai sto function class 
	'''
	if previous_scope_key is not None:
		temp_key = "_current_scope_"+previous_scope_key
		current_scope_keys.insert(0, temp_key)

	# Add the pointer values to the struct
	for i in range(len(current_scope_keys)):
		struct_element = IR_State.builder.gep(
					allocated_scope_struct ,
					[ ir.Constant(ir.IntType(32), 0)
					, ir.Constant(ir.IntType(32), i) 
					] ,
					name="_"+current_scope_keys[i] )
		#print struct_element, struct_element.type

		saved_element = IR_State.builder.store(
					current_scope[current_scope_keys[i]],
					struct_element )
		#print saved_element, saved_element.type

		IR_State.eds_var_map[0][current_scope_keys[i]][2] = i
		
		#print "---------------------AAAAAAAAAAAAAAAAAAAAA---------------"
		#print IR_State.eds_var_map[0][current_scope_keys[i]]


## All useful classes
class AST(object):
	head = None
	@classmethod
	def print_tree(cls, outstream):
		cls.rec_print_tree( cls.head, 0, outstream);
	@classmethod
	def rec_print_tree(cls,head,tabs, outstream):
		if not (type(head) is list):
			outstream.write(tabs*"\t"+str(head)+"\n")

		for element in head:
			if type(head) is list:
				cls.rec_print_tree(element,tabs, outstream)
			else:
				cls.rec_print_tree(element,tabs+1, outstream)


# State class
class Program_State(object):
	variable_scope_stack = []
	function_scope_stack = []
	@classmethod
	def push(cls, scope):
		cls.variable_scope_stack.insert(0, scope)
		cls.function_scope_stack.insert(0, scope)
	@classmethod
	def pop(cls):
		return ( cls.variable_scope_stack.pop(0), cls.function_scope_stack.pop(0) ) 
	@classmethod
	def add_variable_to_curr_scope(cls,identifier):
		if(identifier.name in cls.variable_scope_stack[0]):
			print warning_messages.redeclaration(identifier.name, str(cls.variable_scope_stack[0][identifier.name].lineno))
		cls.variable_scope_stack[0][identifier.name] = identifier
	@classmethod
	def add_function_to_curr_scope(cls,identifier):
		if(identifier.get_signature() in cls.function_scope_stack[0]):
			print warning_messages.redeclaration(identifier.name, str(cls.function_scope_stack[0][identifier.get_signature()].lineno))
		cls.function_scope_stack[0][identifier.get_signature()] = identifier
	@classmethod
	def variable_in_scope(cls,identifier):
		for scope in cls.variable_scope_stack:
			if(identifier in scope):
				return scope[identifier]
		return None
	@classmethod
	def function_in_scope(cls,identifier, type_list):
		signature = find_function_signature(identifier, type_list)
		for scope in cls.function_scope_stack:
			if(signature in scope):
				return scope[signature]
		return None
	@classmethod
	def function_in_top_scope(cls,identifier, type_list):
		signature = find_function_signature(identifier, type_list)
		if(signature in cls.function_scope_stack[0]):
			return cls.function_scope_stack[0][signature]
		return None

class Loop_Stack(object):
	stack = []
	loop_names = {}
	@classmethod
	def push(cls, loop, lineno):
		if(loop in cls.loop_names):
			print warning_messages.loop_name_exists(loop, str(lineno))
			exit(1)
		cls.loop_names[loop] = 1
		cls.stack.insert(0, loop)
	@classmethod
	def pop(cls):
		return cls.stack.pop(0) 
	@classmethod
	def isEmpty(cls):
		return not cls.stack
	@classmethod
	def exists(cls, name):
		for loop in cls.stack:
			if(loop == name):
				return loop
		return None 
	@classmethod
	def loop_name_creator(cls):
		for i in itertools.count():
			if(not (("_le_loop" + str(i)) in cls.loop_names)):
				yield "_le_loop" + str(i)

class Function_Stack(object):
	stack = []
	@classmethod
	def push(cls, function, lineno):
		cls.stack.insert(0, function)
	@classmethod
	def pop(cls):
		return cls.stack.pop(0) 
	@classmethod
	def isEmpty(cls):
		return not cls.stack
	
# Expression class
class Expr(): 
	def __init__(self,lineno, e_type):
		self.type = e_type
		self.lineno = lineno
		# TODO : Maybe fill here with the sons of the expression
		# TODO : So that we can have the full tree in ht end 
	def __iter__(self):
		rlist = []
		return iter(rlist)
	def code_gen(self):
		pass
        def code_gen1(self, expected_type):
                return self.code_gen()

# Type class
class Type():
	def __init__(self,constant_type,pointer=0):
		self.type = constant_type
		self.pointer = pointer
	def similar(self, other):

		return self.__eq__(other)
		'''
		# Old Policy
		if((other.isNull() and not self.isPrimitive()) or 
		   (self.isNull() and not other.isPrimitive())):
			return True
		return (isinstance(other, self.__class__) and self.type == other.type and (self.pointer > 0) == (other.pointer > 0))
		'''
	def __eq__(self, other):
		return (isinstance(other, self.__class__) and self.type == other.type and self.pointer == other.pointer )
	#Select among 2 policies 
	#C-Like (self.type == other.type) and ()
	#TODO FIX ME.. Maybe put Array in Variable Class
	def __ne__(self, other):
		return not self.__eq__(other)
	def __str__(self):
		return str(self.type) + ("_pointer" * self.pointer)
	def copyfrom(self, other):  
		self.type=other.type
		self.pointer=other.pointer
	def __iter__(self):
		rlist = [].__iter__(self)
		return iter(rlist)
	def isGenBool(self):
		return self.type == "bool"
	def isGenInt(self):
		return self.type == "int"
	def isGenChar(self):
		return self.type == "char"
	def isGenDouble(self):
		return self.type == "double"
	def isBool(self):
		return self.type == "bool" and self.isPrimitive()
	def isInt(self):
		return self.type == "int" and self.isPrimitive()
	def isChar(self):
		return self.type == "char" and self.isPrimitive()
	def isDouble(self):
		return self.type == "double" and self.isPrimitive() 
	def isPrimitive(self):
		return self.pointer == 0 
	def isVoid(self):
		return self.type == "void"
	def isNull(self):
		return self.type == "null"
	def defaultValue(self):
		ret_val = None
		if(self.isInt()):
			ret_val = ir.Constant(ir.IntType(TypeSizes.int), 
					0)
		elif(self.isChar()):
			ret_val = ir.Constant(ir.IntType(TypeSizes.char), 
					0)
		elif(self.isBool()):
			ret_val = ir.Constant(ir.IntType(TypeSizes.bool), 
					0)
		elif(self.isDouble()):
			ret_val = ir.Constant(Extended_DoubleType(), 
					0)
		return ret_val

# Constant value
class Constant_Value(Expr):
	def __init__(self,lineno,constant_type,value):
		if(constant_type == "string"):
			self.type = Type("char", 1)
			# Save the value 
			StringConstants.strings[value] = None
		else: 
			self.type = Type(constant_type)
		self.value = value
		self.lineno = lineno
		#print self.value
	def __str__(self):
		return "Constant_Value( " + str(self.type) + ", " + str(self.value) + " )"
	def code_gen(self):
		## --- WORK IN PROGRESS ---
		## TODO: Make checks for types
		if self.type.isInt():
			dest = ir.Constant(ir.IntType(TypeSizes.int), self.value)
		elif self.type.isDouble():
			dest = ir.Constant(Extended_DoubleType(), self.value)
		elif self.type.isBool():
			dest = ir.Constant(ir.IntType(TypeSizes.bool), self.value)
		elif self.type.isChar():
			# Decode the character and save it
			#print self.value
			#print ord(self.value[1:-1].decode("string_escape"))
			dest = ir.Constant(ir.IntType(TypeSizes.char), ord(self.value[1:-1].decode("string_escape")))
		elif self.type.isGenChar() and self.type.pointer == 1:
			
			# Find the string in the dictionary
			global_string = StringConstants.strings[self.value]
			#print global_string
			dest = IR_State.builder.bitcast(global_string, 
					ir.PointerType(ir.IntType(TypeSizes.char))  )
		elif self.type.isNull():
			dest = ir.Constant(ir.IntType(TypeSizes.int), None)
		else:
			print"Exit like we got a big problem :'("
			exit(1)
		return dest
        def code_gen1(self, expected_type):
                print "Expected Type:", expected_type
                if self.type.isNull():
                        ir_type = transform_type_basic(expected_type)
                        dest = ir.Constant(ir_type, None)
                else:
                        dest = self.code_gen()
                return dest

# Identifier
class Identifier(Expr):
	def __init__(self,lineno,name):
		self.name = name
		self.lineno = lineno

	def __str__(self):
		return "Identifier( " + str(self.name) + " )" 


class Variable(Identifier):
	def __init__(self,lineno,vtype, name, array_expr = None):
		self.type = vtype
		self.name = name
		self.lineno = lineno
		self.array_expr = array_expr
		self.isGlobal = False

	def declare_type(self,vtype):
		self.type = deepcopy(vtype)

	def __str__(self):
		return "Variable( " + str(self.name)  + " , " + str(self.type) + " )" + (" [ " + str(self.array_expr) + " ] " )*(not self.array_expr is None) 

	def code_gen(self):
		var_name = self.name 
		name = "_temp"+str(IR_State.var_counter)

		#print IR_State.eds_var_map

		ptr = IR_State.get_from_eds_var_map(var_name)

		if(not IR_State.left_side):     
			dest = IR_State.builder.load(ptr, name=name)
			IR_State.var_map.append(dest) 
			IR_State.var_counter += 1
			return dest
		else:
			return ptr

	def code_gen_decl(self):

		our_name = self.name 

		type_and_size = transform_type(self)
		
		var_type = type_and_size[0]
		array_size = type_and_size[1]
		


		if(self.isGlobal):


			'''
			TODO:
			- FTiaxnw ta global arrays ws exhs
			  Ftiaxnw dio values, ena me to array
			  kai ena me otn pointer tou
			  opws kaname sto variable.code_gen_decl()
			 '''
			if(array_size > 1):
				# Declare the array space and the  pointer space
				arr_type = ir.ArrayType(var_type.pointee, array_size)
				arr_vals = ir.GlobalVariable(IR_State.module, 
							arr_type, 
							our_name+"+array_vals")
				arr_vals.linkage = "private"

				ret_val = ir.GlobalVariable(IR_State.module, 
							var_type, 
							our_name)

				# Add to the array list
				ir_arr_size = ir.Constant(ir.IntType(TypeSizes.int), array_size*TypeSizes.int/8)
				bitcasted = IR_State.builder.bitcast(arr_vals, 
							ir.PointerType(ir.IntType(TypeSizes.int)),
							name=our_name+"-bitcasted-kalesma-pinaka")
				add_to_list = IR_State.builder.call(IR_State.matrix_add_to_list_function, 
						[bitcasted, ir_arr_size], 
						name=our_name+"-kalesma-pinaka")
				
				# Assign the pointer to the array space
				with IR_State.builder.goto_block(IR_State.block):
					arr_vals_converted = IR_State. \
						builder.bitcast(arr_vals, var_type)
					point_to_vals = IR_State.builder.store(
						arr_vals_converted , 
						ret_val)

			else:
				ret_val = ir.GlobalVariable(IR_State.module, 
							var_type, 
							our_name)   
			ret_val.linkage = "private"
			

			
			IR_State.add_to_eds_var_map(our_name, ret_val, 
						len(IR_State.eds_var_map))
		else:
			# If it an array we have to do 2 steps
			if(array_size > 1):
				arr_vals = IR_State.builder.alloca( var_type.pointee, 
						size=array_size, name=our_name+"+array_vals" )
				ret_val = IR_State.builder.alloca( var_type, 
						size=1, name=our_name )
				point_to_vals = IR_State.builder.store(
						arr_vals , 
						ret_val)

				# Addare sth lista pinakwn
				ir_arr_size = ir.Constant(ir.IntType(TypeSizes.int), array_size*TypeSizes.int/8)
				bitcasted = IR_State.builder.bitcast(arr_vals, 
							ir.PointerType(ir.IntType(TypeSizes.int)),
							name=our_name+"-bitcasted-kalesma-pinaka")
				add_to_list = IR_State.builder.call(IR_State.matrix_add_to_list_function, 
						[bitcasted, ir_arr_size], 
						name=our_name+"-kalesma-pinaka")
			
			else:
				ret_val = IR_State.builder.alloca( var_type, 
						size=array_size, name=our_name )
			IR_State.add_to_eds_var_map(our_name, ret_val, 
						len(IR_State.eds_var_map))
		return ret_val




class Parameter(Variable):
	def __init__(self,lineno,vtype, name, byref=0):
		self.type = vtype
		self.name = name
		self.lineno = lineno
		self.byref = byref
		'''
		TODO: Fix !! Should parameters be arrays or not?
		'''
		self.array_expr = None

	def __str__(self):
		return "Parameter( " + str(self.name) + " , " + str(self.byref) + " " + str(self.type) + " )"   

	def code_gen(self):
		var_name = self.name 
		# If the variable is passed by value we just evaluate it
		# Else we have to evaluate its 
		
		'''OLD WAY TODELETE
		if( self.byref == 0 and False):
			param_value = IR_State.get_from_eds_var_map(var_name)
		else:
		'''
		ptr = IR_State.get_from_eds_var_map(var_name)
		if(not IR_State.left_side):     
			param_value = IR_State.builder.load(ptr, name=self.name)
			IR_State.var_map.append(param_value) 
			IR_State.var_counter += 1
			return param_value
		else:
			return ptr

		return param_value
	def code_gen_decl(self):
		# If it is byval
		if( self.byref == 0 ):
			actual_parameter = IR_State.get_from_eds_var_map_ext(self.name)
			allocated_parameter = IR_State.builder.alloca(actual_parameter[0].type, 
							name=self.name+"+parameter")
			IR_State.builder.store(actual_parameter[0], 
							allocated_parameter)
			IR_State.add_to_eds_var_map(self.name, 
							allocated_parameter, 
							actual_parameter[1])




class Function(Identifier):
	def __init__(self,lineno,r_type, name, parameters = [], declarations = [], statements = []):
		self.type = r_type
		self.name = name
		self.parameters = list(parameters)
		self.lineno = lineno
		self.declarations = declarations
                self.statements = statements
		self.scope_level = None
		self.uid = -1
                self.is_declaration = True


	def get_signature(self):
		return find_function_signature(self.name, map(lambda x: x.type, self.parameters) )

	def get_extended_signature(self):
		return  find_function_signature(self.name, map(lambda x: x.type, self.parameters), self.uid) 

	# Parameters will be a list of variables
	def add_parameter(self,parameter):
		self.parameters.append(parameter) 

        def set_declaration(self, is_declaration):
                self.is_declaration = is_declaration
                
	def __str__(self):
		return str(self.type) + " function " + self.name + "(" + str(map(str,self.parameters)) + ")" 
	def __iter__(self):
		rlist = self.declarations + [Delimiter("Statements")] +  self.statements 
		return iter(rlist)
	
	def code_gen(self):
		return self.code_gen_decl()

	def code_gen_decl(self):

		# TODO: Put also the pointer
		# Find the arguments types
		function_arg_types = []
		for param in self.parameters:
			
			type_and_size = transform_type(param)

			arg_type = type_and_size[0]

			if param.byref == 1:
				arg_type = arg_type.as_pointer()
			function_arg_types.append(arg_type)


		#print self
		#print "Stack"
		#print IR_State.eds_var_map

		'''
		TODO: 7/10/2016
		Bres to sosto _current_scope_ me bash to level tou
		PX. "_current_scope_2"
		'''
		scope_depth = len(IR_State.eds_var_map)
		scope_struct = IR_State.get_from_eds_var_map("_current_scope_"+str(scope_depth))
		# An einai None prepei na kna wkati? 
		if scope_struct is not None:    
			function_arg_types.append(scope_struct.type)
			# DEBUG
			#print function_arg_types


		# If we are getting for the first time in declaration or definiton
		# we should check the uid if it has been initialized or otherwise we should do it here
		if(self.uid == -1):
			self.uid = IR_State.update_function_unique_identifier(self.get_signature())
			if(self.get_signature()=="main-0" and  scope_depth == 1):
				IR_State.main_anchor = self.get_extended_signature()

		'''
		Elegxoume an uparxei h sunarthsh hdh declared
		kai thn kanoume bind me auth
		'''

		# function_with_metadata = IR_State.get_from_function_map(self.name)
		# We had the simple signature checking but now we 
		# will need the extended with the id included
		function_with_metadata = IR_State.get_from_function_map(self.get_extended_signature())
		if(function_with_metadata is not None):
			function = function_with_metadata.function
		else:
			# Find the return type
			ret_type = transform_type(self)[0]

			# Create a new function and and save it at its map 
			function_type = ir.FunctionType(ret_type, function_arg_types)
			function = ir.Function(IR_State.module, function_type, name=self.get_extended_signature())			
			# THe original command has been kept before testing
			# IR_State.function_map[self.name] = function
			function_with_metadata = Function_With_Metadata(function)
			function_with_metadata.set_scope_struct(scope_struct)
			IR_State.add_to_function_map(self.get_extended_signature(), function_with_metadata)


			# Store as function metadata the byref
			# We store whether the arguments are byref so that
			# We can load them properly afterwards
			byref_array = []
			for i in range(len(self.parameters)):
				eds_param_byref = self.parameters[i].byref
				llvm_param = function.args[i]

				if eds_param_byref == 0:
					byref_array.append(self.parameters[i].name + "->byval")
				else:
					byref_array.append(self.parameters[i].name + "->byref")
			function_with_metadata.set_metadata("byref", " ".join(byref_array))


		# If the function is not declared but it is defined it should pass this control only once
                if not self.is_declaration:
		# if(len(self.declarations)>0 or len(self.statements)>0):

			# Anoixe kainourgio scope level
			IR_State.push_level_function_map()
			IR_State.push_level_eds_var_map()

			# Get a new block name and Crete a new block
			block_name = "_block" + str(IR_State.block_counter)
			block = function.append_basic_block(name=block_name)
			IR_State.block_map[block_name] = block
			IR_State.block_counter += 1

			# Map the arguments to their real names
			for i in range(len(self.parameters)):
				eds_param_name = self.parameters[i].name
				llvm_param = function.args[i]
				
				IR_State.add_to_eds_var_map(eds_param_name, llvm_param, 
							len(IR_State.eds_var_map))



			# Evaluate the function declarations and statements
			with IR_State.builder.goto_block(block):

				# Kane prwta ola ta variable declarations
				# Gia na mporesei na dhmiourghsei to scope
				# struct
				variable_decls = [x for x in enlist(
						self.declarations) if isinstance(x, Variable)]
				function_decls = [x for x in enlist(
						self.declarations) if isinstance(x, Function)]
				
				for element in self.parameters:
					element.code_gen_decl()

				for element in variable_decls:
					element.code_gen_decl()
				

				'''
				Map the variables to their real value
				'''
				previous_scope_frame = IR_State.eds_var_map[1]
				previous_scope_frame_keys = [x for x in sorted(
						previous_scope_frame.keys()) 
							if not x[:len("_current_scope_")] ==
							"_current_scope_"]
				#print "Prohgoumeno"
				#print previous_scope_frame_keys

				#print "Variable stack prin to 'declaration' paliwn scope"
				#print previous_scope_frame
				previous_scope_structs = [x for x in sorted(
						previous_scope_frame.keys()) 
							if x[:len("_current_scope_")] ==
							"_current_scope_"]
				#print previous_scope_structs
				if( len(previous_scope_structs) > 0):
					retrieve_previous_scope_structs(function.args[-1], previous_scope_structs)

				# Create the current scope_struct
				create_scope_struct()

				# Kratame to scope level gia to function call
				# kai to scope struct
				self.scope_level = len(IR_State.eds_var_map)
				'''
				- An to megethos eiani 2 shmainei oti 
				  den uparxei pio prin giati eimaste global
				- Ebala to idio sto function call
				TODO: Elegxw an isxuei auto 
				'''
				if( len(IR_State.eds_var_map) > 2):
					
					'''
					TODO: 7/10/2016
					Auto skaei kai prepei na kanw swsta to anoigma twn metablitwn
					'''
					#print "Variable Retrieval"
					#print previous_scope_frame_keys
					#print [(x, y[1]) for x,y in IR_State.eds_var_map[1].iteritems()]
					#print IR_State.eds_var_map
					#print function.args[-1]

					previous_variables_and_depth = unflatten_previous_scope()

					#print previous_variables_and_depth

					
					for level in previous_variables_and_depth:
						for i in range(0,len(previous_variables_and_depth[level])):
							key = previous_variables_and_depth[level][i][0]
							value = previous_variables_and_depth[level][i][1]
							gep_index = previous_variables_and_depth[level][i][2]
							if( gep_index < 0 ):
								gep_index = i
							
							containing_scope = IR_State.get_from_eds_var_map( \
									"_current_scope_" + str(level))

							'''
							print "====TO SOSTO TO SCOPE===="
							print containing_scope.function.name
							print previous_variables_and_depth[level]
							print key, value
							print IR_State.eds_var_map[0]
							#print i
							print level
							print gep_index
							'''
							if(level == 2 ):
								scope_variable_address = IR_State.builder.gep(
										containing_scope ,
										[ ir.Constant(ir.IntType(32), 0)
										, ir.Constant(ir.IntType(32), gep_index) 
										] ,
										name="__"+key+"+ptr_in_struct" )
							else:
								scope_variable_address = IR_State.builder.gep(
										containing_scope ,
										[ ir.Constant(ir.IntType(32), 0)
										, ir.Constant(ir.IntType(32), i+1) 
										] ,
										name="__"+key+"+ptr_in_struct" )
							
							#print scope_variable_address
							#print "=========================="
							
							scope_variable = IR_State.builder.load(
									scope_variable_address,
									name="___"+key+"+val_in_struct" )
							IR_State.add_if_not_to_eds_var_map(key, scope_variable,
										level)


				

				for element in function_decls:
                                        element.code_gen_decl()
				

				for element in enlist(self.statements):
					element.code_gen()

				# Termatise tis void sunarthseis
				if (self.type.isVoid()):
					IR_State.builder.ret_void()

			# Kleise to scope level We are out of the "with" block 
			IR_State.pop_level_function_map()
			IR_State.pop_level_eds_var_map()


		

class If_Statement():
	def __init__(self, lineno, predicate, then_stmts, else_stmts):
		if(not predicate.type.isBool()):
			print warning_messages.predicate_not_bool(str(lineno))
			exit(1)
		self.lineno = lineno
		self.predicate = predicate
		self.then_stmts = then_stmts
		self.else_stmts = else_stmts
	def __str__(self):
		return "If ( " + str(self.predicate) + " ) then stmts else stmts"
	def __iter__(self):
		rlist = [self.predicate] + [Delimiter("Then_Stmts")] + enlist(self.then_stmts) + [Delimiter("Else_Stmts")] + enlist(self.else_stmts) 
		return iter(rlist)
	def code_gen(self):

		predicate = self.predicate.code_gen()

		## TODO: Maybe fix the bug with return by using if _then and if_else
		if(self.else_stmts):
			with IR_State.builder.if_else(predicate) as (then, otherwise):
				with then:
					# emit instructions for when the predicate is true
					for stmt in enlist(self.then_stmts):
						stmt.code_gen()
				with otherwise:
					# emit instructions for when the predicate is false
					for stmt in enlist(self.else_stmts):
						stmt.code_gen()
		else:
			with IR_State.builder.if_then(predicate) as then:
				# emit instructions for when the predicate is true
				for stmt in enlist(self.then_stmts):
					stmt.code_gen()
	
		IR_State.unreachable_array.append(IR_State.builder.block)


class For_Statement():
	def __init__(self, lineno, expression1, expression2, expression3, stmts, name):
		self.lineno = lineno
		self.expression1 = expression1
		self.expression2 = expression2
		self.expression3 = expression3
		self.stmts = stmts
		self.name = name
	def __str__(self):
		return "For Statement: " + self.name + " ( ; ; ): "
	def __iter__(self):
		rlist = [self.expression1] + [self.expression2] + [self.expression3] + [Delimiter("Statements")] + enlist(self.stmts) 
		return iter(filter(lambda x: x is not None, rlist))
	def code_gen(self):

		loop_name = self.name
		#loop_name = self.name[4:]

		# Create the essential loop blocks
		pred_loop_block = IR_State.builder.append_basic_block(loop_name + ".pred")
		loop_block = IR_State.builder.append_basic_block(loop_name)
		loop_end_block = IR_State.builder.append_basic_block(loop_name + ".loop_end")
		exit_loop_block = IR_State.builder.append_basic_block(loop_name + ".exit")

		# Save the blocks in the map
		IR_State.block_map[loop_name + ".pred"] = pred_loop_block
		IR_State.block_map[loop_name] = loop_block
		IR_State.block_map[loop_name + ".loop_end"] = loop_end_block
		IR_State.block_map[loop_name + ".exit"] = exit_loop_block

		exp1 = None
		if(self.expression1 is not None):
			exp1 = self.expression1.code_gen()
		IR_State.builder.branch(pred_loop_block)

		with IR_State.builder.goto_block(pred_loop_block):
			# emit instructions for the pred_loop_block
			predicate = ir.Constant(ir.IntType(TypeSizes.bool), True)
			if(self.expression2 is not None):
				predicate = self.expression2.code_gen()

			IR_State.builder.cbranch(predicate, loop_block, exit_loop_block)


		with IR_State.builder.goto_block(loop_block):
			# emit instructions for the loop_block
			for stmt in enlist(self.stmts):
				stmt.code_gen()
			IR_State.builder.branch(loop_end_block)

		with IR_State.builder.goto_block(loop_end_block):
			exp3 = None
			if(self.expression3 is not None):
				exp3 = self.expression3.code_gen()

			IR_State.builder.branch(pred_loop_block)

		IR_State.builder.position_at_end(exit_loop_block)




class Break():
	def __init__(self,lineno, name):
		self.lineno = lineno
		self.name = name
	def __str__(self):
		return "Break at: " + self.name
	def __iter__(self):
		rlist = []
		return iter(rlist)
	def code_gen(self):
		
		loop_block = IR_State.block_map[self.name + ".exit"]
		IR_State.builder.branch(loop_block)
		create_unreachable()
		


class Continue():
	def __init__(self,lineno, name):
		self.lineno = lineno
		self.name = name
	def __str__(self):
		return "Continue at: " + self.name
	def __iter__(self):
		rlist = []
		return iter(rlist)
	def code_gen(self):
		
		loop_block = IR_State.block_map[self.name + ".loop_end"]
		IR_State.builder.branch(loop_block)
		create_unreachable()

class Operator():
	#Read the description below in order to get an idea 
	#about what the heck we are coding
	dictionary={
	"/":[0, 3, 0, 3],
	"%":[0, 3, 3, 3],
	"b+":[0, 3, 0, 3],
	"b-":[0, 3, 0, 3], 
	"u+":[0, 3, 0, 3],
	"u-":[0, 3, 0, 3],
	"<":[2, 2, 2, 2],
	">":[2, 2, 2, 2],
	"<=":[2, 2, 2, 2],
	">=":[2, 2, 2, 2],
	"==":[2, 2, 2, 2],
	"!=":[2, 2, 2, 2],
	"||":[3, 3, 3, 0],
	"&&":[3, 3, 3, 0],
	",":[2, 2, 2, 2],
	"b*":[0, 3, 0, 3],
	"u*":[1, 1, 1, 1],
	"&":[2, 2, 2, 2],
	"!":[3, 3, 3, 0],
	"++":[2, 1, 2, 1],
	"--":[2, 1, 2, 1],
	"=":[2, 2, 2, 2],
	"+=":[2, 2, 2, 2],
	"-=":[2, 2, 2, 2],
	"*=":[2, 2, 2, 2],
	"/=":[2, 2, 2, 2],
	"%=":[2, 2, 2, 2]
	}
	mapper={"int":0,"char":1,"double":2,"bool":3}
	# every operator has a list of 4 values (int, char,double,bool)
	#and each one of them has a value {0, 1, 2, 3} which declares
	#the efunctionality of the operator so respectively we have:
	# 0 ==> only for primitive
	# 1 ==> only for pointers
	# 2 ==> valid for both the above
	# 3 ==> non valid
	def __init__(self, lineno, operator, binar):
		if(operator=="+" or operator=="-" or operator=="*"):
			if(binar):
				curoperator="b"+operator
			else:
				curoperator="u"+operator
		else:
			curoperator=operator
		self.validtypes=self.dictionary[curoperator]
		self.lineno=lineno
		self.operator=curoperator
		self.binar=binar

	def __str__(self):
		return "OP: "+str(self.operator) + (" binary " * self.binar) 

	def unary_typecheck(self,exp_type):

		valid_list=self.validtypes
		exp_checking_type=exp_type.type
		exp_pointer = exp_type.pointer
		index=self.mapper[exp_checking_type]
		#if is not a pointer check if it is valid
		if(exp_pointer==0):
			if(valid_list[index]==0 or valid_list[index]==2):
				return True
			else: #its not valid raise an ERROR message
				return False
		else: #check if its valid if it is a pointer of some deepness
			if(valid_list[index]==1 or valid_list[index]==2):
				return True
			else: #its not valid raise an ERROR message
				return False

	def binary_typecheck(self,exp1_type,exp2_type):
		
		#print "Typecheck " + str(self)
		#print exp1_type, exp2_type
		#check the binary typechecking practically the same type for both expressions all except COMMA 
		if(self.operator == "b+" or self.operator == "b-"): # + or - binary
			if(exp1_type.isInt()):
				if(exp2_type.type == "int" or exp2_type.pointer != 0):
					return True
				else:
					return False
			elif(exp2_type.isInt()):

				if(exp1_type.type == "int" or exp1_type.pointer != 0):
					return True
				else:
					return False
			elif(exp2_type == exp1_type):
				return self.unary_typecheck(exp1_type)
			else:
				return False
		elif (self.operator == ","):
			return self.unary_typecheck(exp2_type) and self.unary_typecheck(exp1_type)
		#elif(self.operator == "<" or self.operator == ">" or self.operator == ">=" or self.operator == "<="):
		#   if(exp2_type == exp1_type):
		#       TODO check for the binary <= >= etc indexes in the same array only!!!!!!!!!!!!!!!!
		#       if(exp2_type.pointer > 0 and exp1_type.pointer >0):  
		#       return self.check_operator_expr(exp1_type.type)
		else: #all the other binary operators make the same type check
			if( ((exp1_type.isNull() and not exp2_type.isPrimitive()) or
				   (exp2_type.isNull() and not exp1_type.isPrimitive()) or
				   (exp2_type.isNull() and exp1_type.isNull()))):
				if((self.operator in ["=","==","!="])):
					return True
				else:
					return False
			elif(exp2_type.similar(exp1_type)):
				return self.unary_typecheck(exp1_type)
			else: 
				return False

	def convert_to_equivalent_type(self):
		if(self.operator == "++"):
			self.operator="b+"
		elif(self.operator =="--"):
			self.operator="b-"
		elif(self.operator =="+="):
			self.operator="b+"
		elif(self.operator =="-="):
			self.operator="b-"
		elif(self.operator =="*="):
			self.operator="b*"
		elif(self.operator =="/="):
			self.operator="/"
		elif(self.operator =="%="):
			self.operator="%"
		else:
			#TODO FIX ME, PLEASE TRANSFER ME TO WARNING MESSAGES. MY BODY IS HERE BUT MY SOUL...
			print "Cannot Find Equivalent Type"
		self.binar = True
		

	def __iter__(self):
		rlist = []
		return iter(rlist)

class Node_unary_operation(Expr):
	def __init__(self, operator, exp, lineno):  
		self.operator=operator
		self.exp=exp
		self.lineno=lineno
		#We have to configure the type for this operator and for its expr
		if(operator.operator=="&"):
			self.type=Type(exp.type.type, exp.type.pointer + 1)
		elif(operator.operator=="u*"):
			self.type=Type(exp.type.type, exp.type.pointer - 1)
		else:
			self.type=Type(exp.type.type, exp.type.pointer)
	def __str__(self):
		return str(self.operator) + " My type: " + str(self.type)
	def __iter__(self):
		rlist = [self.operator]+[self.exp]
		return iter(rlist)
	def code_gen(self):
		
		op = self.operator.operator
		op_type = self.type
		name = "_temp"+str(IR_State.var_counter)


		# TODO: Think if it should have only &
		# An to operation einai & prepei an mhn epistrepsoume thn timi tou mesa alla thn dieuthinsi
		if op in ["&"]:
			old_val = IR_State.left_side
			IR_State.left_side = True
			var_s = self.exp.code_gen()
			IR_State.left_side = old_val
		else:           
			var_s = self.exp.code_gen()


		
		if(op== "u+"):
			if(op_type.isDouble()):
				floatzero = ir.Constant(Extended_DoubleType(), "0.0")
				dest = IR_State.builder.fadd(var_s, floatzero, name=name)
			else:
				intzero = ir.Constant(ir.IntType(TypeSizes.int), 0)
				dest = IR_State.builder.add(var_s, intzero, name=name)
		elif(op== "u-"):
			if(op_type.isDouble()):
				floatzero = ir.Constant(Extended_DoubleType(), "0.0")
				dest = IR_State.builder.fsub(floatzero, var_s, name=name)
			else:
				intzero = ir.Constant(ir.IntType(TypeSizes.int), 0)
				dest = IR_State.builder.sub(intzero, var_s, name=name)
		elif(op == "u*"):
			# This control is made in order to allow *(p+1+1)
			if(IR_State.left_side):
				if(var_s.type.pointee.is_pointer):
					dest = IR_State.builder.load(var_s, name=name)
				else:
					dest = var_s
			else:
				dest = IR_State.builder.load(var_s, name=name)
		elif(op == "&"):
			intzero = ir.Constant(ir.IntType(TypeSizes.int), 0)
			dest = IR_State.builder.gep(var_s,[intzero], name=name)
		elif(op == "!"):
			bin_one = ir.Constant(ir.IntType(TypeSizes.bool), 1)
			dest = IR_State.builder.xor(var_s,bin_one, name=name)
		else:
			print("Exit violently :O")
			exit(1)


		IR_State.var_map.append(dest) 
		IR_State.var_counter += 1

		return dest

class Node_binary_operation(Expr):
	def __init__(self, operator, exp1, exp2, lineno):   
		self.operator=operator
		self.exp1=exp1
		self.exp2=exp2
		self.lineno=lineno
		#We have to configure the type for this operator and for its expr
		if(operator.operator == "b+" or operator.operator == "b-"): # + or - binary
			if(exp1.type.type == "int" and
                           exp2.type.type == "int" and
                           exp1.type.pointer == 0 and
                           exp2.type.pointer == 0):
				self.type=Type("int", 0)
			elif(exp1.type.type == "double" and
                             exp2.type.type == "double" and
                             exp1.type.pointer == 0 and
                             exp2.type.pointer == 0):
				self.type=Type("double", 0)
			elif(exp1.type.type == "int" and
                             exp1.type.pointer == 0 and
                             exp2.type.pointer != 0):
				self.type=Type(exp2.type.type, exp2.type.pointer)
			elif(exp2.type.type == "int" and
                             exp2.type.pointer == 0 and
                             exp1.type.pointer != 0):
				self.type=Type(exp1.type.type, exp1.type.pointer)
		elif(operator.operator in ["<", ">", "<=", ">=", "==", "!=", "&&", "||"]):
			self.type=Type("bool", 0)
		#elif(operator.operator == ","):
		#   self.type=Type(exp2.type, exp2.pointer)
		else:
		        self.type=Type(exp2.type.type, exp2.type.pointer)
	def __str__(self):
		return str(self.operator)+ " My type: " + str(self.type)
	def __iter__(self):
		rlist = [self.exp1]+[self.exp2]
		return iter(rlist)
	def code_gen(self):
		'''
		--- WORK IN PROGRESS ---
		TODO: Make checks for types
		'''
		var_s1 = self.exp1.code_gen()
		var_s2 = self.exp2.code_gen()
		# Find the operation
		op = self.operator.operator
                op_type = self.type
		
		# Needed control if there is pointer add or sub
		if(op in ["b+", "b-"]):
			if(op_type.pointer > 0):
				old_left_side = IR_State.left_side
				if(self.exp1.type.isPrimitive()):
					IR_State.left_side = False
					int_var = self.exp1.code_gen()
					IR_State.left_side = old_left_side
					ptr_var = var_s2
				else:
					IR_State.left_side = False
					int_var = self.exp2.code_gen()
					IR_State.left_side = old_left_side
					ptr_var = var_s1
				#print dir(ptr_var.type)

		name = "_temp"+str(IR_State.var_counter)

		if(op == "b+"):
			if(op_type.pointer > 0):
				# An exei o pointer exei meinei pointer
				if(ptr_var.type.pointee.is_pointer):
					loaded = IR_State.builder.load(ptr_var, name=name+"-loaded")
					dest = IR_State.builder.gep(loaded, [int_var], name=name)
				else:
					dest = IR_State.builder.gep(ptr_var, [int_var], name=name)
			elif(op_type.isDouble()):
				'''
				print "====Bugeto edw===="
				print var_s1
				print var_s2
				for key in IR_State.eds_var_map[0]:
					print "Key, Value"
					print key, IR_State.eds_var_map[0][key]
				'''

				dest = IR_State.builder.fadd(var_s1, var_s2, name=name)
			else:
				dest = IR_State.builder.add(var_s1, var_s2, name=name)
		elif(op == "b-"):
			if(op_type.pointer > 0):
				# We negate the int_var value
				intzero = ir.Constant(ir.IntType(TypeSizes.int), 0)
				int_var = IR_State.builder.sub(intzero, int_var, name=name+"-negated")
				#print dir(ptr_var.type)
				# An exei o pointer exei meinei pointer
				if(ptr_var.type.pointee.is_pointer):
					loaded = IR_State.builder.load(ptr_var, name=name+"-loaded")
					dest = IR_State.builder.gep(loaded, [int_var], name=name)
				else:
					dest = IR_State.builder.gep(ptr_val, [int_var], name=name)
			elif(op_type.isDouble()):
				dest = IR_State.builder.fsub(var_s1, var_s2, name=name)
			else:
				dest = IR_State.builder.sub(var_s1, var_s2, name=name)
		elif(op == "b*"):
			if(op_type.isDouble()):
				dest = IR_State.builder.fmul(var_s1, var_s2, name=name)
			else:
				dest = IR_State.builder.mul(var_s1, var_s2, name=name)
		elif(op == "/"):
			if(op_type.isDouble()):
				dest = IR_State.builder.fdiv(var_s1, var_s2, name=name)
			else:
				dest = IR_State.builder.sdiv(var_s1, var_s2, name=name)
		elif(op == "%"):
			dest = IR_State.builder.srem(var_s1, var_s2, name=name)     
		elif(op == "||"):
			dest = IR_State.builder.or_(var_s1, var_s2, name=name)
		elif(op == "&&"):
			dest = IR_State.builder.and_(var_s1, var_s2, name=name)
		elif(op in ["==", "<", ">", "<=", ">=", "!="]):
			if(self.exp1.type.isNull() or self.exp2.type.isNull()):
				if(self.exp1.type.isNull() and self.exp2.type.isNull()):
					dest = IR_State.builder.icmp_signed(op, var_s1, var_s2, name=name)
				elif(self.exp1.type.isNull()):
					casted_var_s1 = var_s1.inttoptr(var_s2.type)
					dest = IR_State.builder.icmp_signed(op, casted_var_s1, var_s2, name=name)
				else:
					casted_var_s2 = var_s2.inttoptr(var_s1.type)
					dest = IR_State.builder.icmp_signed(op, var_s1, casted_var_s2, name=name)
			elif(self.exp1.type.isDouble()): # TODO: Check the need of flags
				dest = IR_State.builder.fcmp_ordered(op, var_s1, var_s2, name=name)
			elif(not self.exp1.type.isPrimitive() and 
				 not self.exp2.type.isPrimitive() and
				 op in ["<", ">", "<=", ">="]):
				# Bit cast the 2 pointers

				print "NASAI================"
				print var_s1, var_s2
				
				bitcasted1 = IR_State.builder.bitcast(var_s1, 
							ir.PointerType(ir.IntType(TypeSizes.int)))
				bitcasted2 = IR_State.builder.bitcast(var_s2, 
							ir.PointerType(ir.IntType(TypeSizes.int)))
				check_pointers = IR_State.builder.call(IR_State.check_compared_pointers_function, 
						[bitcasted1, bitcasted2])
				dest = IR_State.builder.icmp_signed(op, var_s1, var_s2, name=name)
			else:
				dest = IR_State.builder.icmp_signed(op, var_s1, var_s2, name=name)
		elif(op == ","):    
			dest = var_s2
		else:
			print("Exit violently :O")
			exit(1)
		
		IR_State.var_map.append(dest) 
		IR_State.var_counter += 1

		return dest


class Node_pre_unary_assignment(Expr):
	def __init__(self, operator, exp, lineno, typeop):  
		self.operator=operator
		if(self.operator.operator == "b+"):
			self.operator.operator="++"
			self.operator.binar = False
		elif(self.operator.operator =="b-"):
			self.operator.operator="--"
			self.operator.binar = False
		self.exp=exp
		self.lineno=lineno
		self.type=typeop
	def __str__(self):
		return str(self.operator) + " My type: " + str(self.type)
	def __iter__(self):
		rlist = [self.exp]
		return iter(rlist)

	def code_gen(self):
                previous_left_side = IR_State.left_side
                IR_State.left_side = True
		left_side = self.exp.code_gen()
		IR_State.left_side = previous_left_side
                if self.operator.operator == "++":
                        binary_operator = Operator(self.lineno, "+", True)
                elif self.operator.operator == "--":
                        binary_operator = Operator(self.lineno, "-", True)
                op_type = self.type
                if(op_type.isDouble()):
                        constant_one = Constant_Value(self.lineno, "double", 1.0)
                else:
                        constant_one = Constant_Value(self.lineno, "int", 1)
                binary_operation = Node_binary_operation(binary_operator, self.exp,
                                                 constant_one, self.lineno)
                dest = binary_operation.code_gen()

		IR_State.var_map.append(dest) 
		IR_State.var_counter += 1

		IR_State.builder.store(dest, left_side)
		return dest

class Node_post_unary_assignment(Expr):
	def __init__(self, operator, exp, lineno, typeop):  
		self.operator=operator
		if(self.operator.operator == "b+"):
			self.operator.operator="++"
			self.operator.binar = False
		elif(self.operator.operator =="b-"):
			self.operator.operator="--"
			self.operator.binar = False
		self.exp=exp
		self.lineno=lineno
		self.type=typeop
	def __str__(self):
		return str(self.operator) + " My type: " + str(self.type)
	def __iter__(self):
		rlist = [self.exp]
		return iter(rlist)

	def code_gen(self):
                previous_left_side = IR_State.left_side
		IR_State.left_side = True
		left_side = self.exp.code_gen()
		IR_State.left_side = previous_left_side

                var_s1 = self.exp.code_gen()
                if self.operator.operator == "++":
                        binary_operator = Operator(self.lineno, "+", True)
                elif self.operator.operator == "--":
                        binary_operator = Operator(self.lineno, "-", True)
                op_type = self.type
                if(op_type.isDouble()):
                        constant_one = Constant_Value(self.lineno, "double", 1.0)
                else:
                        constant_one = Constant_Value(self.lineno, "int", 1)
                binary_operation = Node_binary_operation(binary_operator, self.exp,
                                                 constant_one, self.lineno)
                dest = binary_operation.code_gen()

		IR_State.var_map.append(dest) 
		IR_State.var_counter += 1

		IR_State.builder.store(dest, left_side)
		return var_s1




class Node_whole_assignment(Expr):
	def __init__(self, operator, exp1, exp2, lineno, typeop):   
		self.operator=operator
		if(self.operator.operator =="b+"):
			self.operator.operator="+="
		elif(self.operator.operator =="b-"):
			self.operator.operator="-="
		elif(self.operator.operator =="b*"):
			self.operator.operator="*="
		elif(self.operator.operator =="/"):
			self.operator.operator="/="
		elif(self.operator.operator =="%"):
			self.operator.operator="%="
		self.exp1=exp1
		self.exp2=exp2
		self.lineno=lineno
		self.type=typeop
	def __str__(self):
		return str(self.operator)+ " My type: " + str(self.type)
	def __iter__(self):
		rlist=[self.exp1]+[self.exp2]
		return iter(rlist)

	def code_gen(self):


		IR_State.left_side = True
		left_ptr = self.exp1.code_gen()
		IR_State.left_side = False
		if(self.operator.operator == "="):
			if(self.exp2.type.isNull()):
				null_val = self.exp2.code_gen()
				right_value = null_val.inttoptr(left_ptr.type.pointee)
			else:	
				right_value = self.exp2.code_gen()
		else:
			bin_op = create_bin_op_for_whole_ass(self)
			right_value = bin_op.code_gen()
		IR_State.builder.store(right_value, left_ptr)
		return right_value



class Ternary(Expr):
	def __init__(self, predicate, then_expr, else_expr, lineno):
		if(not predicate.type.isBool()):
			print warning_messages.predicate_not_bool(str(lineno))
			exit(1)
		control1 = ((then_expr.type.isNull() and not else_expr.type.isPrimitive()) or
			   (else_expr.type.isNull() and not then_expr.type.isPrimitive()) or
			   (else_expr.type.isNull() and then_expr.type.isNull()))
		control2 = then_expr.type.similar(else_expr.type)
		if( not control1 and not control2):
			print warning_messages.ternary_expr_type_mismatch(str(lineno))
			exit(1)

		self.predicate = predicate
		self.then_expr = then_expr
		self.else_expr = else_expr
		self.type = then_expr.type
		if(then_expr.type.isNull() and not else_expr.type.isNull()):
			self.type = else_expr.type
		self.lineno = lineno
	def __str__(self):
		return "Ternary ? :"
	def __iter__(self):
		rlist = [self.predicate] + [Delimiter("Then_Stmts")] + [self.then_expr] + [Delimiter("Else_Stmts")] + [self.else_expr]
		return iter(rlist)
	def code_gen(self):
		var_s1 = self.then_expr.code_gen()
		var_s2 = self.else_expr.code_gen()
		
		predicate = self.predicate.code_gen()

		name = "_temp"+str(IR_State.var_counter)  

		if(self.then_expr.type.isNull() and not self.else_expr.type.isNull()):
			var_s1 = IR_State.builder.inttoptr(var_s1, var_s2.type, name=name+"-casted")
		elif(self.else_expr.type.isNull() and not self.then_expr.type.isNull()):
			var_s2 = IR_State.builder.inttoptr(var_s2, var_s1.type, name=name+"-casted")
		      
		
		dest = IR_State.builder.select(predicate, var_s1, var_s2, name=name)

		IR_State.var_map.append(dest) 
		IR_State.var_counter += 1

		return dest


class New(Expr):
	def __init__(self, type, lineno, array_expr = None):
		self.type = type
		self.lineno = lineno
		self.array_expr = array_expr
	def __str__(self):
		return "New " + str(self.type) + "[]" * (not self.array_expr is None)
	def __iter__(self):
		rlist = []
		return iter(rlist)
	def code_gen(self):
	
		# Evaluate the size of the new      
		if self.array_expr is not None:
			new_positions = self.array_expr.code_gen()
		else:
			new_positions = ir.Constant(ir.IntType(TypeSizes.int), 1)

		# Transform the type
		ir_type = transform_type_basic(self.type)
		#print ir_type

		name = "_temp"+str(IR_State.var_counter)        
		

		dest_generic = IR_State.builder.call(IR_State.new_function, 
				[new_positions], 
				name=name+"-generic")

		add_to_list = IR_State.builder.call(IR_State.add_to_new_list_function, 
				[dest_generic], 
				name=name+"-generic-add_to_list")


		byte_constant = ir.Constant(ir.IntType(TypeSizes.int), TypeSizes.int/8)
		positions_matrix_list = IR_State.builder.mul(new_positions, byte_constant)
		# Addare sth lista pinakwn 
		add_to_matrix_list = IR_State.builder.call(IR_State.matrix_add_to_list_function, 
				[dest_generic, positions_matrix_list], 
				name=name+"-kalesma-pinaka")
		

		# Having declared new with a generic
		# Return Type: i16 pointer
		# We need to explicitly change the pointer to
		# the desired type
		dest = IR_State.builder.bitcast(dest_generic
						, ir_type
						, name=name)



		

		IR_State.var_map.append(dest) 
		IR_State.var_counter += 1

		return dest

class Delete_Pointer(Expr):
	def __init__(self, pointer):
		self.pointer = pointer
	def __str__(self):
		return "Delete " + str(self.pointer)
	def __iter__(self):
		rlist = []
		return iter(rlist)
	def code_gen(self):
		
		'''
		TODO:
		Check if the pointer has been allocated by new
		'''
		pointer_eval = self.pointer.code_gen()
		#print "Deikths gai katastrofh"
		#print pointer_eval
		#print dir(pointer_eval)

		name = "_temp"+str(IR_State.var_counter)        
				
		pointer_casted = IR_State.builder.bitcast(pointer_eval
						, ir.PointerType(ir.IntType(TypeSizes.int))
						, name=name+"-casted")

		check_if_newed = IR_State.builder.call(IR_State.delete_from_list_function, 
						 [pointer_casted], 
						 name=name)		

		# Delete from array_list if it exists
		delete_from_list = IR_State.builder.call(IR_State.matrix_delete_from_list_function, 
				[pointer_casted])

		dest = IR_State.builder.call(IR_State.dispose_function, 
				[pointer_casted], 
				name=name)

		IR_State.var_map.append(dest) 
		IR_State.var_counter += 1

		return dest


class Function_call(Expr):
	def __init__(self,name,  type, params, lineno, function):
		self.type = type
		self.name = name
		self.actual_parameters = params
		self.lineno = lineno
		self.function = function
	def __str__(self):
		return "Function call: " + self.name + " of type " + str(self.type)
	def __iter__(self):
		rlist = self.actual_parameters
		return iter(rlist)
	def code_gen(self):

		# Get the function from its name ( Original Command has been kept)
		# function = IR_State.function_map[self.name)]
		function_with_metadata = IR_State.get_from_function_map(self.function.get_extended_signature())

		function = function_with_metadata.function
		scope_struct = function_with_metadata.get_scope_struct()

		# Evaluate the args
		# In order to evaluate the byref args we change the l-side var
		args = []
		byref_metadata = function_with_metadata.metadata["byref"].split(" ")
		for i in range(len(self.actual_parameters)):
			act_param = self.actual_parameters[i]
			# Check if the attributes list contains something
			#print byref_metadata
			if('byval' == byref_metadata[i][-5:]):
				args.append(act_param.code_gen())
			else:
				IR_State.left_side = True
				args.append(act_param.code_gen())
				IR_State.left_side = False


		#print "Auto einai to scope pou brhka sto call"
		#print scope_struct


		# Pass the scope struct as the last argument
		# An exei scope struct
		# TODO: Elegxe mexri akrwn an auto einai swsto
		if( scope_struct is not None):  
			args.append(scope_struct)

		name = "_temp"+str(IR_State.var_counter)        
		

		dest = IR_State.builder.call(function, args, name=name)

		
		IR_State.var_map.append(dest) 
		IR_State.var_counter += 1
		
		return dest


class Return():
	def __init__(self,function, expression, lineno):
		self.function = function
		self.expression = expression
		self.lineno = lineno
	def __str__(self):
		return "Return type: " + str(self.expression.type)
	def __iter__(self):
		rlist = self.expression
		return iter(rlist)
	def code_gen(self):

		# Remove all static_arrays from array_list
		#print "Return code_gen"
		for decl in (x for x in self.function.declarations if isinstance(x, Variable)):
			if(decl.array_expr is not None):
				#print decl
				arr_pointer = IR_State.get_from_eds_var_map(decl.name)
		
				# Addare sth lista pinakwn
				arr_address = IR_State.builder.load(arr_pointer)
				bitcasted = IR_State.builder.bitcast(arr_address, 
							ir.PointerType(ir.IntType(TypeSizes.int)))
				delete_from_list = IR_State.builder.call(IR_State.matrix_delete_from_list_function, 
						[bitcasted])			

		#print self.expression
		if(self.expression is None or self.expression.type.type == "void"):
			result = IR_State.builder.ret_void()
		else:
			# Evaluate the result and then return it
                        print self.function.type
                        result = self.expression.code_gen1(self.function.type)
			IR_State.builder.ret(result)	

		create_unreachable()
		
		return result

class Delimiter():
	def __init__(self, name):
		self.name = name
	def __str__(self):
		return "$ " + self.name
	def __iter__(self):
		return iter([])


class Type_cast(Expr):
	def  __init__(self, from_expr, to_type, lineno):
		self.old_expr=from_expr
		self.type=to_type
		self.lineno = lineno
	def is_valid_type_cast(self):
		if(self.old_expr.type.isPrimitive()):
			if(self.type.isPrimitive()):
				return True
			else:
				return False
		else:
			if(self.type.isInt()  or
			   self.type.isBool() or
			   self.type.isChar() or
			   not self.type.isPrimitive()):
				return True
			else:
				return False
		#else:  
		#   return False
	def __str__(self):
		return "Casting: " + str(self.type) 
	def __iter__(self):
		rlist = self.old_expr
		return iter(rlist)
	def code_gen(self):
		old_type = self.old_expr.type
		new_type = self.type

		old_type_llvm = transform_type(self.old_expr)[0]
		new_type_llvm = transform_type(self)[0]

		eval_exp = var_s = self.old_expr.code_gen()
		
		#print "Typoi"
		#print old_type, new_type
		#print old_type_llvm.is_pointer
		try:
			pass
			#print old_type_llvm.width
		except:
			pass
		#print dir(old_type_llvm)
		#print dir(new_type_llvm)
		#print type(old_type_llvm)
		#print type(new_type_llvm)
		#print isinstance(old_type_llvm, ir.types.DoubleType)
		#print isinstance(new_type_llvm, ir.types.DoubleType)
		name = "_temp"+str(IR_State.var_counter)

		'''
		We have to check every case of old and new type
		in order to apply an instruction
		We considered that primitive types can be 
		converted in any primitive type and pointers can
		be converted in pointers and integers
		'''
		dest = None
		if(isinstance(old_type_llvm, ir.types.IntType)):
			if(isinstance(new_type_llvm, ir.types.IntType)):
				if(old_type_llvm.width < new_type_llvm.width):
					dest = IR_State.builder.sext(eval_exp
							, new_type_llvm
							, name=name)
				else:
					dest = IR_State.builder.trunc(eval_exp
							, new_type_llvm
							, name=name)
			elif(isinstance(new_type_llvm, Extended_DoubleType)):
				dest = IR_State.builder.sitofp(eval_exp
						, new_type_llvm
						, name=name)
			else:
				print "This shouldnt have passed the semantic analysis"
				print "You cannot cast an integer into a pointer"
				exit(1)
		elif(isinstance(old_type_llvm, Extended_DoubleType)):
			if(isinstance(new_type_llvm, ir.types.IntType)):
				dest = IR_State.builder.fptosi(eval_exp
						, new_type_llvm
						, name=name)
			elif(isinstance(new_type_llvm, Extended_DoubleType)):
				dest = IR_State.builder.fpext(eval_exp
						, new_type_llvm
						, name=name)
			else:
				print "This shouldnt have passed the semantic analysis"
				print "You cannot cast a double into a pointer"
				exit(1)     
		elif(isinstance(old_type_llvm, ir.types.PointerType)):
			if(isinstance(new_type_llvm, ir.types.PointerType)):
				dest = IR_State.builder.bitcast(eval_exp
						, new_type_llvm
						, name=name)
			elif(isinstance(new_type_llvm, ir.types.IntType)):
				dest = IR_State.builder.ptrtoint(eval_exp
						, new_type_llvm
						, name=name)
			else:
				print "This shouldnt have passed the semantic analysis"
				print "You cannot cast a pointer to a double"
				exit(1)
		else:
			print "Something very bad happened. Here is some info:"
			print old_type_llvm
			exit(1)
		

		IR_State.var_map.append(dest) 
		IR_State.var_counter += 1


		return dest

class Array_Deref(Expr):
	def __init__(self, left_expression, index, lineno):
		self.left_expression = left_expression
		self.index = index
		self.lineno = lineno
		self.type = Type("")
		self.type.copyfrom(left_expression.type)
		self.type.pointer -= 1
	def __str__(self):
		return "Array deref of type: " + str(self.type)
	def __iter__(self):
		rlist = [self.left_expression] + [Delimiter("$ Index")] + [self.index]
		return iter(rlist)  
	def code_gen(self):

		

		
		
		# We are keeping the left_side value
		# We change it to False always ,
		# because we never want to save on the address of the variable,
		# but rather somewhere relative to its value
		old_left_side = IR_State.left_side
		IR_State.left_side = False
		arr_index = self.index.code_gen()
		left_exp = self.left_expression.code_gen()
		IR_State.left_side = old_left_side  

		name = "_temp"+str(IR_State.var_counter)

		if(not IR_State.left_side):     
			dest_temp = IR_State.builder.gep(left_exp,[arr_index])
			dest = IR_State.builder.load(dest_temp, name=name)
		else:
			dest = IR_State.builder.gep(left_exp, [arr_index], name=name)


		IR_State.var_map.append(dest) 
		IR_State.var_counter += 1

		return dest

class Parenthesial_expression(Expr):
	def __init__(self, expr, lineno):
		self.expr = expr
		self.lineno=lineno
		self.type = expr.type
	def __str__(self):
		return "Parenthesial Expression: " + str(self.expr) 
	def __iter__(self):
		rlist = self.expr
		return iter(rlist)
	def code_gen(self):
		dest = self.expr.code_gen()

		return dest
