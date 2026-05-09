from database import init_db
from gui import NoticeApp

if __name__ == "__main__":
    init_db()
    app = NoticeApp()
    app.mainloop()
