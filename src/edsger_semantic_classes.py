import warning_messages
import itertools
import operator
from llvmlite import ir
from edsger_ir import IR_State, Function_With_Metadata

############
## Useful ##
############

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


# We are running down the tree until we find a variable
def l_val_typecheck(head, maybe):
	print head
	if (isinstance(head, Variable)):
		return True;
	elif (isinstance(head, Parenthesial_expression)):
		return l_val_typecheck(head.expr, maybe)
	elif (isinstance(head, Array_Deref)):
		return l_val_typecheck(head.left_expression, maybe)
	elif (isinstance(head, Node_unary_operation)):
		if( head.operator.operator == "u*"):
			return l_val_typecheck(head.exp, True)
	elif(isinstance(head, Node_pre_unary_assignment) or isinstance(head, Node_post_unary_assignment)):
		pass
	## TODO WHOLE ASSIGNEMENT AND PRE UNARY ASSIGNEMNT
	elif (isinstance(head, Node_binary_operation)):
		if( (head.operator.operator in ["b+", "b-"]) and maybe and (head.exp1.type.pointer > 0 or head.exp2.type.pointer > 0)):
			if(head.exp1.type.pointer > 0):
				return l_val_typecheck(head.exp1, maybe)
			else:
				return l_val_typecheck(head.exp2, maybe)
	return False;

'''
Transforms our type into an LLVM type instance and it returns
Returns (LLVM_Type, Array_Size (Only useful for allocation))
'''
def transform_type(var):

	our_type = var.type
	our_type_name = our_type.type
	our_type_pointer = our_type.pointer
	
	array_size = 1

	# If the variable is primitive
	var_size = 0
	if our_type.isGenBool():
		var_size = 1
		var_type = ir.IntType(var_size)
	elif our_type.isGenChar():
		var_size = 8
		var_type = ir.IntType(var_size)
	elif our_type.isGenInt():
		var_size = 32
		var_type = ir.IntType(var_size)
	elif our_type.isGenDouble():
		var_size = 64
		var_type = ir.DoubleType()

	# If it is not primitive
	if not our_type.isPrimitive():
		# If its an array , declare it as one less pointer
		pointer_number = our_type_pointer
		
		for i in range(pointer_number):
			var_type = ir.PointerType(var_type)	


	# If it is an array
	if var.array_expr is not None:
		# Evaluate the expression 
		# TODO: For now it only works for constant

		array_size = int(var.array_expr.value)

	return (var_type, array_size)

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
	#print sorted(IR_State.get_curr_level_of_eds_var_map().keys())
	# We sort them so that they have some kind of order
	current_scope = IR_State.get_curr_level_of_eds_var_map()
	current_scope_keys = sorted(current_scope.keys())
	current_scope_types = []
	for var_in_curr_scope_key in current_scope_keys:
		var_in_curr_scope = current_scope[var_in_curr_scope_key]
		current_scope_types.append(var_in_curr_scope.type)

	# Add the scope struct as the last argument of the function
	scope_struct_type = ir.LiteralStructType(current_scope_types)
	allocated_scope_struct = IR_State.builder.alloca( 
				scope_struct_type,  
				name="_current_scope" )
	IR_State.add_to_eds_var_map("_current_scope"
				, allocated_scope_struct)
	#print allocated_scope_struct
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
		signature = identifier + "-" + str(len(type_list)) + reduce(operator.concat, map(lambda x: "-" + str(x), type_list) , "")
		for scope in cls.function_scope_stack:
			if(signature in scope):
				return scope[signature]
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

# Type class
class Type():
	def __init__(self,constant_type,pointer=0):
		self.type = constant_type
		self.pointer = pointer
	def similar(self, other):
		return (isinstance(other, self.__class__) and self.type == other.type and (self.pointer > 0) == (other.pointer > 0))
	def __eq__(self, other):
		return (isinstance(other, self.__class__) and self.type == other.type and self.pointer == other.pointer )
	#Select among 2 policies 
	#C-Like (self.type == other.type) and ()
	#TODO FIX ME.. Maybe put Array in Variable Class
	def __ne__(self, other):
		return not self.__eq__(other)
	def __str__(self):
		return str(self.type) + (" pointer" * self.pointer)
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

