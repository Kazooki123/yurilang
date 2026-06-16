#ifndef LIBYURI_SOCKETS_H
#define LIBYURI_SOCKETS_H

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    typedef SOCKET yuri_socket_t;
    #define YURI_INVALID_SOCKET INVALID_SOCKET
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <unistd.h>
    typedef int yuri_socket_t;
    #define YURI_INVALID_SOCKET (-1)
#endif

/* Create a raw TCP socket. Returns YURI_INVALID_SOCKET on failure. */
yuri_socket_t libyuri_socket_create(void);

/* Set socket to non-blocking mode.
 * Returns 0 on success, -1 on failure. */
int libyuri_socket_set_nonblocking(yuri_socket_t sock);

/* Set SO_REUSEADDR on socket.
 * Returns 0 on success, -1 on failure. */
int libyuri_socket_set_reuseaddr(yuri_socket_t sock);

void libyuri_socket_close(yuri_socket_t sock);

/* Returns 1 if socket is valid, 0 otherwise. */
int libyuri_socket_is_valid(yuri_socket_t sock);

#endif /* LIBYURI_SOCKETS_H */
