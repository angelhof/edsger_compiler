import sys
import os
from subprocess import Popen, PIPE
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
class Globals(object):
    # File args
    args = []
    f_out_name = "a.out"

lex_debug = 0
parse_debug = 0
sem_debug = 0
ir_debug = 1

# Arguments
parsed_args = {"-O" : False ,
               "-i" : False ,
               "-f" : False }



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
    if (not ((len(Globals.args) in [1,2] and not parsed_args["-i"] and not parsed_args["-f"])
        or (len(Globals.args) == 0 and ( parsed_args["-i"] or parsed_args["-f"])))):
        print "Example use: ./cedsg [-i] | [-f] | [-O] source.eds [executable]"
        print "If -i or -f is passed as an argument no filename should be passed"
        exit_func(1)

def parse_args():
    Globals.args = sys.argv[1:]
    i = 0
    while True:
        try:
            curr_arg = Globals.args[i]
        except:
            break
        if(curr_arg[0] == "-" and curr_arg not in parsed_args):
            print " _____       _   _   _               _____    _           \n\
/  __ \     | | | | (_)             |  ___|  | |          \n\
| /  \/_   _| |_| |_ _ _ __   __ _  | |__  __| |___  __ _ \n\
| |   | | | | __| __| | '_ \ / _` | |  __|/ _` / __|/ _` |\n\
| \__/\ |_| | |_| |_| | | | | (_| | | |__| (_| \__ \ (_| |\n\
 \____/\__,_|\__|\__|_|_| |_|\__, | \____/\__,_|___/\__, |\n\
                              __/ |                  __/ |\n\
                             |___/                  |___/ "
            print "Example use: ./cedsg [-i] | [-f] | [-O] source.eds [executable]"
            print "If -i or -f is passed as an argument no filename should be passed"
            exit_func(1) 
        if(curr_arg in parsed_args):
            parsed_args[curr_arg] = True
            Globals.args.pop(i)
        elif(i+1 < len(Globals.args)):
            i += 1
        else:
            break

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


parse_args()

correct_use()
if(not parsed_args["-i"] and not parsed_args["-f"]):
    file_exists(Globals.args[0])
    input_file = open(Globals.args[0],"r")
    warning_messages.file_name = Globals.args[0]

    if(len(Globals.args) == 2):
        Globals.f_out_name = Globals.args[1]
        #f_out = open(Globals.args[1],"w")
    else:
        Globals.f_out_name = "a.out"
        #f_out = open("a.out","w")   
else:
    input_file = sys.stdin
    f_out = sys.stdout

# Has the user defined an output file?


# Open the file and call the lexer
lexer_process(input_file.read(), lexer_base)

# After that we can call parser on each separate lexers[i]
initial_scope = ({}, {})
# Tree heads
tree_heads = []
# We call all the parser on the libraries first
# And then we have the scope to call it also on the main program
for lexer_file in lexers[1:]:
    warning_messages.file_name = "library"
    curr_parser,initial_scope = parse( lexer_file.lexdata, lexer_file, initial_scope)
    parsers.append(curr_parser)
    tree_heads.append(edsger_semantic_classes.AST.head)

curr_parser,scope = parse( lexers[0].lexdata, lexers[0], initial_scope)
#print "No syntax error at program: " + sys.argv[1] + " :)"
parsers.insert(0, curr_parser)
tree_heads.insert(0, edsger_semantic_classes.AST.head)

#print tree_heads

# DEBUG ONLY
if(sem_debug):
    edsger_semantic_classes.AST.print_tree(f_out)

# edsger_ir.IR_State.rec_code_generation(tree_heads[0])
# edsger_ir.IR_State.code_generation(tree_heads[0])
ir_code = edsger_ir.IR_State.all_code_generation(tree_heads)

if(ir_debug):
    print ir_code
'''
Execute the llc, and clang commands
'''
if(parsed_args["-i"]):
    f_out.write(str(ir_code))

if(parsed_args["-f"] or (not parsed_args["-i"] and not parsed_args["-f"])):
    if(parsed_args["-O"]):
        p1 = Popen(['llc','-O2', '-mtriple=x86_64-unknown-gnulinux'], stdin=PIPE, stdout=PIPE)
    else:    
        p1 = Popen(['llc', '-mtriple=x86_64-unknown-gnulinux'], stdin=PIPE, stdout=PIPE)
    assembly = p1.communicate(str(ir_code))[0]
    llc_ret = p1.wait()
    if(llc_ret):
        print "Error: llc"
        exit(1)
    if(parsed_args["-f"]):
        f_out.write(assembly)
    else:
        name = "__temp.s"
        while(os.path.isfile(name) ):
            name = "_" + name
        f_temp = open(name, "w")
        f_temp.write(assembly)
        f_temp.close()
        if(parsed_args["-O"]):
            p2 = Popen(['clang','-O2', name, 'obj/lib.a', 'obj/libnew.a', '-o', Globals.f_out_name], stdin=PIPE, stdout=PIPE)
        else:    
            p2 = Popen(['clang', name, 'obj/lib.a', 'obj/libnew.a', '-o', Globals.f_out_name], stdin=PIPE, stdout=PIPE)
        clang_ret = p2.wait()
        os.system("rm " + name)
        if(clang_ret):
            print "Error: clang"
            exit(1)