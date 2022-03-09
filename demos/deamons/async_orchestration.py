import blumycelium.machine_elf as melf

class User(melf.MachineElf):

    def set_database(self, url, database_name, username, password):
        self.connection = ADB.Connection(
            arangoURL = url,
            username = username,
            password = password
        )

        self.db = self.connection[database_name]

    def task_send_article(self) -> {"title": str, "author": str}:
        from random import choice, randint

        title_maker = {
            "adjectives": ["Orange", "Yellow", "Green", "White", "Black", "Gigantic", "Famous", "Enlightened"],
            "nouns": ["Gorilla", "Giraf", "Hypo", "Gnu", "Parrot"],
            "verbs": ["ate", "talked", "laughted", "argued with"],
            "connector": ["about", "with", "over", "at", "to"],
            "complements": ["a Banana", "an Apple", "an Orange"]
        }

        title = [ choice(value) for key, value in title_maker ]
        title = " ".join(title)

        username = "User %d" % randint(0, 3)

        return {
            "title": title,
            "author": username
        }

    def task_view_article(self, article_key) -> None:
        import time
        doc = self.db["Articles"][article_key]
        
        view = self.db["Views"].createEdge()
        view.set{
            "_from": doc["_id,"],
            "_to": doc["userid"],
            "date": time.time(),
        }
        view.save()

def main():
    user = User("A User")
    user.
if __name__ == '__main__':
    main():
    pass