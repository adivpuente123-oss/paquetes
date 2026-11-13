#ifndef PDF_LINEARIZATION_WARNINGS_H
#define PDF_LINEARIZATION_WARNINGS_H
#include <stdio.h>
#include <string.h>

/* Only these qpdf 12.4.2 hint-table warnings may pass the input check.
   Syntax, xref reconstruction, damaged streams and all unknown warnings fail. */
static int hint_message_allowed(const char *msg){
 unsigned a,b,c;int end=-1;
 if(sscanf(msg,"part %u is empty but nshared_total > nshared_first_page%n",&a,&end)==1&&end>=0&&msg[end]==0)return 1;
 end=-1;
 if(sscanf(msg,"page %u has shared identifier entries%n",&a,&end)==1&&end>=0&&msg[end]==0)return 1;
 end=-1;
 if(sscanf(msg,"page %u: shared object %u: in hint table but not computed list%n",&a,&b,&end)==2&&end>=0&&msg[end]==0)return 1;
 end=-1;
 if(sscanf(msg,"object count mismatch for page %u: hint table = %u; computed = %u%n",&a,&b,&c,&end)==3&&end>=0&&msg[end]==0)return 1;
 return 0;
}
static int hint_warnings_only(FILE *f){
 char line[65536];int found=0;
 while(fgets(line,sizeof(line),f)){
  size_t n=strlen(line);
  if(!n||((line[n-1]!='\n')&&!feof(f)))return 0;
  while(n&&(line[n-1]=='\r'||line[n-1]=='\n'))line[--n]=0;
  char *warning=strstr(line,"WARNING:");
  if(!warning)continue;
  if(warning!=line||strncmp(line,"WARNING: ",9))return 0;
  /* After WARNING: comes an absolute Windows path, then ': ' and a message. */
  char *separator=strstr(line+9,": ");
  if(!separator||!hint_message_allowed(separator+2))return 0;
  found=1;
 }
 return !ferror(f)&&found;
}
#endif
