#ifndef LIBYURI_DNS_H
#define LIBYURI_DNS_H

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
#else
    #include <sys/socket.h>
    #include <netdb.h>
    #include <arpa/inet.h>
#endif

#include <stddef.h>

/* Resolve a hostname to an IPv4 address string.
 * Output is written into `out_ip` (caller must provide at least 46 bytes).
 * Returns 0 on success, -1 on failure. */
int libyuri_dns_resolve(const char *hostname, char *out_ip, size_t out_len);

/* Reverse lookup: IP string -> hostname.
 * Returns 0 on success, -1 on failure. */
int libyuri_dns_reverse(const char *ip, char *out_host, size_t out_len);

#endif /* LIBYURI_DNS_H */
