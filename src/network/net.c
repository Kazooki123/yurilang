#define LIBYURI_BUILD_DLL
#include "net.h"

#include <stdio.h>
#include <string.h>

/* -----------------------------------------------------------------------
 * Handle table
 * Python/ctypes can't store a SOCKET (64-bit on Win64) cleanly as a plain
 * int without risk of truncation. Uses a simple handle table that maps
 * int handles (1-based) to actual sockets. Keeps the public API clean ^~^
 * --------------------------------------------------------------------- */

#define LIBYURI_MAX_SOCKETS 256

static yuri_socket_t g_sockets[LIBYURI_MAX_SOCKETS];
static int g_initialized = 0;

static void handle_table_init(void) {
    for (int i = 0; i < LIBYURI_MAX_SOCKETS; i++)
        g_sockets[i] = YURI_INVALID_SOCKET;
}

/* Returns 1-based handle, or -1 if table is full. */
static int handle_alloc(yuri_socket_t sock) {
    for (int i = 0; i < LIBYURI_MAX_SOCKETS; i++) {
        if (g_sockets[i] == YURI_INVALID_SOCKET) {
            g_sockets[i] = sock;
            return i + 1; /* 1-based */
        }
    }
    return -1;
}

/* Returns the socket, or YURI_INVALID_SOCKET for bad handle. */
static yuri_socket_t handle_get(int handle) {
    if (handle < 1 || handle > LIBYURI_MAX_SOCKETS) return YURI_INVALID_SOCKET;
    return g_sockets[handle - 1];
}

static void handle_free(int handle) {
    if (handle < 1 || handle > LIBYURI_MAX_SOCKETS) return;
    g_sockets[handle - 1] = YURI_INVALID_SOCKET;
}

/*
 * Lifecycle
 */

LIBYURI_API int libyuri_net_init(void) {
    if (g_initialized) return 0;

#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return -1;
#endif

    handle_table_init();
    g_initialized = 1;
    return 0;
}

LIBYURI_API void libyuri_net_shutdown(void) {
    if (!g_initialized) return;

    /* Close any leaked sockets */
    for (int i = 0; i < LIBYURI_MAX_SOCKETS; i++) {
        if (g_sockets[i] != YURI_INVALID_SOCKET) {
            libyuri_socket_close(g_sockets[i]);
            g_sockets[i] = YURI_INVALID_SOCKET;
        }
    }

#ifdef _WIN32
    WSACleanup();
#endif

    g_initialized = 0;
}

LIBYURI_API const char *libyuri_net_version(void) {
    return "libyurinet 0.1.0";
}

/*
 * DNS wrappers
 */

LIBYURI_API int libyuri_net_resolve(const char *hostname, char *out_ip, int out_len) {
    return libyuri_dns_resolve(hostname, out_ip, (size_t)out_len);
}

LIBYURI_API int libyuri_net_reverse(const char *ip, char *out_host, int out_len) {
    return libyuri_dns_reverse(ip, out_host, (size_t)out_len);
}

/*
 * TCP wrappers — all return int handles, never raw sockets
 */

LIBYURI_API int libyuri_net_tcp_connect(const char *hostname, int port) {
    /* Resolve hostname first, then connect */
    char ip[46] = {0};
    if (libyuri_dns_resolve(hostname, ip, sizeof(ip)) != 0)
        return -1;

    yuri_socket_t sock = libyuri_tcp_connect(ip, port);
    if (!libyuri_socket_is_valid(sock)) return -1;

    int handle = handle_alloc(sock);
    if (handle < 0) {
        libyuri_socket_close(sock);
        return -1;
    }
    return handle;
}

LIBYURI_API int libyuri_net_tcp_send(int handle, const char *data, int len) {
    yuri_socket_t sock = handle_get(handle);
    return libyuri_tcp_send(sock, data, len);
}

LIBYURI_API int libyuri_net_tcp_recv(int handle, char *buf, int buf_len) {
    yuri_socket_t sock = handle_get(handle);
    return libyuri_tcp_recv(sock, buf, buf_len);
}

LIBYURI_API int libyuri_net_tcp_listen(int port, int backlog) {
    yuri_socket_t sock = libyuri_tcp_listen(port, backlog);
    if (!libyuri_socket_is_valid(sock)) return -1;

    int handle = handle_alloc(sock);
    if (handle < 0) {
        libyuri_socket_close(sock);
        return -1;
    }
    return handle;
}

LIBYURI_API int libyuri_net_tcp_accept(int listen_handle) {
    yuri_socket_t listen_sock = handle_get(listen_handle);
    yuri_socket_t client_sock = libyuri_tcp_accept(listen_sock);
    if (!libyuri_socket_is_valid(client_sock)) return -1;

    int handle = handle_alloc(client_sock);
    if (handle < 0) {
        libyuri_socket_close(client_sock);
        return -1;
    }
    return handle;
}

LIBYURI_API void libyuri_net_tcp_close(int handle) {
    yuri_socket_t sock = handle_get(handle);
    libyuri_tcp_close(sock);
    handle_free(handle);
}

/*
 * DllMain (Windows only) — minimal, just lets Windows load the DLL
 */
#ifdef _WIN32
#include <windows.h>
BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {
    (void)hinstDLL; (void)lpvReserved;
    return TRUE;
}
#endif