# Constant value
class Constant_Value(Expr):
    def __init__(self,lineno,constant_type,value):
    	if(constant_type == "string"):
    		self.type = Type("char", 1)
    	else: 
        	self.type = Type(constant_type)
        self.value = value
        self.lineno = lineno
    def __str__(self):
    	return "Constant_Value( " + str(self.type) + ", " + str(self.value) + " )"
    def code_gen(self):
    	## --- WORK IN PROGRESS ---
		## TODO: Make checks for types
		if self.type.isInt():
			dest = ir.Constant(ir.IntType(32), self.value)
		elif self.type.isDouble():
			dest = ir.Constant(ir.DoubleType(), self.value)
		elif self.type.isBool():
			dest = ir.Constant(ir.IntType(1), self.value)
		elif self.type.isChar():
			# Supposing that characters are always 3 chars long
			dest = ir.Constant(ir.IntType(8), ord(self.value[1]))
		elif self.type.isGenChar() and self.type.pointer == 1:
			pass
		else:
			print"Exit like we got a big problem :'("
			exit(1)
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

	def declare_type(self,vtype):
		self.type = vtype

	def __str__(self):
		return "Variable( " + str(self.name)  + " , " + str(self.type) + " )" + (" [ " + str(self.array_expr) + " ] " )*(not self.array_expr is None) 

	def code_gen(self):
		var_name = self.name 
		name = "_temp"+str(IR_State.var_counter)
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
		
		ret_val = IR_State.builder.alloca( var_type, 
					size=array_size, name=our_name )
		IR_State.add_to_eds_var_map(our_name, ret_val)
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
		if( self.byref == 0 ):
			param_value = IR_State.get_from_eds_var_map(var_name)
		else:
			ptr = IR_State.get_from_eds_var_map(var_name)
			if(not IR_State.left_side):		
				param_value = IR_State.builder.load(ptr, name=self.name)
				IR_State.var_map.append(param_value) 
				IR_State.var_counter += 1
				return param_value
			else:
				return ptr

		return param_value

