/* host_main.c - reads a frame stream and prints one JSON line per frame.
 * usage: star_aos_dump <file> <len>:<fecf 0|1> [<len>:<fecf> ...]  (frames in order) */
#include <stdio.h>
#include <stdlib.h>
#include "star_aos.h"

int main(int argc, char **argv) {
    if (argc < 3) { fprintf(stderr, "usage: %s file len:fecf ...\n", argv[0]); return 2; }
    FILE *fp = fopen(argv[1], "rb");
    if (!fp) { perror("open"); return 2; }
    static uint8_t buf[1u << 20];
    size_t n = fread(buf, 1, sizeof buf, fp);
    int more = fgetc(fp) != EOF; /* a stream larger than the buffer is an error, never a silent truncation */
    fclose(fp);
    if (more) { fprintf(stderr, "stream larger than %lu bytes\n", (unsigned long)sizeof buf); return 2; }
    size_t off = 0;
    for (int i = 2; i < argc; i++) {
        unsigned len = 0; int fecf = 0;
        if (sscanf(argv[i], "%u:%d", &len, &fecf) != 2 || off + len > n) { fprintf(stderr, "bad spec %s\n", argv[i]); return 2; }
        star_aos_header_t h;
        int rc = star_aos_parse(buf + off, len, fecf, &h);
        if (rc) { printf("{\"index\":%d,\"error\":%d}\n", i - 2, rc); off += len; continue; }
        printf("{\"index\":%d,\"tfvn\":%u,\"scid\":%u,\"vcid\":%u,\"vcfc\":%lu,\"replay\":%u,\"fhp\":%u,"
               "\"fecf_valid\":%u,\"fecf_received\":%u,\"fecf_computed\":%u,\"data_len\":%lu,"
               "\"data_offset\":%lu,\"ocf_len\":%lu}\n",
               i - 2, h.tfvn, h.scid, h.vcid, (unsigned long)h.vcfc, h.replay, h.fhp, h.fecf_valid,
               h.fecf_received, h.fecf_computed, (unsigned long)h.data_len,
               (unsigned long)h.data_offset, (unsigned long)h.ocf_len);
        off += len;
    }
    return 0;
}
