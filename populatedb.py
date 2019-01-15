from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_setup import Base, Category, Quote
import datetime

engine = create_engine('sqlite:///quotecamp.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

session.add(Category(id ="Dreams"))
session.commit()

session.add(Category(id = "Love"))
session.commit()

session.add(Category(id ="Nature"))
session.commit()

session.add(Category(id = "Motivational"))
session.commit()

session.add(Category(id = "Musical"))
session.commit()

session.add(Category(id = "Artistic"))
session.commit()

session.add(Category(id = "Poetic"))
session.commit()

session.add(Quote(
    id = 1,
    content = "The biggest adventure you can take is to live the life of your dreams.",
    author = "Oprah",
    poster_id= "1000",
    category_id = "Dreams",
    datetime_added = datetime.datetime.now(),
    ))
session.commit()
