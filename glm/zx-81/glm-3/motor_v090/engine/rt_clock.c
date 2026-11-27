/* rt_clock.c - date/time handling without libc (see rt_clock.h). */
#include "rt_clock.h"

static const int MDAYS[12] = { 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 };
static const char *DAYNAME[7] = { "sunday", "monday", "tuesday", "wednesday",
                                  "thursday", "friday", "saturday" };
static const char *SEASON[12] = { "winter", "winter", "spring", "spring",
                                  "spring", "summer", "summer", "summer",
                                  "autumn", "autumn", "autumn", "winter" };

void rt_clock_init(rt_clock *c)
{
    c->y = 2026; c->mo = 1; c->d = 1;
    c->h = 12; c->mi = 0;
    c->wd = rt_clock_weekday(2026, 1, 1);
    c->valid = 0;
}

int rt_clock_leap(int y)
{
    return (y % 4 == 0 && y % 100 != 0) || y % 400 == 0;
}

int rt_clock_days_in(int y, int mo)
{
    if (mo < 1 || mo > 12)
        return 0;
    if (mo == 2 && rt_clock_leap(y))
        return 29;
    return MDAYS[mo - 1];
}

int rt_clock_weekday(int y, int mo, int d)
{
    /* Sakamoto's algorithm: 0=Sunday */
    static const int t[12] = { 0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4 };
    int w;
    if (mo < 3)
        y -= 1;
    w = (y + y / 4 - y / 100 + y / 400 + t[mo - 1] + d) % 7;
    if (w < 0)
        w += 7;
    return w;
}

int rt_clock_set(rt_clock *c, int y, int mo, int d, int h, int mi)
{
    if (y < 1970 || y > 2099 || mo < 1 || mo > 12)
        return -1;
    if (d < 1 || d > rt_clock_days_in(y, mo))
        return -1;
    if (h < 0 || h > 23 || mi < 0 || mi > 59)
        return -2;
    c->y = y; c->mo = mo; c->d = d;
    c->h = h; c->mi = mi;
    c->wd = rt_clock_weekday(y, mo, d);
    c->valid = 1;
    return 0;
}

const char *rt_clock_dayname(int wd)
{
    if (wd < 0 || wd > 6)
        return "?";
    return DAYNAME[wd];
}

const char *rt_clock_part_of_day(int h)
{
    if (h < 5)
        return "night";
    if (h < 12)
        return "morning";
    if (h < 17)
        return "afternoon";
    if (h < 21)
        return "evening";
    return "night";
}

const char *rt_clock_season(int mo)
{
    if (mo < 1 || mo > 12)
        return "?";
    return SEASON[mo - 1];
}

/* days since 1970-03-01 style count (civil-from-days inverse, integer) */
static long to_serial(int y, int mo, int d)
{
    long yy = (long)y, mm = (long)mo, era, yoe, doy, doe, days;
    if (mo <= 2) {
        yy -= 1;
        mm += 12;
    }
    era = (yy >= 0 ? yy : yy - 399) / 400;
    yoe = yy - era * 400;
    doy = (153 * (mm - 3) + 2) / 5 + d - 1;
    doe = yoe * 365 + yoe / 4 - yoe / 100 + doy;
    days = era * 146097 + doe - 719468; /* days since 1970-01-01 */
    return days;
}

long rt_clock_days_diff(const rt_clock *a, const rt_clock *b)
{
    return to_serial(b->y, b->mo, b->d) - to_serial(a->y, a->mo, a->d);
}
