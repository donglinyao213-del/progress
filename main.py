from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import asyncio
from processor import fake_stage, TOTAL_PAGES
import time

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存存储[任务进度]（重启即丢）-> 可换成redis缓存
progress_map: dict[str, dict] = {}  # 任务id执行到阶段的多少百分比了

@app.get("/")
async def index():
    with open("static/index.html", encoding="utf8") as f:
        return HTMLResponse(f.read())

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    uid = uuid.uuid4().hex  # 生成任务id
    progress_map[uid] = {"page":1,"stage": "idle", "percent": 0,"current_speed":1,"predict_completed_time":3}  # 空闲 百分比为0
    # 后台启动管道
    asyncio.create_task(pipeline(uid))
    return {"uid": uid}

async def pipeline(uid: str):
    """pdf-parser模拟函数
    
    pdf-parser处理一个pdf包括多个阶段stages，假设当前仅仅包括四个阶段
    
    参数:
        uid: 处理pdf对应的id
        
    返回: 
        None
    """
    stages = ["MFD", "MFR", "TableRec", "OCR"]
    for idx, stage in enumerate(stages, 1): 
        progress_map[uid]["stage"] = stage
        start_time = 0
        cur_speed = 0
        pred_total_time = 0
        start_time = time.time()
        time_stack = []
        async for done in fake_stage(stage):
            percent = int(done / TOTAL_PAGES * 100)
            progress_map[uid]["page"] = done
            time_stack.append(time.time())  # pages个time
            if done >= 2:
                cur_speed = round((time_stack[:done])/len(time_stack[:done]),2)
                pred_total_time = cur_speed*TOTAL_PAGES
            
            # 每 1 % 推送一次
            if percent % 1 == 0:
                progress_map[uid]["percent"] = percent
                progress_map[uid]["current_speed"] = cur_speed
                progress_map[uid]["predict_completed_time"] = pred_total_time
                await asyncio.sleep(0)  # 让 SSE 读最新值
        # 阶段完成
        progress_map[uid]["percent"] = 100
        # 延迟0.2秒确保前端能平滑显示完成动画，可能需要根据实际场景调整
        await asyncio.sleep(0.2)
    progress_map[uid]["stage"] = "done"

@app.get("/progress/{uid}")
async def sse_progress(uid: str):
    from fastapi.responses import StreamingResponse
    import json

    async def event_generator():
        while True:
            prog = progress_map.get(uid, {"page":1, "stage": "unknown", "percent": 0,"current_speed":1,"predict_completed_time":3})
            yield f"data: {json.dumps(prog)}\n\n"
            if prog.get("stage") == "done":
                yield f"event: close\ndata: \n\n"
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )