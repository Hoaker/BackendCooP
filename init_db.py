from database import engine, Base
import models 

print("Creating database tables...")
# This tells SQLAlchemy to look at 'Base' and create everything connected to it
Base.metadata.create_all(bind=engine)
print("Done! Your zimco.db file is ready.")