#ifndef RT_MEMORY_H
#define RT_MEMORY_H

#include "rt_types.h"
#include "rt_config.h"

#define RT_MEM_KEY 24
#define RT_MEM_VAL 64
#define RT_MEM_MAGIC0 'R'
#define RT_MEM_MAGIC1 'T'
#define RT_MEM_MAGIC2 'M'
#define RT_MEM_MAGIC3 '1'

/* One taught fact: "/teach key = value". Stored in model-charset form
 * (lowercase, unknown chars -> space). */
typedef struct {
    char key[RT_MEM_KEY];
    char val[RT_MEM_VAL];
} rt_mem_rec;

typedef struct {
    rt_mem_rec rec[RT_MEM_MAX];
    int n;
} rt_memory;

void rt_mem_init(rt_memory *mem);

/* Teach a fact. 0 ok, -1 table full, -2 empty key. */
int  rt_mem_teach(rt_memory *mem, const char *key, const char *val);
void rt_mem_forget(rt_memory *mem, int idx);

/* Best fact whose key words (>= 3 chars) appear in the question.
 * Returns record index or -1. */
int  rt_mem_match(const rt_memory *mem, const char *question);

/* Build the spoken answer for a record: "your NAME is VALUE." when the
 * key starts with "my ", otherwise "my NAME is VALUE." */
void rt_mem_answer(const rt_mem_rec *r, char *out, int maxlen);

/* Serialize (magic "RTM1" + count + records) for memory.bin on disk or
 * an RT-turbo tape block. Returns bytes written or negative. */
long rt_mem_pack(const rt_memory *mem, rt_u8 *buf, long maxlen);
long rt_mem_unpack(rt_memory *mem, const rt_u8 *buf, long len);

#endif /* RT_MEMORY_H */
