#include <stdlib.h>
#include <stdio.h>
#include <string.h>

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
			else return 1;
		}
	}
	return 1;
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
	if (t==NULL) return -1;
	if ( ( t->Matrix_alocated_address == x) ) {
		Matrix_head = Matrix_head -> next;
		free(t);
		return 1;
	}

	Matrix_AddrPtr p = t->next;

	while (p!=NULL){
		if( p->Matrix_alocated_address == x ) {
			t->next = p->next;
			free(p);
			return 1;
		}
		t=p;
		p=p->next;
	}
	return 0;
}

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