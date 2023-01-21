import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from datetime import datetime
import os

class Stitcher():
    def __init__(self):
        # Some initial setup
        self.image_list = self.find_images()
        self.max_width = self.find_max_width()

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

        # Keep track a list of ImageMeta objects
        self.meta_list = []

        for image in self.image_list:
            # Calculate scale ratio, we need all images to be of same width, and height adjust automatically
            ratio = self.max_width/image["img"].size[0]

            # Open image and convert to tk image object
            resized_img = image["img"].resize((int(image["img"].size[0]*ratio),int(image["img"].size[1]*ratio)), Image.LANCZOS)

            img = ImageTk.PhotoImage(resized_img)
            label = ttk.Label(self.scrollable_frame, image=img)
            label.image = img
            label.pack()

            meta_obj = ImageMeta(0, 0, resized_img)
            self.meta_list.append(meta_obj)

            # Callback need to be in lambda function
            sc1 = ttk.Scale(self.root,
                       from_ = 1,
                       to = image["img"].size[1],
                       orient = tk.HORIZONTAL,
                       command = lambda value, name=image["filename"], label_obj=label, position="top", offset=meta_obj: self.adjust(value, name, label_obj, position, offset))

            sc2 = ttk.Scale(self.root,
                       from_ = 1,
                       to = image["img"].size[1],
                       orient = tk.HORIZONTAL,
                       command = lambda value, name=image["filename"], label_obj=label, position="bottom", meta=meta_obj: self.adjust(value, name, label_obj, position, meta))

            sc1.pack()
            sc2.pack()

        save_btn = ttk.Button(self.root, text ="Save", command = lambda: self.save())

        save_btn.pack()
        self.container.pack()
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.root.mainloop()

    # Give me a list of images and their filename
    def find_images(self):
        image_list = []
        for file_name in os.listdir():
            if file_name.split(".")[1] != "py":
                image_list.append({"filename":file_name, "img":Image.open(os.path.join(os.getcwd(), file_name)).convert('RGB')})
        return image_list

    # Give me the max width so I can create a ratio for scaling up/down
    def find_max_width(self):
        widths, _ = zip(*(i["img"].size for i in self.image_list))
        return max(widths)

    # Give me end result canvas total height
    def find_cropped_heights_sum(self):
        _, heights = zip(*(i.cropped.size for i in self.meta_list))
        return sum(heights)

    # Manipulate original image, with slider value, and save end result into cropped property
    def adjust(self, val, img_name, label_obj, position, meta):
        img_size = meta.orig_img.size

        # If cropping bottom
        if position == "bottom":
            # im.crop((left, top, right, bottom))
            cropped_img = meta.orig_img.crop((0,meta.offset_top,img_size[0],int(img_size[1]-float(val))))
            meta.offset_bottom = float(val)
        else:
            cropped_img = meta.orig_img.crop((0,float(val),img_size[0],img_size[1]-meta.offset_bottom))
            meta.offset_top = float(val)

        # Set the label with new image
        img = ImageTk.PhotoImage(cropped_img)
        meta.cropped = cropped_img
        label_obj.configure(image=img)
        label_obj.image = img
    
    # Saving based on ImageMeta's cropped image object
    def save(self):
        total_height = self.find_cropped_heights_sum()
        # Create a large enough canvas
        new_im = Image.new('RGB', (self.max_width, total_height))

        y_offset = 0
        for im in self.meta_list:
            # Append images and record offset
            new_im.paste(im.cropped, (0,y_offset))
            y_offset += im.cropped.size[1]

        new_im.save('stitch_' + datetime.now().strftime("%Y%m%d%H%M%S") + '.jpg')

# Helper class to store each image offset and PIL image data
class ImageMeta:
    def __init__(self, offset_top, offset_bottom, img):
        self.offset_top = offset_top
        self.offset_bottom = offset_bottom
        self.orig_img = img
        self.cropped = img
        
if __name__ == "__main__":
    Stitcher()
