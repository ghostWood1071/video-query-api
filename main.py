from fastapi import FastAPI
from pyhive import hive
from fastapi import Depends
from typing import *
from starlette.middleware.cors import CORSMiddleware
from fastapi import Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

app = FastAPI()
db_host = '192.168.100.126'
account = 'hduser'
db_port = 10000

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],  # can alter with time
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

def execute(command:str):
    conn = hive.Connection(host=db_host, username=account, port=db_port)
    cursor = conn.cursor()
    cursor.execute(command)
    return cursor.fetchall()

def read_html(path): 
    with open(path, mode='r') as f:
       content = f.read() 
       return content

class ConditionBuilder():
    def __init__(self, names:List[str], times:List[float]): 
        self.names = names
        self.times = times
    def build_names(self):
        name_str_lst = str(tuple(self.names))
        if len(self.names) == 1:
            name_str_lst = name_str_lst.replace(',','')
        return f''' exists (
        select name
        from trackings as t
        where t.segment_id = s.rowkey 
        and s.video_id = t.video_id 
        and t.name in {name_str_lst})'''
        
    def build_times(self):
        q_time_min = self.times[0]
        q_time_max = self.times[1]
        if q_time_max < q_time_min:
            if q_time_max >0:
                raise Exception("wrong time range")
        if q_time_min == 0:
            return f"({q_time_max}>=s.time_end and s.time_start<{q_time_max})"
        if q_time_max == 0:
            return f"(s.time_start>={q_time_min})"
        return f"({q_time_max}>=s.time_end and s.time_start<{q_time_max})\nand ({q_time_min}<s.time_end and s.time_start<={q_time_min})"
    def get_condtion(self):
        if self.times[0] == 0 and self.times[1] == 0:
            if not self.names:
                return ""
            else:
                return f"where {self.build_names()}"
        else:
            if not self.names:
                return f"where {self.build_times()}"
            else:
                return f"where {self.build_names()} and {self.build_times()}"

class QueryModel(BaseModel):
    names: List[str] = Field(default=[])
    time_ranges:List[float] = Field(default=[0,0])
    

def get_query(names, time_ranges):
    builder = ConditionBuilder(names, time_ranges)
    query = f'''
        select s.rowkey as segment_id,
        s.video_id,
        v.location,
        s.url,
        s.time_start,
        s.time_end,
        f.content as cover
        from segments as s
        join  frames as f
        on s.cover = f.rowkey
        join videos as v
        on v.rowkey = s.video_id
        {builder.get_condtion()} order by s.time_start
    '''
    return query


def handle_result(cols:str = "", db_result:List[Any]=None):
    if not cols:
        return db_result
    def match_schema(x:Tuple[Any]):
        schema = cols.split(',')
        if len(x) != len(schema):
            raise Exception("schema not match with value")
        return dict(zip(schema, x))
    result:List[Any] = list(map(match_schema, db_result))
    return result;


@app.get("/", response_class=HTMLResponse)
def index():
    return read_html("./html/index.html")

@app.post('/segments/')
def get_segments(params:QueryModel):
    try:
        query = get_query(params.names, params.time_ranges)
        print(query)
        query = query.replace('\n', ' ').replace('\t',' ').replace('         ',' ')
        print(query)
        db_result = execute(query)
        cols = 'segment_id,video_id,location,url,time_start,time_end,cover'
        result = handle_result(cols, db_result)
        return result
    except Exception as e:
        return Response(str(e), 500)


    
    


