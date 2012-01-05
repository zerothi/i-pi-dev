#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/un.h>
#include <netdb.h> 

void error(const char *msg)
{   perror(msg);  exit(0);   }

void open_socket_(int *psockfd, char* host, int port, int inet)
{
   int sockfd, portno, n;
   struct hostent *server;

   struct sockaddr * psock; int ssock;
   if (inet>0)
   {  
      struct sockaddr_in serv_addr;      psock=(struct sockaddr *)&serv_addr;     ssock=sizeof(serv_addr);
      sockfd = socket(AF_INET, SOCK_STREAM, 0);
      if (sockfd < 0)  error("ERROR opening socket");
   
      server = gethostbyname(host);
      if (server == NULL)
      {
         fprintf(stderr, "ERROR, no such host %s \n", host);
         exit(0);
      }

      bzero((char *) &serv_addr, sizeof(serv_addr));
      serv_addr.sin_family = AF_INET;
      bcopy((char *)server->h_addr, (char *)&serv_addr.sin_addr.s_addr, server->h_length);
      serv_addr.sin_port = htons(port);
   }
   else
   {
      struct sockaddr_un serv_addr;      psock=(struct sockaddr *)&serv_addr;     ssock=sizeof(serv_addr);
      sockfd = socket(AF_UNIX, SOCK_STREAM, 0);
      bzero((char *) &serv_addr, sizeof(serv_addr));
      serv_addr.sun_family = AF_UNIX;
      strcpy(serv_addr.sun_path, "/tmp/wrappi_");
      strcpy(serv_addr.sun_path+12, host);
   }
   
   if (connect(sockfd, psock, ssock) < 0) error("ERROR connecting");

   *psockfd=sockfd;
}

void writebuffer_(int *psockfd, char *data, int* plen)
{
   int n;   
   int sockfd=*psockfd;
   int len=*plen;

   n = write(sockfd,data,len);
   if (n < 0) error("ERROR writing to socket");
}


void readbuffer_(int *psockfd, char *data, int* plen)
{
   int n, nr;
   int sockfd=*psockfd;
   int len=*plen;

   n = nr = read(sockfd,data,len);
   
   while (nr>0 && n<len )
   {  nr=read(sockfd,&data[n],len-n); n+=nr; }

   if (n == 0) error("ERROR reading from socket");
}


