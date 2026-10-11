import os, random, sqlite3, json
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
load_dotenv()
app=FastAPI(title="NomerX")
BASE=Path(__file__).parent
DB=os.getenv("DATABASE_PATH","/tmp/nomerx.db")
Path(DB).parent.mkdir(parents=True,exist_ok=True)
def conn():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
with conn() as c:
 c.execute("CREATE TABLE IF NOT EXISTS players (id TEXT PRIMARY KEY, name TEXT, coins INTEGER NOT NULL DEFAULT 1000, garage TEXT NOT NULL DEFAULT '[]')")
CARS=[{"name":"NXR-01","rarity":"Обычная","price":250},{"name":"Vortex GT","rarity":"Редкая","price":900},{"name":"Phantom X","rarity":"Эпическая","price":2500},{"name":"NomerX One","rarity":"Легендарная","price":7000}]
@app.get("/api/health")
def health(): return {"ok":True,"app":"NomerX"}
@app.get("/",response_class=HTMLResponse)
def home():
 p=BASE/"static"/"index.html"
 if p.exists(): return p.read_text()
 return HTMLResponse("<h1>NomerX</h1><p>static/index.html missing</p>",status_code=500)
@app.get("/api/player")
def player(id:str="demo",name:str="Игрок"):
 with conn() as c:
  c.execute("INSERT OR IGNORE INTO players(id,name,coins,garage) VALUES(?,?,1000,'[]')",(id,name))
  r=c.execute("SELECT * FROM players WHERE id=?",(id,)).fetchone()
 return {"id":r["id"],"name":r["name"],"coins":r["coins"],"garage":json.loads(r["garage"])}
@app.post("/api/open")
async def open_box(req:Request):
 d=await req.json(); pid=str(d.get("id","demo")); name=str(d.get("name","Игрок"))
 with conn() as c:
  c.execute("INSERT OR IGNORE INTO players(id,name,coins,garage) VALUES(?,?,1000,'[]')",(pid,name))
  r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
  if r["coins"]<100: return JSONResponse({"error":"Недостаточно монет"},status_code=400)
  car=random.choices(CARS,weights=[60,25,12,3])[0]; garage=json.loads(r["garage"]); garage.append(car)
  c.execute("UPDATE players SET coins=coins-100,garage=? WHERE id=?",(json.dumps(garage,ensure_ascii=False),pid))
  return {"car":car,"player":{"id":pid,"name":r["name"],"coins":r["coins"]-100,"garage":garage}}
@app.post("/api/sell")
async def sell(req:Request):
 d=await req.json(); pid=str(d.get("id","demo")); idx=int(d.get("index",-1))
 with conn() as c:
  r=c.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
  if not r: return JSONResponse({"error":"Игрок не найден"},status_code=404)
  g=json.loads(r["garage"])
  if idx<0 or idx>=len(g): return JSONResponse({"error":"Машина не найдена"},status_code=400)
  car=g.pop(idx); gain=max(50,int(car["price"]*.6)); coins=r["coins"]+gain
  c.execute("UPDATE players SET coins=?,garage=? WHERE id=?",(coins,json.dumps(g,ensure_ascii=False),pid))
  return {"coins":coins,"garage":g,"gain":gain}
app.mount("/static",StaticFiles(directory=str(BASE/"static"),check_dir=False),name="static")
