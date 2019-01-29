from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, Quote
import datetime

engine = create_engine('sqlite:///postgresql.db')
                       #connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

session.add(Category(id="Dreams"))
session.commit()

session.add(Category(id="Love"))
session.commit()

session.add(Category(id="Nature"))
session.commit()

session.add(Category(id="Motivational"))
session.commit()

session.add(Category(id="Musical"))
session.commit()

session.add(Category(id="Artistic"))
session.commit()

session.add(Category(id="Poetic"))
session.commit()
