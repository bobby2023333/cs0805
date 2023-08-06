
import pandas as pd

def import_data(db, User):
    df = pd.read_excel('users.xlsx')

    for index, row in df.iterrows():
        user = User.query.filter_by(phone=row['phone']).first()
        if user is None:
            user = User(
                username=row['username'],
                password=row['password'],
                phone=row['phone'],
                organization=row['organization']
            )
            db.session.add(user)
        else:
            pass  # Add your logic for existing users here
    db.session.commit()
