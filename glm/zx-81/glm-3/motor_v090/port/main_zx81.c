/* main_zx81.c - ZX81 entry point: the single-block cassette image holds
 * the Class D model at 0x4082 (RT_MODEL_BUF_ADDR), so boot = disk-style
 * load that never touches the tape. */
#include "rt_app.h"

int main(void)
{
    if (rt_app_boot("base_d.bin") != 0)
        return 1;
    rt_app_run();
    return 0;
}
