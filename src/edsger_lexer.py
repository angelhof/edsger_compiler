import ply.lex as lex
import re
from ply.lex import TOKEN

tokens = [
    'INCLUDE',
	#Constants
	'DOUBLE','INTEGER','CHAR','STRING',
	#Comments
	'ONELINECOMMENT','MANYLINECOMMENT',
	# Operators (+,-,*,/,%,|,&,~,^,<<,>>, ||, &&, !, <, <=, >, >=, ==, !=)
	'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULO','OR', 'AND', 'NOT','LT', 'LE', 'GT', 'GE', 'EQ', 'NE',
	# Assignment (=, *=, /=, %=, +=, -=, <<=, >>=, &=, ^=, |=)
	'EQUALS', 'TIMESEQUAL', 'DIVEQUAL', 'MODEQUAL', 'PLUSEQUAL', 'MINUSEQUAL',
	# Increment/decrement (++,--)
	'INCREMENT', 'DECREMENT',
	# Ternary operator (?)
	'TERNARY',
	'ID',
    'RBRACE',
    'LBRACE',
    'RBRACKET',
    'RPAREN',
    'LBRACKET',
    'LPAREN',
    'ADDRESS',
    'SEMI',
    'COMMA',
    'COLON',
    'NEWLINE',
    'WHITECHARACTERS',
	'IGNORE'
]

reserved = {
    # Types
    'bool' : 'BOOLTYPE', 'char' : 'CHARTYPE', 'double': 'DOUBLETYPE',  'int'  : 'INTTYPE', 'void' : 'VOID',
    # Bool Constants
    'true' : 'TRUE', 'false': 'FALSE',
    # Allocation operators
    'new'  : 'NEW', 'delete': 'DELETE',
    # If else 
    'if'   : 'IF', 'else': 'ELSE',
    # For
    'for' : 'FOR',
    # Byreference
    'byref' : 'BYREF',
    # Break and continue
    'break' : 'BREAK', 'continue' : 'CONTINUE',
    # Null value
    'NULL' : 'NULL',
    # Return
    'return' : 'RETURN'
}

tokens += reserved.values()

#Some basic building blocks
escaped = r'(n|t|r|0|\\|\'|\"|x[a-f0-9][a-f0-9])'
single_quote = r'\''
double_quote = r'\"'
string = double_quote + r'(\\\"|[^\"\n])*' + double_quote

# Tokens

# Include commands
def t_INCLUDE(t):
    r'(^|\n)\#include[ ]+\"(\\\"|[^\"])*\"'
    return t


# Constants
t_CHAR = single_quote + r'(.|\\(n|t|r|0|\\|\'|\"|x[a-f0-9][a-f0-9]))' + single_quote
t_STRING = string

def t_DOUBLE (t):
    r'[0-9]+\.[0-9]+([eE](\+|-)?[0-9]+)?'
    # TODO Delete the next line
    #t.value = float(t.value)
    return t

def t_INTEGER (t):
    r'[0-9]+'
    # TODO Delete the next line
    #t.value = int(t.value)
    return t




# Comments
def t_ONELINECOMMENT(t):
    r'//.*\n'
    t.lexer.lineno += 1
    return None

def t_MANYLINECOMMENT(t):
    r'/\*([^*]|[\r\n]|(\*+([^*/]|[\r\n])))*\*+/'
    newlines = re.findall(r"\n", t.value)
    t.lexer.lineno += len(newlines)
    return None


# Operators
t_ADDRESS          = r'&'
t_PLUS             = r'\+'
t_MINUS            = r'-'
t_TIMES            = r'\*'
t_DIVIDE           = r'/'
t_MODULO           = r'%'
t_OR               = r'\|\|'
t_AND              = r'&&'
t_NOT              = r'!'
t_LT               = r'<'
t_GT               = r'>'
t_LE               = r'<\='
t_GE               = r'>\='
t_EQ               = r'\=\='
t_NE               = r'!\='


# Assignment operators
t_EQUALS           = r'\='
t_TIMESEQUAL       = r'\*\='
t_DIVEQUAL         = r'/\='
t_MODEQUAL         = r'%\='
t_PLUSEQUAL        = r'\+\='
t_MINUSEQUAL       = r'-\='


# Increment/decrement
t_INCREMENT        = r'\+\+'
t_DECREMENT        = r'--'


# ?
t_TERNARY          = r'\?'


# Delimeters
t_LPAREN           = r'\('
t_RPAREN           = r'\)'
t_LBRACKET         = r'\['
t_RBRACKET         = r'\]'
t_LBRACE           = r'\{'
t_RBRACE           = r'\}'
t_COMMA            = r','
t_SEMI             = r';'
t_COLON            = r':'


# Identifiers
def t_ID(t):
    r'[a-zA-Z][a-zA-Z0-9_]*'
    if t.value in reserved:
        t.type = reserved[ t.value ]
    return t


# Ignored characters
def t_NEWLINE(t): 
    r'\n'
    # TODO Maybe add the line check else too
    t.lexer.lineno += 1
    return None

def t_WHITECHARACTERS(t):
    r'[ \t]+'
    return None

# Only for debugging
# t_IGNORE = r'.'

def t_error(t): 
	print("Illegal character '{0}' at line: {1}".format(t.value[0], t.lexer.lineno)) 
	exit(1)


