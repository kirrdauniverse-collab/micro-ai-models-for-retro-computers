#ifndef RT_ENGINE_H
#define RT_ENGINE_H

#include "rt_types.h"
#include "rt_model.h"

/* All scratch buffers are static inside the engine and sized by the
 * port's RT_MAX_* limits, so no heap is needed anywhere. */

/* Forward pass: ctx holds hdr.ctx charset indices, logits receives
 * hdr.vocab integer logits (higher = more likely). */
void rt_forward(const rt_model *m, const rt_u8 *ctx, rt_i32 *logits);

/* Peek at the last hidden layer computed by rt_forward (fine-tuning). */
void rt_last_hidden(const rt_i8 **h, int *n);

/* xorshift32 PRNG - bit-identical on every port (masked to 32 bits). */
rt_u32 rt_rand(rt_u32 *seed);

/* Sample one charset index from logits.
 * temp_sh: temperature as a right-shift on logit differences (0 = sharp,
 * larger = flatter). greedy: 1 = argmax. seed: PRNG state. */
int rt_sample(const rt_model *m, const rt_i32 *logits, int temp_sh,
              int greedy, rt_u32 *seed);

#endif /* RT_ENGINE_H */
