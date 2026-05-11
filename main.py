import gradio as gr
import uuid
from pathlib import Path
from PIL import Image
import numpy as np

import sphere_snap.utils as snap_utils
import sphere_snap.sphere_coor_projections as sphere_proj
from sphere_snap.snap_config import SnapConfig, ImageProjectionType
from sphere_snap.sphere_snap import SphereSnap
import sphere_snap.reprojections as rpr



import os 
import sys
import cv2
from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1 import ImageGrid
from scipy.spatial.transform import Rotation as R
pitch =0
yaw = 0
def show_img(img):
    plt.figure(figsize=(13, 13))
    plt.imshow(img)
    plt.show()

def show_imgs(imgs, size = 14, nb_cols=2, title_txt= None, fontsize=10, imgs_text = None):
    """
    Display a gird of images 
    :param imgs: the list of images to be displayed 
    :param size: display size of a cell
    :param nb_cols: number of columns
    """

    row_size = int(np.ceil(len(imgs)/nb_cols))
    fig = plt.figure(figsize=(size,size))
    axes_pad = 0.1 if imgs_text is None else 0.5

    if title_txt is not None:
        fig.suptitle(title_txt, fontsize=fontsize)
    grid = ImageGrid(fig, 111,  # similar to subplot(111)
                     nrows_ncols=(row_size, nb_cols),  # creates 2x2 grid of axes
                     axes_pad=axes_pad,  # pad between axes in inch.
                     )

    for idx, data in enumerate(zip(grid, imgs)):
        ax, img  = data
        if imgs_text is not None:
             ax.set_title(imgs_text[idx], fontdict={'fontsize': 15, 'fontweight': 'medium'}, loc='center', color = "k")
        ax.imshow(img)
    plt.show()
    
def rot(yaw, pitch):
    return R.from_euler("yxz",[yaw,-pitch,0], degrees=True).as_quat()

def blend_img(a, b, alpha=0.8):
    return (alpha*a + (1-alpha) * b).astype(np.uint8)
def predict (
        value
):
    
    global pitch,yaw
    # print(value)
    # so we want the layers part
    drawing = value["layers"][0]
    np.save("drawing.npy",drawing)
    # now need to get a rep of where the value isn't 0
    y,x,z = np.where(drawing>0)
    print(x)
    print()
    print(y)
    #minx = np.min(x)
    #maxx = np.max(x)
    #cenx = (maxx-minx)/2
    #miny = np.min(y)
    #maxy = np.max(y)
    #ceny =  (maxy-miny)/2
    # crop, and perhaps make it so that it's a constant 90,90 FOV 
    # calculate the pitch and yaw from this info 
    print(drawing.shape)
    # need to shift it by the center of the image
    ratiox = ((drawing.shape[1] - x.mean())-drawing.shape[1]/2)/drawing.shape[1]
    ratioy = ((drawing.shape[0] - y.mean())-drawing.shape[0]/2)/drawing.shape[0]
    anglex = 360*ratiox
    angley = 180*ratioy
    pitch = anglex
    yaw = angley
    # now try using the sphere snap perspective render based on the input
    equi_photo = value["background"]
    snap_config = SnapConfig(rot(anglex,angley) , (800,800),(90,90), equi_photo.shape[:2], source_img_type=ImageProjectionType.EQUI)
    snap_test = SphereSnap(snap_config)
    persp_img = snap_test.snap_to_perspective(equi_photo)
    return persp_img

def reconvert(value,jsondata):
    planar_img = value
    # NOTE THIS IS USING CONSTANT SPEC FOR DIMENSIONS
    equi_img = SphereSnap.merge_multiple_snaps((1000,2000),[
    SphereSnap(SnapConfig(rot(pitch,yaw) , (800,800),(90,90), (1000,2000), source_img_type=ImageProjectionType.EQUI))
    ],
    [planar_img],
   target_type=ImageProjectionType.EQUI,
   merge_method="max"

    )
    print("input image has ",planar_img.shape[2],"channels")
    print("equi out image has ",equi_img.shape[2]," channels")
    return equi_img


def download_im(im):
    name= f"{uuid.uuid4()}.png"
    Image.fromarray(im).save(name)
    print("saved image",name)
    return name

demo = gr.Blocks()

input_element_equi = gr.ImageEditor()
output_planar = gr.Image(buttons=None,sources=None)

input_element_planar = gr.Image(image_mode="RGBA")
json_data = gr.File()
output_equi = gr.Image()
download_name = ""
with demo:
    gr.Markdown("# Step1")
    gr.Markdown("upload an pick a section of a 360 image to project into perspective/planar mode")
    with gr.Row():
        with gr.Column():
            input_element_equi.render()
            btn = gr.Button("submit")
            btn.click(fn=predict,inputs=input_element_equi,outputs=[output_planar])
        with gr.Column():
            output_planar.render()
            btn = gr.Button("download")
            btn.click(download_im,inputs=output_planar,outputs = gr.File())


    gr.Markdown("# Step2")
    gr.Markdown("take the generated layer from photoshop and insert here, then submit to re-distor the planar generated data")
    with gr.Row():
        with gr.Column():
            input_element_planar.render()
            btn = gr.Button("submit")
            btn.click(fn=reconvert,inputs=[input_element_planar,json_data],outputs=output_equi)
        with gr.Column():
            output_equi.render()
            btn = gr.Button("download")
            btn.click(download_im,inputs=output_equi,outputs = gr.File())

demo.launch()

