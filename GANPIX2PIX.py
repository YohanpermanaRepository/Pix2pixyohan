import streamlit as st
import torch
from torchvision import transforms
from PIL import Image
import numpy as np
from skimage.color import rgb2lab, lab2rgb
import matplotlib.pyplot as plt
from io import BytesIO
import os
import gdown
import streamlit as st
import torch
from torchvision import transforms
from PIL import Image
import numpy as np
from skimage.color import rgb2lab, lab2rgb
import matplotlib.pyplot as plt
from io import BytesIO
import glob
from torch import nn
import cv2 as cv
import streamlit as st
import os
import gdown
import numpy as np
import cv2 as cv
import torch
from PIL import Image
from io import BytesIO
from torchvision import transforms
from skimage.color import rgb2lab, lab2rgb

import streamlit as st
import tensorflow as tf
import numpy as np
from PIL import Image
import cv2 as cv
import io
import gdown
import os
import io

def upsample(c_in, c_out, dropout=False):
    result = nn.Sequential()
    result.add_module('con', nn.ConvTranspose2d(c_in, c_out, kernel_size=4, stride=2, padding=1, bias=False))
    result.add_module('bat', nn.BatchNorm2d(c_out))
    if dropout:
        result.add_module('drop', nn.Dropout2d(0.5, inplace=True))
    result.add_module('relu', nn.ReLU(inplace=False))
    return result

def downsample(c_in, c_out, batchnorm=True):
    result = nn.Sequential()
    result.add_module('con', nn.Conv2d(c_in, c_out, kernel_size=4, stride=2, padding=1, bias=False))
    if batchnorm:
        result.add_module('batc', nn.BatchNorm2d(c_out))
    result.add_module('LRelu', nn.LeakyReLU(0.2, inplace=False))
    return result

class Generator(nn.Module):
    def __init__(self, input_nc=1, output_nc=2, n_filters=64):
        super(Generator, self).__init__()

        layer1 = nn.Conv2d(input_nc, n_filters, kernel_size=4, stride=2, padding=1, bias=False)
        layer2 = downsample(n_filters, n_filters * 2)
        layer3 = downsample(n_filters * 2, n_filters * 4)
        layer4 = downsample(n_filters * 4, n_filters * 8)
        layer5 = downsample(n_filters * 8, n_filters * 8)
        layer6 = downsample(n_filters * 8, n_filters * 8)
        layer7 = downsample(n_filters * 8, n_filters * 8)
        layer8 = downsample(n_filters * 8, n_filters * 8)

        # Decoder
        d_inc = n_filters * 8
        dlayer8 = upsample(d_inc, n_filters * 8, dropout=True)
        dlayer7 = upsample(n_filters * 8 * 2, n_filters * 8, dropout=True)
        dlayer6 = upsample(n_filters * 8 * 2, n_filters * 8, dropout=True)
        dlayer5 = upsample(n_filters * 8 * 2, n_filters * 8)
        dlayer4 = upsample(n_filters * 8 * 2, n_filters * 4)
        dlayer3 = upsample(n_filters * 4 * 2, n_filters * 2)
        dlayer2 = upsample(n_filters * 2 * 2, n_filters)

        dlayer1 = nn.Sequential()
        dlayer1.add_module('relu', nn.ReLU(inplace=False))
        dlayer1.add_module('t_conv', nn.ConvTranspose2d(n_filters * 2, output_nc, kernel_size=4, stride=2, padding=1, bias=False))
        dlayer1.add_module('tanh', nn.Tanh())

        self.layer1 = layer1
        self.layer2 = layer2
        self.layer3 = layer3
        self.layer4 = layer4
        self.layer5 = layer5
        self.layer6 = layer6
        self.layer7 = layer7
        self.layer8 = layer8
        self.dlayer8 = dlayer8
        self.dlayer7 = dlayer7
        self.dlayer6 = dlayer6
        self.dlayer5 = dlayer5
        self.dlayer4 = dlayer4
        self.dlayer3 = dlayer3
        self.dlayer2 = dlayer2
        self.dlayer1 = dlayer1

    def forward(self, input):
        out1 = self.layer1(input)
        out2 = self.layer2(out1)
        out3 = self.layer3(out2)
        out4 = self.layer4(out3)
        out5 = self.layer5(out4)
        out6 = self.layer6(out5)
        out7 = self.layer7(out6)
        out8 = self.layer8(out7)
        dout8 = self.dlayer8(out8)
        dout8_out7 = torch.cat([dout8, out7], 1)
        dout7 = self.dlayer7(dout8_out7)
        dout7_out6 = torch.cat([dout7, out6], 1)
        dout6 = self.dlayer6(dout7_out6)
        dout6_out5 = torch.cat([dout6, out5], 1)
        dout5 = self.dlayer5(dout6_out5)
        dout5_out4 = torch.cat([dout5, out4], 1)
        dout4 = self.dlayer4(dout5_out4)
        dout4_out3 = torch.cat([dout4, out3], 1)
        dout3 = self.dlayer3(dout4_out3)
        dout3_out2 = torch.cat([dout3, out2], 1)
        dout2 = self.dlayer2(dout3_out2)
        dout2_out1 = torch.cat([dout2, out1], 1)
        dout1 = self.dlayer1(dout2_out1)
        return dout1