class Function(Identifier):
	def __init__(self,lineno,r_type, name, parameters = [], declarations = [], statements = []):
		self.type = r_type
		self.name = name
		self.parameters = list(parameters)
		self.lineno = lineno
		self.declarations = declarations
		self.statements = statements

	def get_signature(self):
		return self.name + "-" + str(len(self.parameters)) + reduce(operator.concat, map(lambda x: "-" + str(x.type), self.parameters) , "")

	# Parameters will be a list of variables
	def add_parameter(self,parameter):
		self.parameters.append(parameter) 

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

		'''
			TODO: 
			- Kane kati gia to None
		'''
		#print self
		#print "Stack"
		#print IR_State.eds_var_map
		scope_struct = IR_State.get_from_eds_var_map("_current_scope")
		# TODO: AN einai none kane akti
		if scope_struct is not None:	
			function_arg_types.append(scope_struct.type)
			print function_arg_types

		# Find the return type
		ret_type = ir.IntType(32)

		# Create a new function and and save it at its map 
		function_type = ir.FunctionType(ret_type, function_arg_types)
		function = ir.Function(IR_State.module, function_type, name=self.name)
		
		# THe original command has been kept before testing
		# IR_State.function_map[self.name] = function
		function_with_metadata = Function_With_Metadata(function)
		function_with_metadata.set_scope_struct(scope_struct)
		IR_State.add_to_function_map(self.name, function_with_metadata)

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
			
			IR_State.add_to_eds_var_map(eds_param_name, llvm_param)


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
		

		# Evaluate the function declarations and statements
		with IR_State.builder.goto_block(block):
			variable_decls = [x for x in enlist(
					self.declarations) if isinstance(x, Variable)]
			function_decls = [x for x in enlist(
					self.declarations) if isinstance(x, Function)]
			for element in variable_decls:
				element.code_gen_decl()
			

			'''
			Map the variables to their real value
			'''
			previous_scope_frame = IR_State.eds_var_map[1]
			previous_scope_frame_keys = [x for x in sorted(
					previous_scope_frame.keys()) if not x=="_current_scope"]
			print "Prohgoumeno"
			print previous_scope_frame_keys

			'''
			- An to megethos eiani 2 shmainei oti 
			  den uparxei pio prin giati eimaste global
			- Ebala to idio sto function call
			TODO: Elegxw an isxuei auto 
			'''
			if( len(IR_State.eds_var_map) > 2):
				for i in range(len(previous_scope_frame_keys)):
					key = previous_scope_frame_keys[i]
					print function.args[-1]
					scope_variable_address = IR_State.builder.gep(
							function.args[-1] ,
							[ ir.Constant(ir.IntType(32), 0)
							, ir.Constant(ir.IntType(32), i) 
							] ,
							name="__"+key )
					scope_variable = IR_State.builder.load(
							scope_variable_address,
							name="___"+key )
					IR_State.add_if_not_to_eds_var_map(key, scope_variable)


			# Create the current scope_struct
			create_scope_struct()

			for element in function_decls:
				element.code_gen_decl()
			

			for element in enlist(self.statements):
				element.code_gen()

		# Kleise to scope level
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
		with IR_State.builder.if_else(predicate) as (then, otherwise):
		    with then:
		        # emit instructions for when the predicate is true
		        for stmt in enlist(self.then_stmts):
		        	stmt.code_gen()
		    with otherwise:
		        # emit instructions for when the predicate is false
		        if(self.else_stmts):
		        	for stmt in enlist(self.else_stmts):
		        		stmt.code_gen()
		        else:
		        	IR_State.builder.unreachable()		
		


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
		exit_loop_block = IR_State.builder.append_basic_block(loop_name + ".exit")

		# Save the blocks in the map
		IR_State.block_map[loop_name + ".pred"] = pred_loop_block
		IR_State.block_map[loop_name] = loop_block
		IR_State.block_map[loop_name + ".exit"] = exit_loop_block

		exp1 = self.expression1.code_gen()
		IR_State.builder.branch(pred_loop_block)

		with IR_State.builder.goto_block(pred_loop_block):
			# emit instructions for the pred_loop_block
			predicate = self.expression2.code_gen()

			IR_State.builder.cbranch(predicate, loop_block, exit_loop_block)


		with IR_State.builder.goto_block(loop_block):
			# emit instructions for the loop_block
			for stmt in enlist(self.stmts):
				stmt.code_gen()
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
		
		loop_block = IR_State.block_map[self.name + ".pred"]
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
		#	if(exp2_type == exp1_type):
		# 		TODO check for the binary <= >= etc indexes in the same array only!!!!!!!!!!!!!!!!
		#		if(exp2_type.pointer > 0 and exp1_type.pointer >0):  
		#		return self.check_operator_expr(exp1_type.type)
		else: #all the other binary operators make the same type check
			if(exp2_type.similar(exp1_type)):
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
				floatzero = ir.Constant(ir.DoubleType(), 0.0)
				dest = IR_State.builder.fadd(var_s, floatzero, name=name)
			else:
				intzero = ir.Constant(ir.IntType(32), 0)
				dest = IR_State.builder.add(var_s, intzero, name=name)
		elif(op== "u-"):
			if(op_type.isDouble()):
				floatzero = ir.Constant(ir.DoubleType(), 0.0)
				dest = IR_State.builder.fsub(floatzero, var_s, name=name)
			else:
				intzero = ir.Constant(ir.IntType(32), 0)
				dest = IR_State.builder.sub(intzero, var_s, name=name)
		elif(op == "u*"):
			dest = IR_State.builder.load(var_s, name=name)
		elif(op == "&"):
			intzero = ir.Constant(ir.IntType(32), 0)
			dest = IR_State.builder.gep(var_s,[intzero], name=name)
		elif(op == "!"):
			bin_one = ir.Constant(ir.IntType(1), 1)
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
			if(exp1.type.type == "int" and exp2.type.type == "int" and exp1.type.pointer == 0 and exp2.type.pointer == 0):
				self.type=Type("int", 0)
			elif(exp1.type.type == "double" and exp2.type.type == "double" and exp1.type.pointer == 0 and exp2.type.pointer == 0):
				self.type=Type("double", 0)
			elif(exp1.type.type == "int" and exp1.type.pointer == 0 and exp2.type.pointer != 0):
				self.type=Type(exp2.type.type, exp2.type.pointer)
			elif(exp2.type.type == "int" and exp2.type.pointer == 0 and exp1.type.pointer != 0):
				self.type=Type(exp1.type.type, exp1.type.pointer)
		elif(operator.operator == "<" or operator.operator == ">" or operator.operator == "<=" or operator.operator == ">=" or operator.operator == "==" or operator.operator == "!=" or operator.operator == "&&" or operator.operator == "||"):
			self.type=Type("bool", 0)
		#elif(operator.operator == ","):
		#	self.type=Type(exp2.type, exp2.pointer)
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

		name = "_temp"+str(IR_State.var_counter)

		if(op == "b+"):
			if(op_type.isDouble()):
				dest = IR_State.builder.fadd(var_s1, var_s2, name=name)
			else:
				dest = IR_State.builder.add(var_s1, var_s2, name=name)
		elif(op == "b-"):
			if(op_type.isDouble()):
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
			if(self.exp1.type.isDouble()): # TODO: Check the need of flags
				dest = IR_State.builder.fcmp_signed(op, var_s1, var_s2, name=name)
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
		IR_State.left_side = True
		left_side = self.exp.code_gen()
		IR_State.left_side = False
		var_s1 = self.exp.code_gen()
		var_s2 = ir.Constant(ir.IntType(32), 1)
		op_type = self.type
		
		name = "_temp"+str(IR_State.var_counter)

		if (self.operator.operator == "++"):
			if(op_type.isDouble()):
				var_s2 = ir.Constant(ir.DoubleType(), 1.0)
				dest = IR_State.builder.fadd(var_s1, var_s2, name=name)
			else:
				dest = IR_State.builder.add(var_s1, var_s2, name=name)
		elif(self.operator.operator == "--"):
			if(op_type.isDouble()):
				var_s2 = ir.Constant(ir.DoubleType(), 1.0)
				dest = IR_State.builder.fsub(var_s1, var_s2, name=name)
			else:
				dest = IR_State.builder.sub(var_s1, var_s2, name=name)
		else:
			print "Pre unary assignment invalid operator: " + str(self.operator.operator)

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
		IR_State.left_side = True
		left_side = self.exp.code_gen()
		IR_State.left_side = False
		var_s1 = self.exp.code_gen()
		var_s2 = ir.Constant(ir.IntType(32), 1)
		op_type = self.type
		
		name = "_temp"+str(IR_State.var_counter)

		if (self.operator.operator == "++"):
			if(op_type.isDouble()):
				var_s2 = ir.Constant(ir.DoubleType(), 1.0)
				dest = IR_State.builder.fadd(var_s1, var_s2, name=name)
			else:
				dest = IR_State.builder.add(var_s1, var_s2, name=name)
		elif(self.operator.operator == "--"):
			if(op_type.isDouble()):
				var_s2 = ir.Constant(ir.DoubleType(), 1.0)
				dest = IR_State.builder.fsub(var_s1, var_s2, name=name)
			else:
				dest = IR_State.builder.sub(var_s1, var_s2, name=name)
		else:
			print "Post unary assignment invalid operator: " + str(self.operator.operator)

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
		right_value = self.exp2.code_gen()
		IR_State.builder.store(right_value, left_ptr)
		return right_value



