#ifndef LIBYURI_TCP_H
#define LIBYURI_TCP_H

#include "sockets.h"
#include <stddef.h>

/* Connect to a remote host by IP string and port.
 * Returns a valid socket on success, YURI_INVALID_SOCKET on failure. */
yuri_socket_t libyuri_tcp_connect(const char *ip, int port);

/* Send data over a connected socket.
 * Returns bytes sent on success, -1 on failure. */
int libyuri_tcp_send(yuri_socket_t sock, const char *data, int len);

/* Receive data from a connected socket into `buf` (size `buf_len`).
 * Returns bytes received, 0 on disconnect, -1 on failure. */
int libyuri_tcp_recv(yuri_socket_t sock, char *buf, int buf_len);

/* Bind and listen on a port (server side).
 * Returns a listening socket on success, YURI_INVALID_SOCKET on failure. */
yuri_socket_t libyuri_tcp_listen(int port, int backlog);

/* Accept an incoming connection from a listening socket.
 * Returns a connected client socket, YURI_INVALID_SOCKET on failure. */
yuri_socket_t libyuri_tcp_accept(yuri_socket_t listen_sock);

/* Close a TCP connection. */
void libyuri_tcp_close(yuri_socket_t sock);

#endif /* LIBYURI_TCP_H */
