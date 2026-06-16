#include "tcp.h"
#include "sockets.h"

#include <string.h>
#include <stdio.h>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
#endif

yuri_socket_t libyuri_tcp_connect(const char *ip, int port) {
    if (!ip || port <= 0 || port > 65535) return YURI_INVALID_SOCKET;

    yuri_socket_t sock = libyuri_socket_create();
    if (!libyuri_socket_is_valid(sock)) return YURI_INVALID_SOCKET;

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_port   = htons((unsigned short)port);

    if (inet_pton(AF_INET, ip, &addr.sin_addr) != 1) {
        libyuri_socket_close(sock);
        return YURI_INVALID_SOCKET;
    }

    if (connect(sock, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        libyuri_socket_close(sock);
        return YURI_INVALID_SOCKET;
    }

    return sock;
}

int libyuri_tcp_send(yuri_socket_t sock, const char *data, int len) {
    if (!libyuri_socket_is_valid(sock) || !data || len <= 0) return -1;
    return (int)send(sock, data, len, 0);
}

int libyuri_tcp_recv(yuri_socket_t sock, char *buf, int buf_len) {
    if (!libyuri_socket_is_valid(sock) || !buf || buf_len <= 0) return -1;
    return (int)recv(sock, buf, buf_len, 0);
}

yuri_socket_t libyuri_tcp_listen(int port, int backlog) {
    if (port <= 0 || port > 65535) return YURI_INVALID_SOCKET;

    yuri_socket_t sock = libyuri_socket_create();
    if (!libyuri_socket_is_valid(sock)) return YURI_INVALID_SOCKET;

    libyuri_socket_set_reuseaddr(sock);

    struct sockaddr_in addr;
    memset(&addr, 0, sizeof(addr));
    addr.sin_family      = AF_INET;
    addr.sin_port        = htons((unsigned short)port);
    addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(sock, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        libyuri_socket_close(sock);
        return YURI_INVALID_SOCKET;
    }

    if (listen(sock, backlog > 0 ? backlog : 5) != 0) {
        libyuri_socket_close(sock);
        return YURI_INVALID_SOCKET;
    }

    return sock;
}

yuri_socket_t libyuri_tcp_accept(yuri_socket_t listen_sock) {
    if (!libyuri_socket_is_valid(listen_sock)) return YURI_INVALID_SOCKET;

    struct sockaddr_in client_addr;
    socklen_t addr_len = sizeof(client_addr);
    memset(&client_addr, 0, sizeof(client_addr));

    return accept(listen_sock, (struct sockaddr *)&client_addr, &addr_len);
}

void libyuri_tcp_close(yuri_socket_t sock) {
    libyuri_socket_close(sock);
}
