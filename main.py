from fastapi import FastAPI
from routers import root, line_break, export_ppt, export_docx, export_xlsx

app = FastAPI()

app.include_router(root.router)
app.include_router(line_break.router)
app.include_router(export_ppt.router)
app.include_router(export_docx.router)
app.include_router(export_xlsx.router)
