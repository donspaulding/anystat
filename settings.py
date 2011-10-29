HOST = '127.0.0.1'
PORT = 57475


class Config:
    def __getattr__(self, attr):
        return self[attr]

    def __setattr__(self, attr, val):
        self[attr] = val

    def __getitem__(self, item):
        return globals()[item]()

    def __setitem__(self, item, val):
        globals()[item] = lambda:val

config = Config()
