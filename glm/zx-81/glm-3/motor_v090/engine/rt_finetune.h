#ifndef RT_FINETUNE_H
#define RT_FINETUNE_H

#include "rt_types.h"
#include "rt_model.h"

/* Only compiled when the port sets RT_ENABLE_FINETUNE=1 (host, Amiga).
 * On-device learning, mechanism 2: online int8 SGD on the output layer.
 * Hidden layers are frozen; the last hidden activations h[0..n) plus the
 * constant 127 bias lane drive the updates.
 */

/* Run `steps` SGD sweeps over `text` (plain ASCII, mapped to the charset).
 * lr_sh: learning rate as a right shift (update = (err*h) >> lr_sh);
 * 17..19 works well for our sizes. Returns the number of positions whose
 * argmax prediction was already correct on the last sweep (progress
 * indicator; higher = the model now knows the text). */
int rt_finetune_text(rt_model *m, const char *text, int steps, int lr_sh);

#endif /* RT_FINETUNE_H */
