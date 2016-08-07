## Warning messages

file_name = ""
def error_header():
	return "---ERROR!! In file: " + file_name + "\n"

def reinclude_library_error(lib_name):
    return error_header() + "You tried re-including the library with name: " + lib_name + " ---"

def wrong_file_name(file_name):
    return error_header() + "No file with name: " + file_name + " ---"
 
def wrong_include_position():
    return error_header() + "#include statement is not in the beginning of a line"    

def syntax_error_at(value, line):
	return error_header() + "Syntax error at \"" + value + "\" at line: " + line

def not_constant(line):
	return error_header() + "The expression at line: " + line + " is not constant"

def not_int_index(line):
	return error_header() + "The index at line: " + line + " is not an integer"

def redeclaration(name, lineno):
	return "---WARNING!! You redeclared identifier: " + name + " that was declared at line: " + lineno

def undeclared_variable(name, lineno):
	return error_header() + "Undeclared variable: " + name + " at line: " + lineno

def undeclared_function(name, lineno):
	return error_header() + "Undeclared function: " + name + " at line: " + lineno

def non_valid_dereference(lineno):
	return error_header() + "Dereferencing of non pointer object at line: " + lineno

def not_allowed_typecast(from_t, to_t, lineno):
	return error_header() + "Cannot cast from: " + from_t + " to: " + to_t + " at line: " + lineno

def redefine_function(name, lineno)	:
	return "---WARNING!! You redeclared function: " + name + " that was declared at line: " + lineno

def outside_loop(name, lineno):
	return error_header() + name + " statement at line: " + lineno + " is not inside a loop "

def loop_tag_doesnt_exist(name, lineno):
	return error_header() + "Loop name: " + name + " at line: " + lineno + " doesn't exist"

def loop_name_exists(name, lineno):
	return error_header() + "Loop name: " + name + " at line: " + lineno + " already exists"	

def invalid_type(lineno, types):
	return error_header() + "Invalid type in line " + lineno + " Actual: " + " - ".join(types)

def predicate_not_bool(lineno):
	return error_header() + "Predicate is not boolean in line: " + lineno

def ternary_expr_type_mismatch(lineno):
	return error_header() + "Expressions at ternary are not the same type in line: " + lineno

def bad_argument_number(lineno):
	return error_header() + "Bad Argument number in line: " + lineno

def type_mismatch(actual, lineno):
	return error_header() + "Type mismatch, Actual: " + actual + " in line: " + lineno	

def is_not_a_pointer(lineno):
	return error_header() + "Expression is not of type pointer in line: " + lineno	
def not_l_value(lineno):
	return error_header() + "Expression is not an L-Value in line: " + lineno