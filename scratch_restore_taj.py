import urllib.request
import io
import json
from PIL import Image

def run():
    with open('web-demo/public/samples/taj_mahal_degraded.jpg', 'rb') as f:
        img_bytes = f.read()

    boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
    parts = []
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="taj.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode('utf-8'))
    parts.append(img_bytes)
    parts.append(f'\r\n--{boundary}\r\nContent-Disposition: form-data; name="options"\r\n\r\n{{"denoise": true, "colorize": true, "face_restore": false}}\r\n--{boundary}--\r\n'.encode('utf-8'))
    body = b''.join(parts)

    req = urllib.request.Request(
        'http://localhost:8000/api/v1/restore/sync',
        data=body,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )

    print('Sending restore request to backend...')
    with urllib.request.urlopen(req, timeout=120) as resp:
        restored_bytes = resp.read()
        print('Received restored bytes:', len(restored_bytes))
        print('Stages header:', resp.headers.get('X-Stages-Applied'))
        with Image.open(io.BytesIO(restored_bytes)) as im:
            im = im.convert('RGB')
            # Verify exact dimension match with degraded image
            with Image.open('web-demo/public/samples/taj_mahal_degraded.jpg') as deg:
                print('Degraded size:', deg.size)
                print('Restored size before resize:', im.size)
                if im.size != deg.size:
                    im = im.resize(deg.size, Image.Resampling.LANCZOS)
            im.save('web-demo/public/samples/taj_mahal_restored.jpg', 'JPEG', quality=88, optimize=True)
            print('Saved web-demo/public/samples/taj_mahal_restored.jpg with exact match!')

if __name__ == '__main__':
    run()
