import tkinter as tk
r = tk.Tk()
r.withdraw()
img = tk.PhotoImage(file="/mnt/d/Temp/tooie/launcher/banjotooie.png")
r.iconphoto(True, img)
print("iconphoto OK - PNG", img.width(), "x", img.height(), "set as window icon on Linux")
r.destroy()
