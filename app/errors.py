class ContactNotFoundError(Exception):
    def __init__(self, id):
        super().__init__(f"No contact found by id {id}")
        self.id = id
