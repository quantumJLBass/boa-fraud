from db.dbefclasses import Session, Person

class GenericModel:
    def __init__(self):
        self.session = Session()

    def add_person(self, person_data):
        person = Person(**person_data)
        self.session.add(person)
        self.session.commit()

    def get_person(self, person_id):
        return self.session.query(Person).get(person_id)

    def update_person(self, person_id, update_data):
        for key, value in update_data.items():
            setattr(person, key, value)
        self.session.commit()

    def delete_person(self, person_id):
        person = self.session.query(Person).get(person_id)
        self.session.delete(person)
        self.session.commit()