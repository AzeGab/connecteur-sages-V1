from fastapi.templating import Jinja2Templates
from app.utils.paths import templates_path

templates = Jinja2Templates(directory=templates_path) 