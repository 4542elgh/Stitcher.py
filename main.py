import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfile
from PIL import Image, ImageTk
from datetime import datetime
import math
import os

class Stitcher():
    def __init__(self):
        # Some initial setup
        self.meta_list = self.find_images()
        self.max_width = self.find_max_width(list(map(lambda x:x.orig_img, self.meta_list)))

        # IDK what is going on, but thank god we have stackoverflow
        self.root = tk.Tk()
        self.container = ttk.Frame(self.root)
        self.canvas = tk.Canvas(self.container, width=self.max_width, height=1000)
        self.scrollbar = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        for (idx,meta) in enumerate(self.meta_list):
            # Calculate scale ratio, we need all images to be of same width, and height adjust automatically
            ratio = self.max_width/meta.orig_img.size[0]

            # Open image and convert to tk image object
            resized_img = meta.orig_img.resize((int(meta.orig_img.size[0]*ratio),int(meta.orig_img.size[1]*ratio)), Image.LANCZOS)

            img = ImageTk.PhotoImage(resized_img)
            label = ttk.Label(self.scrollable_frame, image=img)
            label.image = img
            label.pack()

            meta.label = label

            self.tkscale(meta, idx, "top", 1)
            self.tkscale(meta, idx, "bottom", 1)
            self.tkscale(meta, idx, "left", 2)
            self.tkscale(meta, idx, "right", 2)

            tk.Label(self.root, text='Image ' + str(idx+1) + ":").grid(row=(3*idx),column=2)
            tk.Label(self.root, text='Top').grid(row=(3*idx)+1,column=2, pady=(0,10))
            tk.Label(self.root, text='Bottom').grid(row=(3*idx)+1,column=4, pady=(0,10))
            tk.Label(self.root, text='Left').grid(row=(3*idx)+2,column=2, pady=(0,10))
            tk.Label(self.root, text='Right').grid(row=(3*idx)+2,column=4, pady=(0,10))

        save_btn = ttk.Button(self.root, text ="Save", command = lambda: self.save())
        save_btn.grid(row=(3*len(self.meta_list))+2,column=2, pady=(10,0))

        save_as_btn = ttk.Button(self.root, text ="Save As", command = lambda ask=True: self.save(ask))
        save_as_btn.grid(row=(3*len(self.meta_list))+3,column=2, pady=(10,0))

        self.container.grid(row=0,column=0, rowspan=999)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.root.mainloop()

    # Give me a list of images and their filename
    def find_images(self):
        meta_list = []
        for file_name in os.listdir():
            if file_name.split(".")[1].lower() == "png" or file_name.split(".")[1].lower() == "jpg":
                meta_list.append(ImageMeta(0, 0, 0, 0, Image.open(os.path.join(os.getcwd(), file_name)).convert('RGB'), file_name))
        return meta_list

    # Give me the max width so I can create a ratio for scaling up/down
    def find_max_width(self, image_list):
        widths, _ = zip(*(i.size for i in image_list))
        return max(widths)

    # Give me end result canvas total height
    def find_cropped_heights_sum(self):
        _, heights = zip(*(i.cropped.size for i in self.meta_list))
        return sum(heights)

    # Manipulate original image, with slider value, and save end result into cropped property
    def adjust(self, val, position, meta):
        img_size = meta.orig_img.size
        val = math.floor(float(val))

        # If cropping bottom
        if position == "bottom":
            # im.crop((left, top, right, bottom))
            cropped_img = meta.orig_img.crop(( meta.offset_left, meta.offset_top, img_size[0]-meta.offset_right, img_size[1]-val))
            meta.offset_bottom = val

        elif position == "top":
            cropped_img = meta.orig_img.crop(( meta.offset_left, val, img_size[0]-meta.offset_right, img_size[1]-meta.offset_bottom))
            meta.offset_top = val

        elif position == "left":
            cropped_img = meta.orig_img.crop(( val, meta.offset_top, img_size[0]-meta.offset_right, img_size[1]-meta.offset_bottom))
            meta.offset_left = val

        else:
            cropped_img = meta.orig_img.crop(( meta.offset_left, meta.offset_top, img_size[0]-val, img_size[1]-meta.offset_bottom))
            meta.offset_right = val

        if position == "left" or position == "right":
            self.max_width = self.find_max_width(list(map(lambda x:x.cropped, self.meta_list)))
            ratio = self.max_width/cropped_img.size[0]

            # Open image and convert to tk image object
            cropped_img = cropped_img.resize((int(cropped_img.size[0]*ratio),int(cropped_img.size[1]*ratio)), Image.LANCZOS)

        img = ImageTk.PhotoImage(cropped_img)
        meta.cropped = cropped_img
        meta.label.configure(image=img)
        meta.label.image = img
    
    # Saving based on ImageMeta's cropped image object
    def save(self, ask=False):
        total_height = self.find_cropped_heights_sum()

        # Create a large enough canvas
        new_im = Image.new('RGB', (self.max_width, total_height))

        filename = 'stitch_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.png'
        if ask: 
            f = asksaveasfile(initialfile = filename,
                              defaultextension=".png",
                              filetypes=[("All Files","*.*"),("JPEG","*.jpg"),("PNG","*.png")])
            filename = f.name
        y_offset = 0
        for im in self.meta_list:
            # center image if its smaller than max width, this shouldnt be necessay if you press the scale button
            center_x = int((self.max_width-im.cropped.size[0])/2)
            # Append images and record offset
            new_im.paste(im.cropped, (center_x,y_offset))
            y_offset += im.cropped.size[1]
        new_im.save(filename)
    
    def tkscale(self, meta, idx, pos, grid):
        col = (3 if pos == "bottom" or pos == "left" else 5)
        ttk.Scale(
            self.root,
            from_ = 1,
            to = meta.cropped.size[grid%2],
            orient = tk.HORIZONTAL,
            length = 200,
            command = lambda value, position=pos, offset=meta: self.adjust(value, position, offset)
        ).grid(row=(3*idx)+grid, column=col, padx=(0,30), pady=(0,10))

# Helper class to store each image offset and PIL image data
class ImageMeta:
    def __init__(self, offset_top, offset_bottom, offset_left, offset_right, img, filename):
        self.offset_top = offset_top
        self.offset_bottom = offset_bottom
        self.offset_left = offset_left
        self.offset_right = offset_right
        self.orig_img = img
        self.cropped = img
        self.label = None
        self.filename = filename
        
if __name__ == "__main__":
    Stitcher()
