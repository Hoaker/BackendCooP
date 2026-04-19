from database import engine, Base
import models 

print("Connecting to PostgreSQL and creating tables...")
# This creates the tables in the cloud
Base.metadata.create_all(bind=engine)
print("Done! Your cloud database tables are created and ready.")
