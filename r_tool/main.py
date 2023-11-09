from PIL import Image
import math
from pdf2image import convert_from_path
import os
import shutil
from pathlib import Path
from zipfile import ZipFile
import base64
from io import BytesIO



## 配置信息
beishu = 2
size = 113 * beishu
output_dir = "upload"


def png_transparency(sign_path,transparency):
    # sign = Image.open(sign_path)
    sign = sign_path
    sign = sign.convert('RGBA')
    x, y = sign.size
    for i in range(x):
        for k in range(y):
            color = sign.getpixel((i, k))
            color = color[:-1] + (int(color[-1]*transparency), )
            sign.putpixel((i, k), color)
    return sign

#PIL图片保存为base64编码
def PIL_base64(img, coding='utf-8'):
    img_format = img.format
    if img_format == None:
        img_format = 'JPEG'
 
    format_str = 'JPEG'
    if 'png' == img_format.lower():
        format_str = 'PNG'
    if 'gif' == img_format.lower():
        format_str = 'gif'
 
    if img.mode == "P":
        img = img.convert('RGB')
    if img.mode == "RGBA":
        format_str = 'PNG'
        img_format = 'PNG'
 
    output_buffer = BytesIO()
    # img.save(output_buffer, format=format_str)
    img.save(output_buffer, quality=100, format=format_str)
    byte_data = output_buffer.getvalue()
    base64_str = 'data:image/' + img_format.lower() + ';base64,' + base64.b64encode(byte_data).decode(coding)
    return base64_str


def cut_sign(sign_path,times,transparency):
    """
    将印章图片按宽度切分成数组
    """
    times = times if times <= 10 else 10  # 判定pdf页数，如果页数少，按页数切分
    
    sign = png_transparency(sign_path,transparency)
    
    image=sign.resize((size,size))  
    cut = math.ceil(size/times)  #向上取整
    out_image  = []
    for i in range(times):
        box = (i*cut,0,(i+1)*cut,size)
        img = image.crop(box)
        im = Image.new("RGBA", (cut, size))
        im.paste(img,(0,0))
        out_image.append(im)
    return out_image

def a4_sign(a4_image_path,sign,height):
    """
    A4图，添加骑缝章的图片覆盖
    """
    a4_size = (595 * beishu,842 * beishu)
    # a4_image=Image.open(a4_image_path)
    a4_image=a4_image_path
    image=a4_image.resize(a4_size)  #缩放到A4尺寸
    layer=Image.new('RGBA',a4_size, (0,0,0,0)) #创建空白的A4
    layer.paste(sign,(595 * beishu-sign.size[0],height)) #sign 透明底
    out=Image.composite(layer,image,layer)
    return out

def a4_sign2(a4_image_path,sign,coordinate):
    """
    A4图，添加完整印章
    """

    a4_size = (595 * beishu,842 * beishu)
    # a4_image=Image.open(a4_image_path)
    a4_image=a4_image_path
    image=a4_image.resize(a4_size)  #缩放到A4尺寸
    layer=Image.new('RGBA',a4_size, (0,0,0,0)) #创建空白的A4
    if coordinate:
        layer.paste(sign,(coordinate)) #sign 透明底，坐标
    out=Image.composite(layer,image,layer)

    return out

def create_jpg(pdf_path,sign_path,coordinate,height,transparency,show_cut):
    """
    PDF 文件添加骑缝章和印章。
    """
    images = convert_from_path(pdf_path)
    times =  len(images) if len(images) <= 10 else 10  # 判定pdf页数，如果页数少，按页数切分

    sign_path = Image.open(sign_path)
    sign=png_transparency(sign_path,transparency)

    sign_image_full =sign.resize((size,size)) 

    out_images = []  #存储盖章好的图片


    if show_cut == True:
        sign_images = cut_sign(sign_path,times,transparency)

    for index,image in enumerate(images):

        try:
            # 查找当页是否有需要盖章的坐标
            x_y = coordinate[index]
        except  Exception as e:
            x_y = False

        image_new = a4_sign2(image,sign_image_full,x_y)

        if show_cut == True:#处理每张图片的骑缝
            sing_image = sign_images[index%times]  #余数，获取当前页数对应的骑缝章的id
            image_new = a4_sign(image_new,sing_image,height*beishu)

        # print(coordinate)

        out_images.append(image_new)
    file_name_out = f"{pdf_path.split('/')[-1][:-4]}_sign.pdf"  #盖章文件名
    out_images[0].save(f"upload/pdf/"+file_name_out, save_all=True, append_images=out_images[1:])  #合成pdf
    return file_name_out


def setDir(filepath):
    if not os.path.exists(filepath):
        os.mkdir(filepath)
    else:
        shutil.rmtree(filepath)
        os.mkdir(filepath)
    return filepath

def pdf2image(pdf_path):
    """
    pdf转图片，填充至前端
    """
    images = convert_from_path(pdf_path)
    jpg_list = []

    #创建文件名的文件夹，存放图片
    file_dir = pdf_path.split('/')[-1].split('.')[0]
    filepath = setDir(f'upload/jpg/{file_dir}')

    for index,image in enumerate(images):
        jpg_path = f'{filepath}/{index}.jpg'
        image.save(jpg_path)
        jpg_list.append(f"/{jpg_path}")
    return jpg_list
    