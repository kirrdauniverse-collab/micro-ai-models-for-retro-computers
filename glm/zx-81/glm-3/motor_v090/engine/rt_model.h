#ifndef RT_MODEL_H
#define RT_MODEL_H

#include "rt_types.h"
#include "rt_config.h"

#define RT_MAGIC0 'R'
#define RT_MAGIC1 'T'
#define RT_MAGIC2 'L'
#define RT_MAGIC3 'M'
#define RT_VERSION 2

#define RT_FLAG_FINETUNE_OK 0x0001

/* On-disk layout of model.bin (all multi-byte values little-endian):
 *
 *   off  size  field
 *    0     4   magic "RTLM"
 *    4     2   u16 version      (RT_VERSION)
 *    6     2   u16 flags        (bit0: fine-tuning allowed)
 *    8     2   u16 vocab        (= 45)
 *   10     2   u16 ctx          context chars
 *   12     2   u16 emb          embedding width
 *   14     2   u16 h1           hidden 1 width
 *   16     2   u16 h2           hidden 2 width (0 = single hidden layer)
 *   18     2   u16 sh_e         reserved (= 7, embeddings are Q7)
 *   20     2   u16 sh1          reserved (0, per-row shifts are used)
 *   22     2   u16 sh2          reserved (0)
 *   24     2   u16 sh_o         reserved (0)
 *   26     2   u16 temp_sh      default sampling temperature shift
 *   28    64   char charset[64] (NUL-padded, must equal RT_CHARSET)
 *   92    ...   tensors:
 *        emb   [vocab][emb]                    int8  Q7 activations
 *        sh1   [h1]                            u8    row shifts
 *        w1    [h1][ctx*emb + 1]               int8  + bias lane (input 128)
 *        sh2   [h2]                            u8    (absent when h2 == 0)
 *        w2    [h2][h1 + 1]                    int8
 *        sho   [vocab]                         u8
 *        wo    [vocab][h_last + 1]             int8
 *   end     2   u16 additive checksum of all preceding bytes
 *
 * Quantization (v2): every activation lives in Q7 (real = v / 128), and
 * every weight ROW carries its own power-of-two shift s: the row is
 * stored as round(w * 2^s). A matmul row computes
 *     y = ( sum(x_i * q_i) + 128 * q_bias ) >> s
 * which returns Q7 activations (hidden layers, after ReLU+clip to [0,127])
 * or Q7-scaled logits (output layer). Because the bias lane input is 128
 * = 1.0 in Q7, biases quantize on exactly the same grid as weights.
 *
 * Expandability: dims live in the header, so a machine with more storage
 * can load a bigger file (up to the port's RT_MAX_* limits) with the same
 * engine - no recompile, no separate model format.
 */

typedef struct {
    rt_u16 version, flags;
    rt_u16 vocab, ctx, emb, h1, h2;
    rt_u16 sh_e, sh1, sh2, sh_o, temp_sh;
} rt_hdr;

typedef struct {
    rt_hdr      hdr;
    rt_i8      *emb;   /* [vocab][emb]              */
    rt_u8      *sh1;   /* [h1] row shifts           */
    rt_i8      *w1;    /* [h1][ctx*emb + 1]         */
    rt_u8      *sh2;   /* [h2] or NULL              */
    rt_i8      *w2;    /* [h2][h1 + 1] or NULL      */
    rt_u8      *sho;   /* [vocab] row shifts        */
    rt_i8      *wo;    /* [vocab][h_last + 1]       */
    const rt_u8 *raw;  /* borrowed: the loaded blob */
} rt_model;

/* Parse a loaded model blob. 0 = ok, negative = error:
 *  -1 too short, -2 bad magic, -3 bad version, -4 dims exceed port limits,
 *  -5 vocab mismatch, -6 charset mismatch, -7 checksum, -8 truncated.
 * len is the BUFFER capacity (how many bytes at buf may be read): the
 * blob's real length comes from its own header, so fixed-address loads
 * pass the port's RT_APP_MODEL_MAX and disk loads pass the file size. */
int  rt_model_load(rt_model *m, const rt_u8 *buf, long len);

/* Total blob size for a header (loader buffer sizing). */
long rt_model_size(const rt_hdr *h);

#endif /* RT_MODEL_H */
