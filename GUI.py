import tkinter as tk
import threading
import client

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Chat Room Application")
        self.geometry("400x250")

        container = tk.Frame(self)
        container.pack(fill="both", expand=True)

        # Ensure frames resize correctly
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for Page in (HomePage, JoinRoomPage, CreateRoomPage, OptionsPage):
            page_name = Page.__name__
            frame = Page(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomePage")

    def show_frame(self, page_name: str):
        frame = self.frames[page_name]
        frame.tkraise()

class HomePage(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        tk.Label(self, text="Home", font=("Arial", 18)).pack(pady=10)
        tk.Button(self, text="Join / Create Room",
                  command=lambda: controller.show_frame("OptionsPage")).pack()

class OptionsPage(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        tk.Label(self, text="Options", font=("Arial", 18)).pack(pady=10)
        tk.Button(self, text="Create Room",
                  command=lambda: controller.show_frame("CreateRoomPage")).pack()
        tk.Button(self, text="Join Room",
                  command=lambda: controller.show_frame("JoinRoomPage")).pack()
        tk.Button(self, text="Back to Home",
                  command=lambda: controller.show_frame("HomePage")).pack()

class CreateRoomPage(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        tk.Button(self, text="Back to Options",
                  command=lambda: controller.show_frame("OptionsPage")).pack()

class JoinRoomPage(tk.Frame):
    def __init__(self, parent, controller: App):
        super().__init__(parent)
        tk.Button(self, text="Back to Options",
                  command=lambda: controller.show_frame("OptionsPage")).pack()
    
    def display_rooms(self):
        for widget in self.winfo_children():
            if isinstance(widget, tk.Button) and widget.cget("text") not in ["Back to Options"]:
                widget.destroy()

        # logic has not been implemented yet to fetch rooms from server
        

if __name__ == "__main__":
    App().mainloop()
