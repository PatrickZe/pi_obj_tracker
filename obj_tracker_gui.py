###Main GUI application
import tkinter as tk
import tkinter.ttk as ttk
import logging
from collections import deque

import sys



class GuiApp(tk.Tk):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        ######################################
        #Variables
        ######################################
        self.rotation_manual_angle = tk.IntVar(value=0)
        self.tilt_manual_angle = tk.IntVar(value=0)

        self.controll_mode = "Automatic"
        self.controll_algo = "No"


        ######################################
        #GUI APP
        ######################################

        self.title("Object Tracker")
        #self.geometry("1000x600")
        self.resizable(width=False, height=False)

        ######################################
        #Configure rows/columns
        ######################################
        self.grid_columnconfigure(0, minsize=170)
        self.grid_columnconfigure(1, minsize=650)

        self.grid_rowconfigure(0, minsize=350)

        ######################################
        #Button Field
        #Column 0
        #Row 0
        ######################################
        #Frame
        self.button_field_frame = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        self.button_field_frame.grid(column=0, row=0, sticky="nsew")

        #Status label
        tk_button_mode_label = tk.Label(self.button_field_frame, text="Mode:")
        tk_button_mode_label.grid(column=0, row=0, sticky="w")
        self.tk_button_mode_clabel = tk.Label(self.button_field_frame, text= "Manual")
        self.tk_button_mode_clabel.grid(column=1, row=0, sticky="we")

        tk_button_algo_label = tk.Label(self.button_field_frame, text="Algorithm:")
        tk_button_algo_label.grid(column=0, row=1, sticky="w")
        self.tk_button_algo_clabel = tk.Label(self.button_field_frame, text="None")
        self.tk_button_algo_clabel.grid(column=1, row=1, sticky="we")

        #Switch controll mode
        tk_button_mode = ttk.Button(self.button_field_frame, text="Manual/Automatic", command=self.change_manual_auto)
        tk_button_mode.grid(column=0, row = 2, columnspan=2, sticky="we")


        #Button raw image
        tk_button_raw_img = ttk.Button(self.button_field_frame, text="Raw Image, no tracking", command=self.set_raw_image)
        tk_button_raw_img.grid(column=0, row = 3, columnspan=2, sticky="we")

        #OpenCV color
        tk_button_opencv_color = ttk.Button(self.button_field_frame, text="OpenCV color tracking", command=self.set_opencv_color)
        tk_button_opencv_color.grid(column=0, row = 4, columnspan=2, sticky="we")

        #OpenCV face
        tk_button_opencv_face = ttk.Button(self.button_field_frame, text="OpenCV face tracking", command=self.set_opencv_face)
        tk_button_opencv_face.grid(column=0, row = 5, columnspan=2, sticky="we")

        #Tensorflow Person
        tk_button_tensorflow_person = ttk.Button(self.button_field_frame, text="Tensorflow person tracking", command=self.placeholder)
        tk_button_tensorflow_person.grid(column=0, row = 6, columnspan=2, sticky="we")

        ######################################
        #Image-Field
        #Column 1
        #Row 0
        ######################################
        #Frame
        self.image_frame = tk.Frame(self, bg="green", highlightbackground="black", highlightthickness=1)
        self.image_frame.grid(column=1, row=0, sticky="nsew")
        tk_image_frame_label = tk.Label(self.image_frame, text="Image_Placeholder", background="green")
        tk_image_frame_label.grid(column=0, row=0)

        ######################################
        #Slider Field
        #Column 1
        #Row 1
        ######################################
        self.slider_frame = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        self.slider_frame.grid(column=1, row=1, sticky="nsew")
        self.slider_frame.grid_columnconfigure(1, weight = 1)

        tk_rotation_label = tk.Label(self.slider_frame, text="Rotation in °:")
        tk_rotation_label.grid(column=0, row=0)

        tk_rotation_slider = ttk.Scale(self.slider_frame, from_=-90, to=90, orient="horizontal", variable=self.rotation_manual_angle)
        tk_rotation_slider.grid(column=1, row=0, sticky="ew")

        
        tk_tilt_label = tk.Label(self.slider_frame, text="Tilt in °:")
        tk_tilt_label.grid(column=0, row=1)

        tk_tilt_slider = ttk.Scale(self.slider_frame, from_=-60, to=60, orient="horizontal", variable=self.tilt_manual_angle)
        tk_tilt_slider.grid(column=1, row=1, sticky="ew")
        


    
    def placeholder(self)->None:    
        pass


    def change_manual_auto(self)->None:
        if self.controll_mode == "Manual":
            self.tk_button_mode_clabel.configure(text="Automatic")
            self.controll_mode = "Automatic"
            return
        else: 
            self.tk_button_mode_clabel.configure(text="Manual")
            self.controll_mode = "Manual"

    def set_raw_image(self)->None:
        self.tk_button_algo_clabel.configure(text="Raw Image")
        self.controll_algo = "Raw Image"

    def set_opencv_color(self)->None:
        #Maybe with color
        self.tk_button_algo_clabel.configure(text="OpenCV color")
        self.controll_algo = "OpenCV color"

    def set_opencv_face(self)->None:
        self.tk_button_algo_clabel.configure(text="OpenCV face")
        self.controll_algo = "OpenCV face"
