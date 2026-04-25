import gradio as gr
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
    
    # print(value)
    # so we want the layers part
    drawing = value["layers"][0]
    np.save("drawing.npy",drawing)
    # now need to get a rep of where the value isn't 0
    y,x,z = np.where(drawing>0)
    minx = np.min(x)
    maxx = np.max(x)
    cenx = (maxx-minx)/2
    miny = np.min(y)
    maxy = np.max(y)
    ceny =  (maxy-miny)/2
    # crop, and perhaps make it so that it's a constant 90,90 FOV 
    # calculate the pitch and yaw from this info 
    ratiox = cenx/drawing.shape[1]
    ratioy = ceny/drawing.shape[0]
    anglex = 360*ratiox
    angley = 360*ratioy
    # now try using the sphere snap perspective render based on the input
    equi_photo = value["background"]
    snap_config = SnapConfig(rot(anglex,angley) , (400,400),(90,90) equi_photo.shape[:2], source_img_type=ImageProjectionType.EQUI)
    snap_test = SphereSnap(snap_config)
    persp_img = snap_test.snap_to_perspective(equi_photo)
    return persp_img

interface = gr.Interface(predict,gr.ImageEditor(),gr.Image())
interface.launch()
