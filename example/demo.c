/**
 * Build this when testing `@sempai`, check KEYWORDS.md on how it works.
 * gcc -shared -o demo.dll demo.c
 */

#include <stdio.h>

__declspec(dllexport) int add(int a, int b) {
    return a + b;
}

__declspec(dllexport) int sub(int a, int b) {
    return a - b;
}
 
__declspec(dllexport) int mul(int a, int b) {
    return a * b;
}

__declspec(dllexport) double div(double a, double b) {
    if (b == 0.0) return 0.0;
    return a / b;
}

__declspec(dllexport) int clamp(int value, int min, int max) {
    if (value < min) return min;
    if (value > max) return max;
    return value;
}
