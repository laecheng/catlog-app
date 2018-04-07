from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Catlog, Base, CatlogItem, User

engine = create_engine('sqlite:///catlog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

catlog1 = Catlog(name="Soccer")
session.add(catlog1)
session.commit()

catlog2 = Catlog(name="Basketball")
session.add(catlog2)
session.commit()

catlog3 = Catlog(name="Baseball")
session.add(catlog3)
session.commit()

catlog4 = Catlog(name="Frisbee")
session.add(catlog4)
session.commit()

catlog5 = Catlog(name="Snowboarding")
session.add(catlog5)
session.commit()

catlog6 = Catlog(name="Rock Climbing")
session.add(catlog6)
session.commit()

catlog7 = Catlog(name="Foosball")
session.add(catlog7)
session.commit()

catlog8 = Catlog(name="Skating")
session.add(catlog8)
session.commit()

catlog9 = Catlog(name="Hockey")
session.add(catlog9)
session.commit()
