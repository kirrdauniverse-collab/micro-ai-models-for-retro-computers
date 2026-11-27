#ifndef RT_ROUTER_H
#define RT_ROUTER_H

/* Topic router: a base model chats about everything; when the input
 * smells like a specialist topic, the app loads that pack (disk first,
 * tape as fallback). When a word fits SEVERAL topics, the engine asks a
 * clarifying question first - "star" may mean astronomy or poetry.
 *
 * Keywords are matched as whole words against the sanitized input.
 * Ports may swap the table at startup via rt_router_set(). */

#define RT_TOPIC_MAX 8
#define RT_ROUTER_MAX_HITS 3

#ifndef RT_ROUTER_NO_SET
void rt_router_set(const char *const *names, const char *const *keys,
                   int n);
#endif

/* Scan text; fills hits (flat, 16-byte entries) with topic names,
 * returns the hit count
 * (0 = general chat, no topic pack needed). */
int rt_router_scan(const char *text, char *hits, int max_hits);

#endif /* RT_ROUTER_H */
