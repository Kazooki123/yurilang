#include "sockets.h"

#ifdef _WIN32
    #include <winsock2.h>
#else
    #include <fcntl.h>
    #include <unistd.h>
    #include <sys/socket.h>
#endif

yuri_socket_t libyuri_socket_create(void) {
    return socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
}

int libyuri_socket_set_nonblocking(yuri_socket_t sock) {
    if (!libyuri_socket_is_valid(sock)) return -1;

#ifdef _WIN32
    u_long mode = 1;
    return (ioctlsocket(sock, FIONBIO, &mode) == 0) ? 0 : -1;
#else
    int flags = fcntl(sock, F_GETFL, 0);
    if (flags < 0) return -1;
    return (fcntl(sock, F_SETFL, flags | O_NONBLOCK) == 0) ? 0 : -1;
#endif
}

int libyuri_socket_set_reuseaddr(yuri_socket_t sock) {
    if (!libyuri_socket_is_valid(sock)) return -1;

    int opt = 1;
    return setsockopt(sock, SOL_SOCKET, SO_REUSEADDR,
                      (const char *)&opt, sizeof(opt)) == 0 ? 0 : -1;
}

void libyuri_socket_close(yuri_socket_t sock) {
    if (!libyuri_socket_is_valid(sock)) return;
#ifdef _WIN32
    closesocket(sock);
#else
    close(sock);
#endif
}

int libyuri_socket_is_valid(yuri_socket_t sock) {
#ifdef _WIN32
    return sock != INVALID_SOCKET;
#else
    return sock >= 0;
#endif
}
