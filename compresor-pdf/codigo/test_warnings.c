#include "linearization_warnings.h"
#include <assert.h>
#include <stdlib.h>

static int classify(const char *text){
 FILE *f=tmpfile();assert(f);fputs(text,f);rewind(f);
 int result=hint_warnings_only(f);fclose(f);return result;
}
int main(int argc,char **argv){
 if(argc==2){FILE *f=fopen(argv[1],"rb");if(!f)return 2;int allowed=hint_warnings_only(f);fclose(f);return allowed?0:1;}
 const char *allowed[]={
  "part 8 is empty but nshared_total > nshared_first_page",
  "page 0 has shared identifier entries",
  "page 1: shared object 854: in hint table but not computed list",
  "object count mismatch for page 1: hint table = 54; computed = 61"
 };
 char line[4096];
 for(int i=0;i<4;i++){
  assert(hint_message_allowed(allowed[i]));
  snprintf(line,sizeof(line),"checking C:\\example.pdf\r\nWARNING: C:\\example.pdf: %s\r\nqpdf: operation succeeded with warnings\r\n",allowed[i]);
  assert(classify(line));
  snprintf(line,sizeof(line),"WARNING: C:\\example.pdf: %s EXTRA\n",allowed[i]);assert(!classify(line));
 }
 assert(!classify("checking C:\\example.pdf\n"));
 assert(!classify("WARNING: C:\\example.pdf: file is damaged\n"));
 assert(!classify("WARNING: C:\\example.pdf: object count mismatch for page 1: hint table = 2\n"));
 assert(!classify("WARNING: C:\\example.pdf: page 0 has shared identifier entries\nWARNING: C:\\example.pdf: attempting to reconstruct cross-reference table\n"));
 assert(!classify("WARNING: C:\\example.pdf: error decoding stream data\n"));
 assert(!classify("WARNING: C:\\example.pdf: unknown warning\n"));
 assert(!classify("prefix WARNING: C:\\example.pdf: page 0 has shared identifier entries\n"));
 char *longline=malloc(70001);assert(longline);memset(longline,'X',70000);longline[70000]=0;assert(!classify(longline));free(longline);
 puts("PASS: avisos conocidos aceptados; avisos mixtos, estructurales, desconocidos, truncados y demasiado largos rechazados");
 return 0;
}
