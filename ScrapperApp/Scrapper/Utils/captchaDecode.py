import pytesseract
from PIL import Image as pimg
from wand.image import Image as wimg
import numpy
import io
import re


async def read_captcha(captcha_blob):
    pic = wimg(blob=captcha_blob)
    pic.modulate(120)
    pic.modulate(150)
    pic.modulate(130)
    #pic.save(filename='pic.png')
    img_buffer = numpy.asarray(bytearray(pic.make_blob(format='png')), dtype='uint8')
    bytesio = io.BytesIO(img_buffer)
    pil_img = pimg.open(bytesio)
    return re.sub('[\W_]+', '', pytesseract.image_to_string(pil_img))
    # return re.sub('[\W_]+', '', pytesseract.image_to_string("pic.png"))
