import asyncio
import random
from typing import AsyncGenerator

TOTAL_PAGES = 17   # 假设 PDF 有 17 页

async def fake_stage(name: str, pages: int = TOTAL_PAGES) -> AsyncGenerator[int, None]:
    """模拟阶段

    模拟某一个阶段处理耗时任务，针对不同stage进行不同的处理逻辑

    参数：
        name: 处理阶段
    
    返回：
        返回生成器，返回完成的当前页码
    """
    for done in range(1, pages + 1):  # 遍历当前pdf解析任务的pdf所有pages
        await asyncio.sleep(random.uniform(0.1, 0.3))  # 实际情况需要替换为真实的处理单页的pdf解析数据处理管道【单个pdf解析函数内包括多个stages】这是一个耗时任务
        yield done



