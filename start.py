import json
from flask import Flask,send_from_directory,request,render_template
from werkzeug.utils import secure_filename
from pypinyin import lazy_pinyin
from PIL import Image
# from flask_cors import CORS
from r_tool import create_jpg,pdf2image,cut_sign,PIL_base64

app = Flask(__name__,
            template_folder='dist',
            static_folder='dist/assets',
            )
# CORS(app)

@app.route('/api/upload_pdf', methods=['POST'])
def upload_pdf():
    """
    上传PDF文件
    """
    if request.method == 'POST':
        file = request.files['file'] #获取上传的文件
        filename = secure_filename(''.join(lazy_pinyin(file.filename)))
        filename = filename.lower()
        
        if filename.endswith('.pdf'):
            pdf_file_path = f"upload/pdf/{filename}"
            file.save(pdf_file_path)
            images = pdf2image(pdf_file_path)
            response_text = {
                "status":"ok",
                "data":{
                    "filename":filename,
                    "url":pdf_file_path,
                    "page_number":len(images),
                    "images":images
                }
            }
        else:
            response_text = {
                "status":"error",
                "data":{
                    "message":"非PDF文件"
                }
            }
        return json.dumps(response_text),201


@app.route('/api/upload_sign', methods=['POST'])
def upload_sign():
    """
    上传印章图片，需要是png格式
    """
    if request.method == 'POST':
        file = request.files['avatar'] #获取上传的文件
        filename = secure_filename(''.join(lazy_pinyin(file.filename)))
        filename = filename.lower()
        
        if filename.endswith('.png'):
            sign_file_path = f"upload/sign/{filename}"
            file.save(sign_file_path)
            
            response_text = {
                "status":"ok",
                "data":{
                    "filename":filename,
                    "url":sign_file_path,
                }
            }
        else:
            response_text = {
                "status":"error",
                "data":{
                    "message":"非png文件"
                }
            }
        return json.dumps(response_text),201


@app.route('/api/sign_cut', methods=['POST'])
def sign_cut():
    """
    裁剪骑缝章
    """
    if request.method == 'POST':
        req_data = json.loads(request.data)
        sign_url = req_data['sign_url'] 
        cut_times = req_data['cut_times'] 
        transparency = float(req_data['transparency'])

        sign = Image.open(sign_url)
        images = cut_sign(sign,cut_times,transparency)

        images_base64 = [PIL_base64(x) for x in images]

        image_size = images[0].size

        response_text = {
            "status":"ok",
            "data":{
                "image_size":{
                    "w":int(image_size[0]/2),
                    "h":int(image_size[1]/2)
                    },
                "images":images_base64
            }
        }
        return json.dumps(response_text),201


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:filename>')
def public(filename):
    """
    访问public文件夹的文件
    """
    return send_from_directory('dist', filename)

@app.route('/upload/<path:upload_file>')
def upload_file(upload_file):
    """
    访问upload文件夹的文件
    """
    return send_from_directory('upload', upload_file)


@app.route('/api/get_pdf_signed', methods=['POST', 'GET'])
def get_pdf_signed():
    """
    生成盖章后的PDF文件
    """

    if request.method == 'POST':
        data_json = json.loads(request.data)
        pdf_path = data_json['pdf_url']
        sign_path = data_json['sign_url']
        height = data_json['height']
        transparency = float(data_json['transparency'] ) 
        show_cut = data_json['show_cut']
        
        coordinate = {}
        # 拼接印章坐标数据，对应到page数
        for i in data_json['image_list']:
            if i['signed'] == True:
                coordinate[i['page']] = (i['x']*2,i['y']*2)

        response_filename = create_jpg(pdf_path,sign_path,coordinate,height,transparency,show_cut)

        response_text = {
            "status":"ok",
            "data":{
                "pdf_name":response_filename,
                "pdf_signed_url":f"/upload/pdf/{response_filename}"
            }
        }
        return json.dumps(response_text),201

if __name__ == '__main__':
    app.run(debug=True)