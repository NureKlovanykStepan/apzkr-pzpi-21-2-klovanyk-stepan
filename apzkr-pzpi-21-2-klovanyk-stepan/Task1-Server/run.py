from app.application import create_app
from app.database.models import User

app = create_app()
app.run(port=8888, debug=True, host='0.0.0.0')