import sys
import os
sys.path.insert(0, os.getcwd() + "/src/")

# Warnings Library
import warning_messages

import ply.lex as lex
from ply.lex import TOKEN
import ply.yacc as yacc

import edsger_lexer
import edsger_parser
import edsger_semantic_classes
import edsger_ir

#############
## GLOBALS ##
#############

lex_debug = 0
parse_debug = 0

# Output file
f_out = sys.stdout

# Used to check for re-including the same libraries
included_libs = []

# Initializing the lexer module
lexer_base = lex.lex(module=edsger_lexer)
parser_base = yacc.yacc(module=edsger_parser)

# All the different lexer instances
lexers = []
parsers = []


###############
## FUNCTIONS ##
###############


# An exit function that closes and removes any output file 
def exit_func(errnum):
    if(len(sys.argv) == 3 and not (f_out == sys.stdout)):
        f_out.close()
        if(not (lex_debug or parse_debug)):
            os.remove(sys.argv[2])
    exit(errnum)

# Correct use of command
def correct_use():
    if (not len(sys.argv) in [2,3]):
        print "Compiler must be called with the file name as an argument"
        print "and an optional second argument as an output file"
        print "Example use: python edsger_compiler.py input.edg output.out"
        exit_func(1)

# Does the file exist?
def file_exists(file_name):
    if(not os.path.isfile(file_name) ):
        print warning_messages.wrong_file_name(file_name)
        exit_func(1)

# The tokenizing process 
def lexer_process(text, curr_lexer):

    # Build the lexer and clone it so that we can handle includes
    curr_lexer.input(text)
    lexers.append(curr_lexer)

    lexer = curr_lexer.clone()
    lexer.input(text)

    last_newline_pos = 0
    ## For every token    
    for tok in iter(lexer.token, None):
        
        ## Handle the include with recursion        
        if(tok.type == 'INCLUDE'):

            lib_name = tok.value.split('"')[1]
            if(not lib_name in included_libs):
                
                ## Include the library in the list
                included_libs.append(lib_name)
                
                ## Open and read the library               
                file_exists(lib_name)

                f_inc = open(lib_name,"r")                
                inc_data = f_inc.read()
                f_inc.close()

                # Create a new lexer for the library
                lib_lexer = lex.lex(module=edsger_lexer)
                warning_messages.file_name = lib_name
                lexer_process(inc_data, lib_lexer)
            else:
                print warning_messages.reinclude_library_error(lib_name)
                exit_func(1)
        
        ## For everything except include print it
        else:

            # Print out all the tokens if debuging
            if(lex_debug):
                f_out.write(str(tok) + "\n")
    return

# The parse process
def parse(data, lexer, curr_scope):
    edsger_parser.Program_State.variable_scope_stack = [curr_scope[0]]
    edsger_parser.Program_State.function_scope_stack = [curr_scope[1]]
    if(not curr_scope):
        edsger_parser.Program_State.push({})
    if(parse_debug):
        p = parser_base.parse(data,lexer=lexer, debug=True)
    else:
        p = parser_base.parse(data,lexer=lexer)
    return (p, (edsger_parser.Program_State.variable_scope_stack[0], edsger_parser.Program_State.function_scope_stack[0] ))


# TODO Encapsulate all of this into a main function
correct_use()
file_exists(sys.argv[1])
# Has the user defined an output file?
if(len(sys.argv) == 3):
    f_out = open(sys.argv[2],"w")    

# Open the file and call the lexer
input_file = open(sys.argv[1],"r")
warning_messages.file_name = sys.argv[1]
lexer_process(input_file.read(), lexer_base)

# After that we can call parser on each separate lexers[i]
initial_scope = ({}, {})
# We call all the parser on the libraries first
# And then we have the scope to call it also on the main program
for lexer_file in lexers[1:]:
    warning_messages.file_name = "library"
    curr_parser,initial_scope = parse( lexer_file.lexdata, lexer_file, initial_scope)
    parsers.append(curr_parser)

warning_messages.file_name = sys.argv[1]
curr_parser,scope = parse( lexers[0].lexdata, lexers[0], initial_scope)
#print "No syntax error at program: " + sys.argv[1] + " :)"
parsers.insert(0, curr_parser)

# DEBUG ONLY
edsger_semantic_classes.AST.print_tree(f_out)

tree_head = edsger_semantic_classes.AST.head

edsger_ir.IR_State.code_generation(tree_head)




