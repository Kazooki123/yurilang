#include "dns.h"
#include <stdio.h>
#include <string.h>

int libyuri_dns_resolve(const char *hostname, char *out_ip, size_t out_len) {
    if (!hostname || !out_ip || out_len == 0) return -1;

    struct addrinfo hints, *res = NULL;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family   = AF_UNSPEC;   /* IPv4 or IPv6 */
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(hostname, NULL, &hints, &res) != 0) return -1;

    void *addr_ptr = NULL;

    if (res->ai_family == AF_INET) {
        struct sockaddr_in *ipv4 = (struct sockaddr_in *)res->ai_addr;
        addr_ptr = &ipv4->sin_addr;
    } else if (res->ai_family == AF_INET6) {
        struct sockaddr_in6 *ipv6 = (struct sockaddr_in6 *)res->ai_addr;
        addr_ptr = &ipv6->sin6_addr;
    } else {
        freeaddrinfo(res);
        return -1;
    }

    if (!inet_ntop(res->ai_family, addr_ptr, out_ip, (socklen_t)out_len)) {
        freeaddrinfo(res);
        return -1;
    }

    freeaddrinfo(res);
    return 0;
}

int libyuri_dns_reverse(const char *ip, char *out_host, size_t out_len) {
    if (!ip || !out_host || out_len == 0) return -1;

    struct sockaddr_in sa;
    memset(&sa, 0, sizeof(sa));
    sa.sin_family = AF_INET;

    if (inet_pton(AF_INET, ip, &sa.sin_addr) != 1) return -1;

    if (getnameinfo((struct sockaddr *)&sa, sizeof(sa),
                    out_host, (socklen_t)out_len,
                    NULL, 0, NI_NAMEREQD) != 0) return -1;

    return 0;
}
