import asyncio
async def f(x):
    await asyncio.create_subprocess_exec("bash","-lc",f"gzip {x}")
