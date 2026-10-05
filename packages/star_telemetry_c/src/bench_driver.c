/* bench_driver.c - throughput of star_aos_parse over a repeated F Prime frame stream (S.T.A.R. benchmark).
 * usage: bench_driver <stream.bin>  -> prints "<frames> <invalid> <seconds>" */
#define _POSIX_C_SOURCE 199309L /* clock_gettime / CLOCK_MONOTONIC under -std=c99 */
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "star_aos.h"

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: %s stream.bin\n", argv[0]); return 2; }
    FILE *f = fopen(argv[1], "rb");
    if (!f) { perror("open"); return 2; }
    static unsigned char buf[8000000];
    size_t n = fread(buf, 1, sizeof buf, f);
    fclose(f);
    const int len[5] = {256, 256, 256, 256, 254}, fecf[5] = {1, 1, 1, 1, 0};
    size_t off = 0;
    long k = 0, bad = 0;
    struct timespec a, z;
    clock_gettime(CLOCK_MONOTONIC, &a);
    while (off + (size_t)len[k % 5] <= n) {
        int i = (int)(k % 5);
        star_aos_header_t h;
        if (star_aos_parse(buf + off, (size_t)len[i], fecf[i], &h) || !h.fecf_valid) bad++;
        off += (size_t)len[i];
        k++;
    }
    clock_gettime(CLOCK_MONOTONIC, &z);
    double s = (double)(z.tv_sec - a.tv_sec) + (double)(z.tv_nsec - a.tv_nsec) / 1e9;
    printf("%ld %ld %.6f\n", k, bad, s);
    return 0;
}
