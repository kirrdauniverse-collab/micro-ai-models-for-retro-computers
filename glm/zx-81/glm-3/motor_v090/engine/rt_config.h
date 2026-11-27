/* rt_config.h - compile-time limits, tuned per port.
 *
 * A port overrides these with -D flags (see the port Makefiles) so the
 * static scratch buffers shrink to fit the target's RAM budget. Example
 * for the ZX81 (Class D only): -DRT_MAX_CTX=8 -DRT_MAX_EMB=16 -DRT_MAX_HID=48
 */
#ifndef RT_CONFIG_H
#define RT_CONFIG_H

/* Charset size cap (our shared charset has exactly 45 chars). */
#ifndef RT_MAX_VOCAB
#define RT_MAX_VOCAB      64
#endif

/* Context window in characters. */
#ifndef RT_MAX_CTX
#define RT_MAX_CTX        16
#endif

/* Embedding width. */
#ifndef RT_MAX_EMB
#define RT_MAX_EMB        64
#endif

/* Hidden layer width (h1 and h2 share this cap). */
#ifndef RT_MAX_HID
#define RT_MAX_HID        512
#endif

/* On-device fine-tuning of the output layer. Enable on host / Amiga. */
#ifndef RT_ENABLE_FINETUNE
#define RT_ENABLE_FINETUNE 0
#endif

/* Teachable key=value facts kept in RAM. */
#ifndef RT_MEM_MAX
#define RT_MEM_MAX        16
#endif

/* Model blob buffer size for rt_app (bytes). Host default fits Class A
 * (~350 KB); small machines override, e.g. C64: -DRT_APP_MODEL_MAX=40960
 * ZX81: -DRT_APP_MODEL_MAX=10240. */
#ifndef RT_APP_MODEL_MAX
#define RT_APP_MODEL_MAX  (512 * 1024)
#endif

/* Longest user input line. */
#ifndef RT_LINE_MAX
#define RT_LINE_MAX       96
#endif

/* Journal (dated episodic memory) entries. Small machines override,
 * e.g. ZX81: -DRT_JOURNAL_MAX=8. */
#ifndef RT_JOURNAL_MAX
#define RT_JOURNAL_MAX    24
#endif

#endif /* RT_CONFIG_H */
