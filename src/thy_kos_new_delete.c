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
	if ( in_list(Addr) ) return 0;
	AddrPtr temp = (AddrPtr) malloc(sizeof(address));
	newest_element->next = temp;
	newest_element = newest_element->next;
	newest_element->next = NULL;
	strcpy(newest_element->alocated_address,Addr);
	return 0;
}

int add_to_list (char * Addr){
	if (head == NULL) return construct_list(Addr);
	else return insert_to_list(Addr);
}


int delete_from_list(char * Addr){
	AddrPtr t = head; 
	if (t==NULL) return -1;
	if ( strcmp( t->alocated_address, Addr) == 0 ) {
		head = head -> next;
		free(t);
		return 1;
	}

	AddrPtr p = t->next;

	while (p!=NULL){
		if( strcmp( p->alocated_address, Addr) == 0 ) {
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
	char a[80];
	newest_element = (AddrPtr) malloc(sizeof(address));
	head = (AddrPtr) malloc(sizeof(address));
	newest_element = NULL;
	head = NULL;
	int dummy;

	while ( strcmp(a, "q\0") != 0){
		printf("Dwse mia dieythinsi na eisagw\n");
		scanf("%s",&a);
		dummy = add_to_list(a);
		//printf("%s\n", a);
		for(AddrPtr t = head; t!=NULL; t=t->next){
		 printf("%s||", t->alocated_address);
		}
		printf("\n");
	}

	while ( strcmp(a, "w\0") != 0){
		printf("Dwse mia dieythinsi na diagrapsw\n");
		scanf("%s",&a);
		dummy = delete_from_list(a);
		//printf("%s\n", a);
		for(AddrPtr t = head; t!=NULL; t=t->next){
		 printf("%s||", t->alocated_address);
		}
		printf("\n");
	}
	
	return 0;
}