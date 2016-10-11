#include <stdlib.h>
#include <stdio.h>
#include <string.h>
//DYNAMICALLY LINK IT TO THE PYTHON SCRIPT
//gcc -fPIC -shared -o libstrtold.so thy_kos_strold.c

char * strtolden(char * strn){
	
  char* pEnd;
  __float80 d1;
  d1 = strtold (strn, &pEnd);
  char * output = (char *) malloc(80);
  snprintf(output,80,"%La", d1);
  return output;
}
