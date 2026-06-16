#ifndef LIBYURI_NET_H
#define LIBYURI_NET_H

/*
 * libyurinet.dll — Networking support for Yurilang
 *
 * This is the single public header the Python runtime or Yurilang
 * interpreter needs to be included. Everything is exported from one DLL.
 *
 * Usage from Python (ctypes):
 *   net = ctypes.WinDLL("libyurinet.dll")
 *   net.libyuri_net_init()
 *   ...
 *   net.libyuri_net_shutdown()
 */

#ifdef _WIN32
    #ifdef LIBYURI_BUILD_DLL
        #define LIBYURI_API __declspec(dllexport)
    #else
        #define LIBYURI_API __declspec(dllimport)
    #endif
#else
    #define LIBYURI_API __attribute__((visibility("default")))
#endif

#include "dns.h"
#include "sockets.h"
#include "tcp.h"

#ifdef __cplusplus
extern "C" {
#endif

/* --- Lifecycle --- */

/* Initialize Winsock (must call before anything else).
 * Returns 0 on success, -1 on failure. */
LIBYURI_API int libyuri_net_init(void);

/* Shutdown Winsock (call at program exit). */
LIBYURI_API void libyuri_net_shutdown(void);

/* Returns a human-readable version string for libyurinet. */
LIBYURI_API const char *libyuri_net_version(void);

/* --- Re-exported DNS --- */
LIBYURI_API int libyuri_net_resolve(const char *hostname, char *out_ip, int out_len);
LIBYURI_API int libyuri_net_reverse(const char *ip, char *out_host, int out_len);

/* --- Re-exported TCP --- */
LIBYURI_API int  libyuri_net_tcp_connect(const char *hostname, int port);
LIBYURI_API int  libyuri_net_tcp_send(int handle, const char *data, int len);
LIBYURI_API int  libyuri_net_tcp_recv(int handle, char *buf, int buf_len);
LIBYURI_API int  libyuri_net_tcp_listen(int port, int backlog);
LIBYURI_API int  libyuri_net_tcp_accept(int listen_handle);
LIBYURI_API void libyuri_net_tcp_close(int handle);

#ifdef __cplusplus
}
#endif

#endif /* LIBYURI_NET_H */
