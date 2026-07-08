/* Yuri's print runtime.
 *
 * Deliberately NOT variadic. Calling C's variadic printf/sprintf directly
 * from hand-written Cranelift IR means dealing with platform-specific
 * variadic calling-convention quirks (e.g. the %al vector-register-count
 * requirement on the SysV x86-64 ABI). Instead, this file, compiled by
 * a real C compiler does the variadic printf calls internally, and
 * exposes plain fixed-arity functions for the compiled Yuri code to call.
 * That sidesteps the whole issue, on every platform, for free.
 */

#include <stdio.h>

void yuri_print_str(const char *s) {
    fputs(s, stdout);
}

void yuri_print_int(long long v) {
    printf("%lld", v);
}

void yuri_print_float(double v) {
    printf("%g", v);
}

void yuri_print_space(void) {
    fputs(" ", stdout);
}

void yuri_print_newline(void) {
    fputs("\n", stdout);
}
