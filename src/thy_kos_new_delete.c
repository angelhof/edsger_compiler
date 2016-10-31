#include <stdlib.h>
#include <stdio.h>
#include <string.h>

struct Addresses{
	char alocated_address[80];
	struct Addresses * next;
} address;

typedef struct Addresses * AddrPtr;

AddrPtr newest_element;
AddrPtr head;


int construct_list (char * Addr){
	head = (AddrPtr) malloc(sizeof(address));
	head->next = NULL;
	strcpy(head->alocated_address,Addr);
	newest_element = head;
	return 0; 
}

int in_list(char * Addr){
	for(AddrPtr t = head; t!=NULL; t=t->next){
		if( !strcmp( t->alocated_address, Addr) ) return 1;
	}
	return 0;
}

int insert_to_list (char * Addr){
	if ( in_list(Addr) ) exit(5);
	AddrPtr temp = (AddrPtr) malloc(sizeof(address));
	newest_element->next = temp;
	newest_element = newest_element->next;
	newest_element->next = NULL;
	strcpy(newest_element->alocated_address,Addr);
	return 0;
}

int LongToString(long x, char * SpecAddr){
	const int n = snprintf(NULL, 0, "%lu", x);
	if (n <= 0) return 1;
	char buf[n+1];
	int c = snprintf(buf, n+1, "%lu", x);
	buf[n] == '\0';
	if (!(c == n)) return 1;
	strcpy(SpecAddr, buf);
	return 0;
}

int add_to_list (long x){
	char Addr[80];
	if (LongToString(x,Addr)){
		exit(1);	
	} 
	if (head == NULL) return construct_list(Addr);
	else return insert_to_list(Addr);
}


int delete_from_list(long x){
	char Addr[80];
	if (LongToString(x,Addr)){
		exit(1);	
	} 
	AddrPtr t = head; 
	if (t==NULL){
		printf("This pointer was not created with new!!");
		exit(1);
	}
	if ( strcmp( t->alocated_address, Addr) == 0 ) {
		head = head -> next;
		free(t);
		return 0;
	}

	AddrPtr p = t->next;

	while (p!=NULL){
		if( strcmp( p->alocated_address, Addr) == 0 ) {
			t->next = p->next;
			free(p);
			return 0;
		}
		t=p;
		p=p->next;
	}

	
	printf("This pointer was not created with new!!");
	exit(1);
}

struct Matrix_Addresses{
	long Matrix_alocated_address;
	long size;
	struct Matrix_Addresses * next;
} Matrix_address;

typedef struct Matrix_Addresses * Matrix_AddrPtr;

Matrix_AddrPtr Matrix_newest_element;
Matrix_AddrPtr Matrix_head;

int pointers_in_the_same_matrix(long x1, long x2){
	for(Matrix_AddrPtr t = Matrix_head; t!=NULL; t=t->next){
		if(  (t->Matrix_alocated_address <= x1) && (t->Matrix_alocated_address + t->size > x1)) {
			if ((t->Matrix_alocated_address <= x2) && (t->Matrix_alocated_address + t->size > x2)){
				return 0;
			}
			else{ 
				printf("The compared pointers are not part of the same array");
				exit(1);
			}
		}
	}
	printf("The compared pointers are not part of the same array");
	exit(1);
}


int Matrix_construct_list (long Addr, long sm){
	Matrix_head = (Matrix_AddrPtr) malloc(sizeof(Matrix_address));
	Matrix_head->next = NULL;
	Matrix_head->size=sm;
	Matrix_head->Matrix_alocated_address = Addr;
	Matrix_newest_element = Matrix_head;
	return 0; 
}

int Matrix_in_list(long Addr){
	for(Matrix_AddrPtr t = Matrix_head; t!=NULL; t=t->next){
		if( ( t->Matrix_alocated_address == Addr) ) return 1;
	}
	return 0;
}

int Matrix_insert_to_list (long Addr, long sm){
	if ( Matrix_in_list(Addr) ) return 0;
	Matrix_AddrPtr temp = (Matrix_AddrPtr) malloc(sizeof(Matrix_address));
	Matrix_newest_element->next = temp;
	Matrix_newest_element = Matrix_newest_element->next;
	Matrix_newest_element->next = NULL;
	Matrix_newest_element->size = sm;
	Matrix_newest_element->Matrix_alocated_address = Addr;
	return 0;
}

int Matrix_add_to_list (long x, long sm){
	if (Matrix_head == NULL) return Matrix_construct_list(x,sm);
	else return Matrix_insert_to_list(x,sm);
}


int Matrix_delete_from_list(long x){
	Matrix_AddrPtr t = Matrix_head; 
	if (t==NULL) return 0;
	if ( ( t->Matrix_alocated_address == x) ) {
		Matrix_head = Matrix_head -> next;
		free(t);
		return 0;
	}

	Matrix_AddrPtr p = t->next;

	while (p!=NULL){
		if( p->Matrix_alocated_address == x ) {
			t->next = p->next;
			free(p);
			return 0;
		}
		t=p;
		p=p->next;
	}
	return 0;
}


/*
int main(int argc, char const *argv[])
{ 
	long a,b;
	Matrix_newest_element = NULL;
	Matrix_head = NULL;
	int dummy;

	while ( a != 19999999){
		printf("Dwse mia dieythinsi na eisagw\n");
		scanf("%ld %ld",&a, &b);
		dummy = Matrix_add_to_list(a,b);
		//printf("%s\n", a);
		for(Matrix_AddrPtr t = Matrix_head; t!=NULL; t=t->next){
		 printf("%ld~%ld||", t->Matrix_alocated_address,t->size);
		}
		printf("\n");
	}

	while ( a != 1){
		printf("Dwse mia dieythinsi na diagrapsw\n");
		scanf("%ld",&a);
		dummy = Matrix_delete_from_list(a);
		//printf("%s\n", a);
		for(Matrix_AddrPtr t = Matrix_head; t!=NULL; t=t->next){
		 printf("%ld~%ld||", t->Matrix_alocated_address,t->size);
		}
		printf("\n");
	}

	while ( a != 2){
		printf("Dwse 2 pointers na sou pw tinos einai to paidi\n");
		scanf("%ld %ld",&a,&b);
		dummy = pointers_in_the_same_matrix(a,b);
		//printf("%s\n", a);
		for(Matrix_AddrPtr t = Matrix_head; t!=NULL; t=t->next){
		 printf("%ld~%ld||", t->Matrix_alocated_address,t->size);
		}
		printf("\n");
		printf("====%d====\n",dummy);
	}

	
	return 0;
}

*/
/*
int main(int argc, char const *argv[])
{ 
	long a;
	newest_element = (AddrPtr) malloc(sizeof(address));
	head = (AddrPtr) malloc(sizeof(address));
	newest_element = NULL;
	head = NULL;
	int dummy;

	while ( a != 0){
		printf("Dwse mia dieythinsi na eisagw\n");
		scanf("%ld",&a);
		dummy = add_to_list(a);
		//printf("%s\n", a);
		for(AddrPtr t = head; t!=NULL; t=t->next){
		 printf("%s||", t->alocated_address);
		}
		printf("\n");
	}

	while ( a != 0){
		printf("Dwse mia dieythinsi na diagrapsw\n");
		scanf("%ld",&a);
		dummy = delete_from_list(a);
		//printf("%s\n", a);
		for(AddrPtr t = head; t!=NULL; t=t->next){
		 printf("%s||", t->alocated_address);
		}
		printf("\n");
	}
	
	return 0;
}

*/