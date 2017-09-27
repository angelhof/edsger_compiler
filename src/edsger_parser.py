from ply import *
import edsger_lexer
from edsger_semantic_classes import *
import warning_messages
import sys
import copy

tokens = edsger_lexer.tokens

precedence = (
			   ('left', 'COMMA'),
			   ('left', 'MOUFETO'),
			   ('right', 'EQUALS','TIMESEQUAL' , 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL'),
			   ('left', 'TERNARY', 'COLON'),
			   ('left', 'OR'),
			   ('left', 'AND'),
			   ('nonassoc', 'LT', 'GT', 'LE', 'GE', 'EQ', 'NE'),  # Nonassociative operators
               ('left', 'PLUS','MINUS'),
               ('left', 'TIMES','DIVIDE', 'MODULO'),
               ('left', 'TYPE_CAST_PAREN'),
               ('right', 'PRE_INCREMENT', 'PRE_DECREMENT'),
               ('left', 'NEW', 'DELETE'),
               ('left','UMINUS', 'NOT', 'UADDRESS', 'USTAR', 'BYREF'), # Mayve byref doesnt go here
               ('right', 'INCREMENT', 'DECREMENT'),
               ('left', 'ARG_COMMA'),
               ('left','LPAREN', 'RPAREN' , 'LBRACKET', 'RBRACKET' , 'LBRACE' ,'RBRACE')
)


#############
### RULES ###
#############

def p_program(p):
	'''program : start_of_program global_declarations'''
	#for i in Program_State.scope_stack:
	#	print i.keys()
	#AST.print_tree(p[2],0)
        if len(p[2]) == 0:
                print warning_messages.empty_program()
                exit(1)
        AST.head = p[2]
	#AST.print_tree(sys.stdout)

def p_start_program(p):
	'''start_of_program :'''
	# We initialize the scope outside of the parser
	# TODO Think of deleting this

def p_program_error(p):
	'''program : error'''
	p[0] = None
	p.parser.error = 1

## We have double declarations rules one for local and one for global 
## so that we can handle includes
def p_declarations(p):
	'''declarations : empty
					| declaration declarations'''
	if(len(p) == 3):
		p[2] = p[1] + p[2]
		p[0] = p[2]
	else:
		p[0] = []

	

def p_declaration(p):
	'''declaration : variable_declaration
				   | function_declaration
				   | function_definition'''
	p[0] = p[1]


def p_global_declarations(p):
	'''global_declarations : empty
					| global_declaration global_declarations'''
	if(len(p) == 3):
		if(p[1] is not None):
			p[2] = p[1] + p[2]
		p[0] = p[2]
	else:
		p[0] = []

def p_global_declaration(p):
	'''global_declaration : INCLUDE
				   | variable_declaration
				   | function_declaration
				   | function_definition'''	
	if(isinstance(p[1], basestring)):
		# Ignore the include
		if(p[1][0] == '#'):
			p[0] = None	   
	else:
		if(isinstance(p[1][0], Variable)):
                        for i in xrange(len(p[1])):
                                p[1][i].isGlobal = True
		p[0] = p[1]
                
def p_variable_declaration(p):
	'''variable_declaration : type many_declarators SEMI'''
	for i in p[2]:
		i.declare_type(p[1])
		# An einai array xanetai h plhroforia mexri edw
		if(i.array_expr):
			i.type.pointer += 1
		Program_State.add_variable_to_curr_scope(i) 
	# TODO Check if we should return something here
	p[0] = p[2]

def p_many_declarators(p):
	'''many_declarators : declarator
						| declarator COMMA many_declarators %prec ARG_COMMA'''
	if(len(p)==2):
		p[0] = [p[1]]
	else:
		p[3].insert(0, p[1])
		p[0] = p[3]
	#print p[0]

# TODO Fix this type
def p_type(p):
	'''type : basic_type maybe_pointer'''
	p[0] = Type(p[1], len(p[2]))
	#print p[0]

def p_maybe_pointer(p):
	'''maybe_pointer : empty
					 | TIMES maybe_pointer %prec USTAR'''
	if(len(p) == 3):
		p[0] = p[1] + p[2]
	else:
		p[0] = ""

def p_basic_type(p):
	'''basic_type : INTTYPE
				  | CHARTYPE
				  | BOOLTYPE
				  | DOUBLETYPE'''
	p[0] = p[1]

def p_identifier(p):
	'''identifier : ID'''
	identifier = Program_State.variable_in_scope(p[1])
	if(identifier):
		p[0] = identifier
	else:
		p[0] = Identifier(p.lineno(1),p[1])
	#print p[0]

def p_decl_identifier(p):
	'''decl_identifier : ID'''
	p[0] = Identifier(p.lineno(1),p[1])
	#print p[0]

def p_declarator(p):
	'''declarator : decl_identifier
				  | decl_identifier LBRACKET constant_expression RBRACKET'''
	# Convert from the general identifier case to a variable 
	if(not isinstance(p[1], Variable)):
		p[1] = Variable(p[1].lineno, Type(""), p[1].name)
	if(len(p) == 2):
		p[0] = p[1]
	else:
		if(p[3].type.isInt()):
			# TODO Check ti mporei na mpei sto array
			p[1].array_expr = p[3]
			p[1].type.pointer += 1 
			p[0] = p[1]	
		else:
			print warning_messages.not_int_index(str(p.lineno(3)))
			exit(1)



def p_function_declaration(p):
	'''function_declaration : function_with_result_type LPAREN maybe_parameter_list RPAREN SEMI'''
	for param in p[3]:
		p[1].add_parameter(param)
        p[1].set_declaration(True)
        p[0] = p[1]
	Program_State.add_function_to_curr_scope(p[0]) 
	p[0] = [p[0]]
	#print p[0]

def p_function_with_result_type(p):
	'''function_with_result_type : type ID
								 | VOID ID'''
	fun_type = p[1]
	if( p[1] == "void"):
		fun_type = Type("void")
	p[0] = Function(p.lineno(2), fun_type, p[2])


def p_maybe_parameter_list(p):
	'''maybe_parameter_list : empty
							| parameter_list'''
	p[0] = p[1]
	if(not p[1]):
		p[0] = []


def p_parameter_list(p):
	'''parameter_list : parameter
					  | parameter COMMA parameter_list %prec ARG_COMMA'''
	if(len(p)==2):
		p[0] = [p[1]]
	else:
		p[3].insert(0, p[1])
		p[0] = p[3]

def p_parameter(p):
	'''parameter : type decl_identifier
				 | BYREF type decl_identifier'''
	## TODO Check if we have to create sub class for parameter
	if(len(p) == 3):
		ident = p[2]
		id_type = p[1]
		byref = 0
	elif(len(p) == 4):
		ident = p[3]
		id_type = p[2]
		byref = 1
	p[0] = Parameter(ident.lineno, id_type, ident.name, byref)


def p_function_definition(p):
	'''function_definition : function_with_result_and_parameters declarations statements RBRACE'''
	p[0] = p[1]
	# Set its declarations and definitions
	p[0].declarations = p[2]
	p[0].statements = p[3]
        p[0].set_declaration(False)
	Function_Stack.pop()
	Program_State.pop()
	#print "DEFINITIONS "
	#print p[0]
	#print id(p[0])
	p[0] = [p[0]]
	

def p_function_with_result_and_parameters(p):
	'''function_with_result_and_parameters : function_with_result_type LPAREN maybe_parameter_list RPAREN LBRACE '''
	# If the function is already declared
	# Important:
	# We consider here that functions can be declared outside of the scope that it is defined

	# Add the parameters	
	for param in p[3]:
		p[1].add_parameter(param)
	
	# Find the function in the scope
	p[0] = Program_State.function_in_top_scope(p[1].name, map(lambda x: x.type, p[1].parameters))
	if(p[0] is not None):
		# If the function is defined
		if(not p[0].is_declaration):
			print warning_messages.redefine_function(p[0].name, str(p[0].lineno))
			exit(1)
	else:
		# If it is not declared
		p[0] = p[1] 
		Program_State.add_function_to_curr_scope(p[1])
	Function_Stack.push(p[0], p.lineno(1))
	Program_State.push({})
	
	# Put the parameters in the function scope
	for param in p[3]:
		Program_State.add_variable_to_curr_scope(param)



def p_new_scope(p):
	'''new_scope :'''
	Program_State.push({})

def p_statements(p):
	'''statements : empty
				  | statement statements'''
	if(len(p) == 3):
		# Statement could be None (for example just a semicolon)
		if(p[1]):
			p[2].insert(0,p[1])
		p[0] = p[2]
	else:
		p[0] = []

def p_statement(p):
	'''statement : SEMI
				 | expression SEMI
				 | LBRACE new_scope statements RBRACE
				 | IF LPAREN expression RPAREN statement maybe_else
				 | for_loop LPAREN maybe_expression SEMI maybe_expression SEMI maybe_expression RPAREN statement
				 | CONTINUE maybe_id SEMI
				 | BREAK maybe_id SEMI
				 | RETURN maybe_expression SEMI''' 
	if(p[1] == ";"):
		p[0] = None
	elif(p[1] == "if"):
		p[0] = If_Statement(p.lineno(1), p[3], p[5], p[6])
	elif(isinstance(p[1], For_Statement)):
		p[0] = For_Statement(p[1].lineno , p[3], p[5], p[7], p[9], p[1].name)
                ## If the loop has no statements dont even execute it
                if p[9] == None or p[9] == []:
                        p[0] = None
		Loop_Stack.pop()
	elif(p[1] == "break" or p[1] == "continue"):
		if(Loop_Stack.isEmpty()):
			print warning_messages.outside_loop(p[1],str(p.lineno(1)))
			exit(1)		
		name = Loop_Stack.stack[0]		
		if(p[2] and not Loop_Stack.exists(p[2].name)):
			print warning_messages.loop_tag_doesnt_exist(p[2].name, str(p.lineno(2)))
			exit(1)
		if(p[2]):
			name = p[2].name
		if(p[1] == "break"):
			p[0] = Break(p.lineno(1), name)
		else:
			p[0] = Continue(p.lineno(1), name)
	elif(isinstance(p[1], Expr)):
		p[0] = p[1]
		# TODO Maybe change this to a statement class
	elif(p[1] == "{"):
		p[0] = p[3]
		Program_State.pop()
	elif(p[1] == "return"):
		if(Function_Stack.isEmpty()):
			print warning_messages.global_return(p.lineno(1))
			exit(1)
		if(not p[2]):
			p[2] = Expr(p.lineno(1), Type("void"))
	
		function = Function_Stack.stack[0]

		if(not function.type == p[2].type and not p[2].type.isNull()):
			print warning_messages.type_mismatch(str(p[2].type), str(p.lineno(1)))
			exit(1)
		
		p[0] = Return(function, p[2], p.lineno(1))

		# TODO Make a return class and a return stack


	# TODO The same I did  for break and continue with return


def p_for_loop(p):
	'''for_loop : FOR
			    | ID COLON FOR'''
	if(p[1] == "for"):
		name = Loop_Stack.loop_name_creator().next()
		p[0] = For_Statement(p.lineno(1), None, None, None, None, name)
	else:	
		name = p[1]
		p[0] = For_Statement(p.lineno(3), None, None, None, None, name)
	Loop_Stack.push(name, p.lineno(1))


def p_maybe_id(p):
	'''maybe_id : empty
				| identifier'''
	p[0] = p[1]

def p_maybe_expression(p):
	'''maybe_expression : empty
						| expression %prec MOUFETO'''
	p[0] = p[1]

def p_maybe_else(p):
	'''maybe_else : empty
				  | ELSE statement'''
	if( len(p) == 2 ):
		p[0] = []
	else:
		p[0] = p[2]


def p_expression(p):
	'''	expression : identifier
	|	parenthesial_expression
	| 	constant_value
	|	function_call
	|	ufo
	|	unary_operation
	|	binary_operation
	|	left_assignment
	|	right_assignment
	|	whole_assignment
	|	type_casting
	|	ternary_operation
	|	new
	|	delete'''
	#TODO FIX MEEEEE!!! idont know my identity ufooooooooooo
	if(isinstance(p[1], Constant_Value)):
		p[0] = p[1]
	elif(isinstance(p[1], Identifier)):
		if(not Program_State.variable_in_scope(p[1].name)):
			print warning_messages.undeclared_variable(p[1].name, str(p.lineno(1)))
			exit(1)
		p[0] = p[1]
	elif(isinstance(p[1], Node_unary_operation) or isinstance(p[1], Node_binary_operation)):
		p[0] = p[1]
		#print p[1]
	# THis elif is for the hack DO NOT DELETE
	elif(isinstance(p[1], New) and len(p) == 3):
		# If it is a basestring it means that it is a pointer
		if( isinstance(p[2], basestring ) ):
			p[1].type.pointer = p[1].type.pointer + 1
			p[0] = p[1]
		elif(p[2]):
			# We have a tuple (op, expr)
			operation = p[2][0]
			expression = p[2][1]
			if( not operation.binary_typecheck(p[1].type,expression.type)):
				print warning_messages.invalid_type(str(operation.lineno), [])
				exit(1)
			p[0]=Node_binary_operation(operation,p[1],expression,operation.lineno)
		else:
			p[0] = p[1]
	else:
		p[0]=p[1]



# ---------------Check this crazy hack ---------------------------


def p_new(p):
	'''new : NEW type
 		   | NEW type LBRACKET expression RBRACKET'''
	#TODO make the if then else
	if(len(p) == 3):
		p[2].pointer += 1
		p[0] = New(p[2], p.lineno(1))
	else:
		if(p[4].type.isInt()):
			p[2].pointer += 1
			p[0] = New(p[2], p.lineno(1), p[4]) 
		else:
			print warning_messages.not_int_index(str(p.lineno(4)))
			exit(1)


# These 3 new rules appeared to deal with the following case:
#	 -> new int * 5  Which is syntactically legal 

# I think we never use it maybe delet it
########################################
def p_soft_new(p):
	'''soft_new : NEW basic_type 
				| soft_new TIMES %prec USTAR'''
	if(p[1] == "new"):
		p[0] = New(Type(p[2],1), p.lineno(1))
	else:
		p[1].type.pointer = p[1].type.pointer + 1
		p[0] = p[1]

def p_strict_new(p):
	'''strict_new : soft_new LBRACKET expression RBRACKET'''
	#p[0] = New(p[2], p[4])
	# Choose whether array needs to be in type or in variable
	if(p[4].type.isInt()):
		p[0] = New(Type(p[2].type, p[2].pointer + 1), p.lineno(1), p[4]) 
	else:
		print warning_messages.not_int_index(str(p.lineno(4)))
		exit(1)

# ATTENTION 
# I Hope and assume this times is always a bin op
def p_maybe_multi_hack(p):
	'''maybe_multi_hack : empty
						| TIMES maybe_expression
						| LBRACKET expression RBRACKET
						| TIMES LBRACKET expression RBRACKET'''
	if(p[1] == "*"):
		if(p[2]):
			# TODO MAKE IT A BINARY OPERATION TIMES
			operator = Operator(p.lineno(1),p[1],True)
			expression = p[2]
			p[0] = (operator, expression)
		else:
			p[0] = p[1]
########################################
	
# ------------------------------------------------------------------






def p_parenthesial_expression(p):
	'''parenthesial_expression : LPAREN expression RPAREN'''
	p[0]=Parenthesial_expression(p[2],p[2].lineno)


def p_ufo(p):
	'''ufo : expression LBRACKET expression RBRACKET'''
	if(p[1].type.pointer <= 0):
		print warning_messages.is_not_a_pointer(str(p.lineno(1)))
		exit(1)
	if(p[3].type.isInt()):
		p[0] = Array_Deref(p[1], p[3], p.lineno(1))
	else:
		print warning_messages.not_int_index(str(p.lineno(3)))
		exit(1)

def p_function_call(p):
	'''function_call : ID LPAREN empty RPAREN
					 | function_with_acts expression RPAREN'''
	if(len(p) == 5):
		# Changed and untested
		identifier = Program_State.function_in_scope(p[1], [])
		if(not identifier):
			print warning_messages.undeclared_function(p[1], str(p.lineno(1)))
			exit(1)
		p[0] = Function_call(identifier.name, identifier.type, [], p.lineno(1), identifier)
	else:
		act_parameter = p[2]
		argument_types_list = map(lambda x: x.type, p[1].actual_parameters + [p[2]])
		identifier = Program_State.function_in_scope(p[1].name, argument_types_list)
		if(not identifier):
			print warning_messages.undeclared_function(p[1].name, str(p.lineno(1)))
			exit(1)
		# TODO Delete
		#if(len(p[1].actual_parameters)  >= len(identifier.parameters)):
		#	print warning_messages.bad_argument_number(str(p.lineno(1)))
		#	exit(1)
		#expected_parameter = identifier.parameters[len(p[1].actual_parameters)]
		#if(not act_parameter.type == expected_parameter.type):
		#	print warning_messages.type_mismatch(str(act_parameter), str(p.lineno(1)))
		#	exit(1)
		p[1].actual_parameters.append(p[2]) 
		p[1].type = identifier.type
		p[1].function = identifier
		p[0] = p[1]


def p_function_with_acts(p):
	'''function_with_acts : ID LPAREN
						  | function_with_acts expression COMMA'''
	if(len(p) == 3):
		identifier = p[1]
		#if(not identifier):
		#	print warning_messages.undeclared_function(p[1].name, str(p.lineno(1)))
		#	exit(1)
		p[0] = Function_call(identifier, None, [], p.lineno(1), None)
	else:
		act_parameter = p[2]
		identifier = p[1]
		# TODO DELETE
		#if(len(p[1].actual_parameters)  >= len(identifier.parameters)):
		#	print warning_messages.bad_argument_number(str(p.lineno(1)))
		#	exit(1)
		#expected_parameter = identifier.parameters[len(p[1].actual_parameters)]
		#if(not act_parameter.type == expected_parameter.type):
		#	print warning_messages.type_mismatch(str(act_parameter), str(p.lineno(1)))
		#	exit(1)
		p[1].actual_parameters.append(p[2]) 
		p[0] = p[1]

###########################################################################
#################### TODO DELETE SOMETIME IN THWE FUTURE   ################

def p_old_function_call(p):
	'''old_function_call : identifier LPAREN empty RPAREN
					 | identifier LPAREN expression_list RPAREN %prec ARG_COMMA'''
	identifier = Program_State.in_scope(p[1].name)
	if(not identifier):
		print warning_messages.undeclared_function(p[1].name, str(p.lineno(1)))
		exit(1)
	# Check for arguments
	act_param_list = p[3]
	if(not act_param_list):
		act_param_list = []
	if(not len(act_param_list) == len(identifier.parameters)):
		print warning_messages.bad_argument_number(str(p.lineno(1)))
		exit(1)
	for i in xrange(len(act_param_list)):
		actual = act_param_list[i].type
		regular = identifier.parameters[i].type
		if(not actual == regular):
			print warning_messages.type_mismatch(str(actual), str(p.lineno(1)))
			exit(1)
	

############################################################################


def p_expression_list(p):
	'''expression_list : expression 
	| 	expression COMMA expression_list %prec ARG_COMMA'''
	if(len(p) == 2):
		p[0] = [p[1]]
	else:
		p[3].insert(0,p[1])
		p[0] = p[3]





def p_unary_operation(p):
	'''unary_operation : ADDRESS expression %prec UADDRESS
					   | TIMES expression %prec USTAR  
					   | PLUS expression %prec UMINUS
					   | MINUS expression %prec UMINUS   
					   | NOT expression''' 
	p[1] = Operator(p.lineno(1),p[1],False)
	if(not p[1].unary_typecheck(p[2].type)):
		print warning_messages.invalid_type(str(p[1].lineno), [str(p[2].type)])
		exit(1)
	p[0]=Node_unary_operation(p[1],p[2],p[1].lineno)


def p_binary_operation(p):
	'''binary_operation : 	expression TIMES expression
						|   expression DIVIDE expression
						|   expression PLUS expression
						|   expression MINUS expression
						|   expression GT expression
						|   expression LT expression
						|   expression LE expression
						|   expression GE expression
						|   expression EQ expression
						|   expression NE expression
						|   expression OR expression
						|   expression AND expression
						|   expression COMMA expression
						|	expression MODULO expression '''
        p[2] = Operator(p.lineno(2),p[2],True)
 	if( not p[2].binary_typecheck(p[1].type,p[3].type)):
		print warning_messages.invalid_type(str(p[2].lineno), [str(p[1].type), str(p[3].type)])
		exit(1)
	p[0]=Node_binary_operation(p[2],p[1],p[3],p[2].lineno)



def p_left_assignment(p):
	'''left_assignment : INCREMENT expression %prec PRE_INCREMENT
					   | DECREMENT expression %prec PRE_DECREMENT'''
	p[1] = Operator(p.lineno(1),p[1],False)
	p[1].convert_to_equivalent_type()
	equiv=p[1]
	One_Type=Type("int",0)
	One_expr=Constant_Value(0,One_Type.type,1)

	# check the valid type of double in ++ and -- 
	if (p[2].type.isDouble()):
		One_Type=Type("double",0)
		One_expr=Constant_Value(0,One_Type.type,1.0)
	
	if(not equiv.binary_typecheck(One_Type,p[2].type)):
		print warning_messages.invalid_type(str(p[1].lineno), [str(p[2].type)] )
		exit(1)
	equiv_node=Node_binary_operation(equiv,One_expr,p[2],p[1].lineno)
	# Not an L-Value
	if(not new_l_val_check(p[2])):
		print warning_messages.not_l_value(str(p[2].lineno))
		exit(1)
	p[0]=Node_pre_unary_assignment(equiv_node.operator,p[2],p[1].lineno,equiv_node.type)


def p_right_assignment(p):
	'''right_assignment : expression INCREMENT
						| expression DECREMENT'''
	p[2] = Operator(p.lineno(2),p[2],False)
	p[2].convert_to_equivalent_type()
	equiv=p[2]
	One_Type=Type("int",0)
	One_expr=Constant_Value(0,One_Type.type,1)

	# check the valid type of double in ++ and -- 
	if (p[1].type.isDouble()):
		One_Type=Type("double",0)
		One_expr=Constant_Value(0,One_Type.type,1.0)

	if(not equiv.binary_typecheck(p[1].type,One_Type)):
		print warning_messages.invalid_type(str(p[2].lineno), [str(p[1].type)])
		exit(1)
	equiv_node=Node_binary_operation(equiv,One_expr,p[1],p[2].lineno)
	# Not an L-Value
	if(not new_l_val_check(p[1])):
		print warning_messages.not_l_value(str(p[1].lineno))
		exit(1)
	p[0]=Node_post_unary_assignment(equiv_node.operator,p[1],p[2].lineno,equiv_node.type)

def p_whole_assignment(p):
	'''whole_assignment : expression EQUALS expression
						| expression TIMESEQUAL expression
						| expression DIVEQUAL expression
						| expression MODEQUAL expression
						| expression PLUSEQUAL expression
						| expression MINUSEQUAL expression'''
	p[2] = Operator(p.lineno(2),p[2],True)
	if( not p[2].binary_typecheck(p[1].type,p[3].type)):
		print warning_messages.invalid_type(str(p[2].lineno), [str(p[1].type), str(p[3].type)])
		exit(1)
	equiv_node=Node_binary_operation(p[2],p[1],p[3],p[2].lineno)
	# Not an L-Value
	if(not new_l_val_check(p[1])):
		print warning_messages.not_l_value(str(p[1].lineno))
		exit(1)
	p[0]=Node_whole_assignment(p[2],p[1],p[3],p[2].lineno,equiv_node.type)



def p_type_casting(p):
	'''type_casting : LPAREN type RPAREN expression %prec TYPE_CAST_PAREN'''
	casted_expression=Type_cast(p[4], p[2], p.lineno(2))
	if not casted_expression.is_valid_type_cast():
		print warning_messages.not_allowed_typecast(str(p[4].type), str(p[2]), str(p.lineno(2)))
		exit(1)
	p[0]=casted_expression

def p_ternary_operation(p):
	'''ternary_operation : expression TERNARY expression COLON expression'''
	p[0] = Ternary(p[1], p[3], p[5], p.lineno(2))




def p_delete(p):
	'''delete : DELETE expression'''
	p[0]=Delete_Pointer(p[2])


def p_constant_value(p):
	'''constant_value : TRUE
	|	FALSE
	|	NULL
	|	constant_value_int
	|	constant_value_char
	|	constant_value_double
	| 	constant_value_string'''
	if(isinstance(p[1], Constant_Value)):
		p[0] = p[1]
	else:
		if(p[1] in ["true","false"]):
			c_type = "bool"
		else:
			c_type = "null"
		p[0] = Constant_Value(p.lineno(1), c_type, p[1])

def p_constant_value_int(p):
	'''constant_value_int : INTEGER'''
	p[0] = Constant_Value(p.lineno(1), "int", p[1])

def p_constant_value_double(p):
	'''constant_value_double : DOUBLE'''
	p[0] = Constant_Value(p.lineno(1), "double", p[1])

def p_constant_value_char(p):
	'''constant_value_char : CHAR'''
	p[0] = Constant_Value(p.lineno(1), "char", p[1])

def p_constant_value_string(p):
	'''constant_value_string : STRING'''
	p[0] = Constant_Value(p.lineno(1), "string", p[1])



def p_constant_expression(p): 
	'''constant_expression : expression'''
	if(isinstance(p[1], Constant_Value)):
		p[0] = p[1]
	else:
		print warning_messages.not_constant(str(p.lineno(1)))
		exit(1)


def p_empty(p):
    '''empty :'''


def p_error(p):
	print warning_messages.syntax_error_at(str(p.value), str(p.lineno) )
	exit(1)