# Fungsi untuk mengonversi Lab ke RGB tetap sama
def lab_to_rgb(L, ab):
    L = (L + 1.) * 50.
    ab = ab * 110.
    Lab = torch.cat([L, ab], dim=1).permute(0, 2, 3, 1).cpu().numpy()
    rgb_imgs = []
    for img in Lab:
        img_rgb = lab2rgb(img)
        rgb_imgs.append(img_rgb)
    return np.stack(rgb_imgs, axis=0)



# Fungsi unduhan file model
def download_model_if_not_exists(model_path, file_id):
    if not os.path.exists(model_path):
        download_url = f'https://drive.google.com/uc?id={file_id}'
        gdown.download(download_url, model_path, quiet=False)

# Fungsi untuk memuat model berdasarkan nama file path
def load_model(model_path):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    net_G = Generator().to(device)
    net_G.load_state_dict(torch.load(model_path, map_location=device))
    net_G.eval()
    return net_G

# Dropdown untuk memilih model
model_options = {
    # "Epoch 40": "1YlNWW59g7A8vwjKXT1RyX9zRw4ao2FrW",
    # "Epoch 60": "1rwuc0qOABxSalJlVsRQ7rY6vpv91zGhn",  
    # "Epoch 80": "1QFixPuRO5G3ZCyYsMvKpxvfBNS4R0HK8",
    # "Epoch 100": "1bVKGgGjHdX4F2t3n3LiKfHyQwHj9ltTP",
    # "Epoch 150": "1PMQVxvDTmLqP1DhX8xmP3K_iw_RCJsQN"

    "Epoch 10": "1VFfEy00mhdlbrNbOGxHCdgY-D4OvcojX",
    "Epoch 50": "1_k8X8uls8Fnt2qQ0xmrx-BC7ogiA6y1c",  
    "Epoch 100": "1oLx_mC5gI0LGaP7CX0ZubGhJwFBE3Rpd",

    
}


# Sidebar untuk memilih metode

method = st.sidebar.selectbox("Pilih Metode", ["-", "GAN 1 With Tensorflow", "GAN 2 With Pytroch", "CNN Pretrained Caffe"])


if method == "-":
    st.write("**Here are some Batik Madura images you can download:**")

    # Batik Madura images directory
    batik_images = {
        "Batik Madura 1": "TESTING/test_madura (1).jpg", 
        "Batik Madura 2": "TESTING/test_madura (2).jpg", 
        "Batik Madura 3": "TESTING/test_madura (3).jpg", 
        "Batik Madura 4": "TESTING/test_madura (4).jpg", 
        "Batik Madura 5": "TESTING/test_madura (5).jpg", 
        "Batik BALI 1": "TESTING/test_bali (1).jpg", 
        "Batik Bali 2": "TESTING/test_bali (2).jpg", 
        "Batik Bali 3": "TESTING/test_bali (3).jpg", 
        "Batik Bali 4": "TESTING/test_bali (4).jpg", 
        "Batik Bali 5": "TESTING/test_bali (5).jpg", 
    }

    # Display Batik images in a grid with consistent size
    cols = st.columns(5)  # Create 5 columns for the grid
    for i, (batik_name, batik_path) in enumerate(batik_images.items()):
        # Resize image to a consistent size
        batik_img = Image.open(batik_path).resize((256, 256)) 

        # Select the appropriate column
        col = cols[i % 5]
        with col:
            st.image(batik_img, caption=batik_name, use_container_width=True)  # Fixed the error
            
            # Add download button for each image
            buf = io.BytesIO()
            batik_img.save(buf, format="PNG")
            byte_im = buf.getvalue()
            st.download_button(
                label="Download",
                data=byte_im,
                file_name=f"{batik_name}.png",
                mime="image/png"
            )


