#ifndef RT_CLOCK_H
#define RT_CLOCK_H

/* Wall clock for machines without an RTC: the app asks for the date and
 * time at boot (exactly what we did in the 80s), validates it, and
 * derives the weekday, part of day and season with pure integer math -
 * no libc time functions, so it works on every retro compiler. */

typedef struct {
    int y, mo, d;  /* date */
    int h, mi;     /* time  */
    int wd;        /* weekday 0=Sunday .. 6=Saturday */
    int valid;     /* 1 once set by the user */
} rt_clock;

void rt_clock_init(rt_clock *c);
/* Validate and set. 0 ok, -1 bad date, -2 bad time. */
int  rt_clock_set(rt_clock *c, int y, int mo, int d, int h, int mi);
int  rt_clock_leap(int y);
/* Day of month cap for a month. */
int  rt_clock_days_in(int y, int mo);
/* Zeller-derived weekday. */
int  rt_clock_weekday(int y, int mo, int d);
const char *rt_clock_dayname(int wd);      /* "monday" ... */
const char *rt_clock_part_of_day(int h);   /* night/morning/... */
const char *rt_clock_season(int mo);       /* northern hemisphere */
/* Whole days from a to b (b - a); negative if b is earlier. */
long rt_clock_days_diff(const rt_clock *a, const rt_clock *b);

#endif /* RT_CLOCK_H */