class Ternary(Expr):
	def __init__(self, predicate, then_expr, else_expr, lineno):
		if(not predicate.type.isBool()):
			print warning_messages.predicate_not_bool(str(lineno))
			exit(1)
		if(not then_expr.type.similar(else_expr.type)):
			print warning_messages.ternary_expr_type_mismatch(str(lineno))
			exit(1)
		self.predicate = predicate
		self.then_expr = then_expr
		self.else_expr = else_expr
		self.type = then_expr.type
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
		function_with_metadata = IR_State.get_from_function_map(self.name)
		function = function_with_metadata.function
		scope_struct = function_with_metadata.get_scope_struct()

		# Evaluate the args
		# In order to evaluate the byref args we change the l-side var
		args = []
		byref_metadata = function_with_metadata.metadata["byref"].split(" ")
		for i in range(len(self.actual_parameters)):
			act_param = self.actual_parameters[i]
			# Check if the attributes list contains something
			if('byval' == byref_metadata[i][-5:]):
				args.append(act_param.code_gen())
			else:
				IR_State.left_side = True
				args.append(act_param.code_gen())
				IR_State.left_side = False


		# Pass the scope struct as the last argument
		# Ann den eiani global sunarthsh
		if( len(IR_State.eds_var_map) > 2):
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
		# Evaluate the result and then return it
		result = self.expression.code_gen()
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
	basic = ["int", "char", "double", "bool"]
	basic_types = [basic, basic, basic, basic]
	allowed = {"int":0, "char":1, "double":2, "bool":3}
	def  __init__(self, from_expr, to_type, lineno):
		self.old_expr=from_expr
		self.type=to_type
		self.lineno = lineno
	def is_valid_type_cast(self):
		if(self.type.type in self.basic_types[self.allowed[self.old_expr.type.type]]):
			return True
		else:	
			return False
	def __str__(self):
		return "Casting: " + str(self.type) 
	def __iter__(self):
		rlist = self.old_expr
		return iter(rlist)

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

		

		arr_index = self.index.code_gen()
		
		# We are keeping the left_side value
		# We change it to False always ,
		# because we never want to save on the address of the variable,
		# but rather somewhere relative to its value
		old_left_side = IR_State.left_side
		IR_State.left_side = False
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