elif method == "GAN 1 With Tensorflow":
    # Fungsi untuk mengunduh model dari Google Drive menggunakan gdown
    def download_model_from_drive(model_id, output_path):
        url = f"https://drive.google.com/uc?id={model_id}"
        gdown.download(url, output_path, quiet=False)

    # Fungsi untuk memuat model generator yang disimpan dalam format .h5
    @st.cache_resource
    def load_model(model_path, model_id):
        if not os.path.exists(model_path):
            st.warning(f"Mengunduh model dari Google Drive ke: {model_path}")
            download_model_from_drive(model_id, model_path)
        model = tf.keras.models.load_model(model_path)
        return model

    # Fungsi untuk melakukan prediksi pada gambar grayscale dengan model GAN
    def predict_image(generator, grayscale_image):
        grayscale_image = np.array(grayscale_image)
        grayscale_image = cv.resize(grayscale_image, (256, 256))
        grayscale_image = grayscale_image.astype('float32') / 255.0
        grayscale_image = np.expand_dims(grayscale_image, axis=-1)  # Ubah jadi 1 channel
        grayscale_image = np.repeat(grayscale_image, 3, axis=-1)  # Ubah jadi 3 channel
        grayscale_image = np.expand_dims(grayscale_image, axis=0)  # Tambah dimensi batch
        prediction = generator.predict(grayscale_image)
        prediction = np.clip(prediction[0], 0, 1)
        return prediction

    # Menggunakan komponen file_uploader di layout utama
    uploaded_files = st.file_uploader("Pilih gambar", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    # Jika tidak ada gambar yang diunggah, tampilkan teks sambutan
    if not uploaded_files:
        st.title("Image Colorization with GAN 1 Tensorflow")

    else:
        # Jika gambar telah diunggah, hilangkan teks sambutan
        st.title("Hasil Prediksi Gambar Berwarna menggunakan GAN")

        # Dropdown untuk memilih model GAN di layout utama
        model_option = st.selectbox(
            "Pilih model GAN",
            ["Model Epoch 40", "Model Epoch 100"]
        )

        # Menentukan path model dan Google Drive ID berdasarkan pilihan dropdown
        model_info = {
            "Model Epoch 40": ("generator_epoch40.h5", "122vKlan3zBfSHA4mq4OJiPQpSM9CqDDa"),
            "Model Epoch 100": ("generator_epoch100.h5", "1q4LNa__tLMV9C_NDH2MekP2XVaLKNXT3")
        }
        model_path, model_id = model_info[model_option]

        # Load model GAN yang sudah dilatih
        generator = load_model(model_path, model_id)

        for uploaded_file in uploaded_files:
            # Membaca gambar dalam grayscale
            grayscale_image = Image.open(uploaded_file).convert("L")

            # Prediksi gambar berwarna dengan GAN
            prediction_image = predict_image(generator, grayscale_image)

            # Ubah ukuran gambar agar konsisten
            target_size = (256, 256)
            grayscale_image = grayscale_image.resize(target_size)
            input_image = Image.open(uploaded_file).resize(target_size)
            prediction_image = Image.fromarray((prediction_image * 255).astype(np.uint8)).resize(target_size)

            # Menampilkan gambar inputan, grayscale, dan hasil prediksi
            col1, col2, col3 = st.columns(3)
            with col1:
                st.image(input_image, caption="Gambar Inputan", use_column_width=True)
            with col2:
                st.image(grayscale_image, caption="Gambar Grayscale", use_column_width=True)
            with col3:
                st.image(prediction_image, caption="Gambar Hasil Prediksi", use_column_width=True)

            # Menyimpan dan mengunduh gambar hasil prediksi
            save_path = f"predicted_{uploaded_file.name}"
            img_bytes = io.BytesIO()
            prediction_image.save(img_bytes, format='PNG')
            img_bytes.seek(0)

            st.download_button(
                label=f"Download Gambar Hasil Prediksi",
                data=img_bytes,
                file_name=save_path,
                mime="image/png"
            )




# elif method == "GAN 2 With Pytroch":


    
#     st.title("Image Colorization with GAN 2 Pytroch")


#     selected_model_name = st.selectbox("Pilih Pretrained Model", list(model_options.keys()))
#     selected_model_file_id = model_options[selected_model_name]
#     model_path = f'{selected_model_name}.pth'


#     # Unduh model jika belum ada
#     download_model_if_not_exists(model_path, selected_model_file_id)

#     # Load model yang dipilih
#     net_G = load_model(model_path)

#     # Definisikan device untuk pemrosesan (CPU atau GPU)
#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

#     # Pengunggah file (dengan multiple file upload)
#     uploaded_files = st.file_uploader("Choose images...", type="jpg", accept_multiple_files=True)

#     if uploaded_files:
#         for uploaded_file in uploaded_files:
#             image = Image.open(uploaded_file).convert("RGB")
            
#             # Crop gambar agar ukuran sama
#             size = (256, 256)  # Ukuran yang diinginkan
#             image_cropped = image.resize(size, Image.LANCZOS)  # Menggunakan LANCZOS sebagai alternatif

#             # Pra-pemrosesan gambar
#             img = np.array(image_cropped)
#             img_lab = rgb2lab(img).astype("float32")
#             img_lab = transforms.ToTensor()(img_lab)
#             L = img_lab[[0], ...] / 50. - 1.  # Saluran warna luminance

#             # Membuat tensor
#             L = L.unsqueeze(0).to(device)

#             # Membuat Gambar Grayscale dari saluran L
#             gray_image = (L.squeeze().cpu().numpy() + 1.) * 255 / 2  # Mengonversi saluran L ke rentang [0, 255]
#             gray_image = gray_image.astype(np.uint8)  # Mengubah ke uint8

#             # Meneruskan melalui model
#             with torch.no_grad():
#                 fake_color = net_G(L)
#                 fake_color = fake_color.detach()

#             # Mengonversi Lab ke RGB
#             fake_imgs = lab_to_rgb(L, fake_color)
#             fake_img = fake_imgs[0]

#             # Menampilkan gambar keluaran dalam satu baris
#             col1, col2, col3 = st.columns(3)

#             with col1:
#                 st.image(image_cropped, caption='Uploaded Image', use_column_width=True)

#             with col2:
#                 st.image(gray_image, caption='Grayscale Image (L channel)', use_column_width=True, clamp=True)

#             with col3:
#                 st.image(fake_img, caption='Colorized Image', use_column_width=True)

#             # Opsi untuk mengunduh hasil
#             result = Image.fromarray((fake_img * 255).astype(np.uint8))
#             buf = BytesIO()
#             result.save(buf, format="JPEG")
#             byte_im = buf.getvalue()
#             st.download_button(f"Download Result for {uploaded_file.name}", data=byte_im, file_name=f"colorized_image_{uploaded_file.name}", mime="image/jpeg")


elif method == "GAN 2 With Pytroch":

    st.title("Image Colorization with GAN 2 Pytroch")

    selected_model_name = st.selectbox("Pilih Pretrained Model", list(model_options.keys()))
    selected_model_file_id = model_options[selected_model_name]
    model_path = f'{selected_model_name}.pth'

    # Unduh model jika belum ada
    download_model_if_not_exists(model_path, selected_model_file_id)

    # Load model yang dipilih
    net_G = load_model(model_path)

    # Definisikan device untuk pemrosesan (CPU atau GPU)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Pengunggah file (dengan multiple file upload), memungkinkan jpg dan png
    uploaded_files = st.file_uploader("Choose images...", type=["jpg", "png"], accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            image = Image.open(uploaded_file).convert("RGB")
            
            # Crop gambar agar ukuran sama
            size = (256, 256)  # Ukuran yang diinginkan
            image_cropped = image.resize(size, Image.LANCZOS)  # Menggunakan LANCZOS sebagai alternatif

            # Pra-pemrosesan gambar
            img = np.array(image_cropped)
            img_lab = rgb2lab(img).astype("float32")
            img_lab = transforms.ToTensor()(img_lab)
            L = img_lab[[0], ...] / 50. - 1.  # Saluran warna luminance

            # Membuat tensor
            L = L.unsqueeze(0).to(device)

            # Membuat Gambar Grayscale dari saluran L
            gray_image = (L.squeeze().cpu().numpy() + 1.) * 255 / 2  # Mengonversi saluran L ke rentang [0, 255]
            gray_image = gray_image.astype(np.uint8)  # Mengubah ke uint8

            # Meneruskan melalui model
            with torch.no_grad():
                fake_color = net_G(L)
                fake_color = fake_color.detach()

            # Mengonversi Lab ke RGB
            fake_imgs = lab_to_rgb(L, fake_color)
            fake_img = fake_imgs[0]

            # Menampilkan gambar keluaran dalam satu baris
            col1, col2, col3 = st.columns(3)

            with col1:
                st.image(image_cropped, caption='Uploaded Image', use_container_width=True)

            with col2:
                st.image(gray_image, caption='Grayscale Image (L channel)', use_container_width=True, clamp=True)

            with col3:
                st.image(fake_img, caption='Colorized Image', use_container_width=True)

            # Opsi untuk mengunduh hasil
            result = Image.fromarray((fake_img * 255).astype(np.uint8))
            buf = BytesIO()
            result.save(buf, format="PNG")  # Save as PNG format
            byte_im = buf.getvalue()
            st.download_button(f"Download Result for {uploaded_file.name}", data=byte_im, file_name=f"colorized_image_{uploaded_file.name}.png", mime="image/png")  # Set MIME type for PNG




# Model OpenCV
elif method == "CNN Pretrained Caffe":
    st.title("Image Colorization with CNN Pretrained Caffe")

    # Define paths for model files
    DIR = 'model'
    if not os.path.exists(DIR):
        os.makedirs(DIR)

    # Paths for model files
    PROTOTXT_PATH = os.path.join(DIR, 'colorization_deploy_v2.prototxt')
    POINTS_PATH = os.path.join(DIR, 'pts_in_hull.npy')
    MODEL_PATH = os.path.join(DIR, 'colorization_release_v2.caffemodel')

    # Check if model files exist, if not download
    if not (os.path.exists(PROTOTXT_PATH) and os.path.exists(POINTS_PATH) and os.path.exists(MODEL_PATH)):
        st.write("Downloading model files...")
        # URLs for model files on Google Drive
        PROTOTXT_URL = 'https://drive.google.com/uc?id=1DZ4cFBYC3_KjOn2ayrhnk2XKHt6E54EJ'
        POINTS_URL = 'https://drive.google.com/uc?id=1Qh54l1Jhh5psiytgsv9WmJVByjpHdF8o'
        MODEL_URL = 'https://drive.google.com/uc?id=1RCb6SJN2T5tdrpPUXEx0L4GBaTtc2OcL'

        # Download the model files
        gdown.download(PROTOTXT_URL, PROTOTXT_PATH, quiet=False)
        gdown.download(POINTS_URL, POINTS_PATH, quiet=False)
        gdown.download(MODEL_URL, MODEL_PATH, quiet=False)

    # Load the Model
    net = cv.dnn.readNetFromCaffe(PROTOTXT_PATH, MODEL_PATH)
    pts = np.load(POINTS_PATH)

    # Load centers for ab channel quantization used for rebalancing
    class8 = net.getLayerId("class8_ab")
    conv8 = net.getLayerId("conv8_313_rh")
    pts = pts.transpose().reshape(2, 313, 1, 1)
    net.getLayer(class8).blobs = [pts.astype("float32")]
    net.getLayer(conv8).blobs = [np.full([1, 313], 2.606, dtype="float32")]

    # Upload images
    uploaded_files = st.file_uploader("Choose images...", type=["jpg", "jpeg", "png"], accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Read the uploaded image
            image = cv.imdecode(np.frombuffer(uploaded_file.read(), np.uint8), cv.IMREAD_COLOR)
            
            # Resize the image to 256x256 pixels
            image_resized = cv.resize(image, (256, 256))
            
            # Convert the image to grayscale
            gray_image = cv.cvtColor(image_resized, cv.COLOR_BGR2GRAY)

            # Process the image
            scaled = image_resized.astype("float32") / 255.0
            lab = cv.cvtColor(scaled, cv.COLOR_BGR2LAB)
            
            resized = cv.resize(lab, (224, 224))  # Resize for model input
            L = cv.split(resized)[0]
            L -= 50
            
            st.write(f"Colorizing the image: {uploaded_file.name}...")
            net.setInput(cv.dnn.blobFromImage(L))
            ab = net.forward()[0, :, :, :].transpose((1, 2, 0))
            
            ab = cv.resize(ab, (image_resized.shape[1], image_resized.shape[0]))
            
            L = cv.split(lab)[0]
            colorized = np.concatenate((L[:, :, np.newaxis], ab), axis=2)
            
            colorized = cv.cvtColor(colorized, cv.COLOR_LAB2BGR)
            colorized = np.clip(colorized, 0, 1)
            colorized = (255 * colorized).astype("uint8")
            
            # Display images in a row
            col1, col2, col3 = st.columns(3)

            with col1:
                st.image(image_resized, channels="BGR", caption='Uploaded Image', use_column_width=True)

            with col2:
                st.image(gray_image, channels="GRAY", caption="Grayscale Image (L channel)", use_column_width=True)

            with col3:
                st.image(colorized, channels="BGR", caption='Colorized Image', use_column_width=True)

            # Option to download the colorized image
            result_image = cv.imencode('.png', colorized)[1].tobytes()
            st.download_button(label=f"Download Colorized Image - {uploaded_file.name}", data=result_image, file_name=f"colorized_{uploaded_file.name}", mime="image/png")
