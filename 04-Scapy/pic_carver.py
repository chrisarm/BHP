import zlib
import cv2

from scapy.all import *

gverbose = True
pictures_dir = 'pics'
faces_dir = 'pics/faces'
pcap_file = 'bhp_faces.pcap'


def vprint(verbose_string, lverbose=False):
    '''
        Enables verbose printing with a custom line icon in brackets.
    '''
    global gverbose
    if lverbose or gverbose:
        if gverbose is True:
            icon = '*'
        else:
            icon = '[{}]'.format(lverbose)
        print('{} {}'.format(icon, verbose_string))


def get_http_headers(http_session, search=b'\r\n\r\n'):
    header_values = ''
    try:
        index1 = http_session.index(search) + 2
        headers = http_session[:index1].decode()
        header_values = dict(re.findall(
            r'(?P<name>.*?): (?P<value>.*?)\r\n',
            headers))
    except UnicodeDecodeError:
        return None
    except ValueError:
        return None
    except Exception:
        raise

    if b'Content-Type' not in http_session:
        return None
    return header_values


def extract_images(headers, http_session):
    image = None
    image_type = None
    images = list()
    max_index = len(http_session)
    try:
        index1 = http_session.index(b'\r\n\r\n') + 4
        index2 = http_session[index1:].index(b'\r\n\r\n') + index1
    except ValueError:
        vprint('Indexes not set.')
        pass
    except Exception:
        raise

    while index1 < max_index and index2 < max_index:
        try:
            if not 'image' in headers['Content-Type']:
                break
            else:
                image_type = headers['Content-Type'].split('/')[1]
                image = http_session[index1:index2]
                try:
                    if 'Content-Encoding' in headers.keys():
                        if headers['Content-Encoding'] == 'gzip':
                            image = zlib.decompress(image, 16 + zlib.MAX_WBITS)
                        elif headers['Content-Encoding'] == 'deflate':
                            image = zlib.decompress(image)
                    if len(image) > 512:
                        images.append((image, image_type))
                except Exception:
                    raise
                # Set index 1 to get next header
                index1 = http_session[index2:].index(b'HTTP/') + index2
                headers = get_http_headers(http_session[index1:])

                # Set index to image data or max to move on
                if not headers:
                    index1 = max_index
                    break
                else:
                    index1 = index1 + 288
                    index2 = index1 + int(headers['Content-Length'])
        except KeyError:
            vprint('No image in this part of the session.')
            break
        except ValueError:
            vprint('Indexes not set. Session end.')
            break
        except Exception:
            raise
    if len(images) >= 1:
        vprint('Returning image list: {}'.format(len(images)))
        return images
    else:
        vprint('No image in session.')
        return None


def face_detect(path, file_name):
    img = cv2.imread(path)
    cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt.xml')
    rects = cascade.detectMultiScale(
        img,
        1.3,
        4,
        cv2.CASCADE_SCALE_IMAGE,
        (20, 20))

    if len(rects) == 0:
        return False

    rects[:, 2:] += rects[:, :2]

    for x1, y1, x2, y2 in rects:
        cv2.rectangle(img, (x1, y1), (x2, y2), (127, 255, 0), 2)

    cv2.imwrite('{}/{}'.format(faces_dir, file_name), img)
    return True


def http_assembler(pcap_file):
    carved_images = 0
    faces_detected = 0

    a = rdpcap(pcap_file)
    sessions = a.sessions()

    for session in sessions:
        http_session = b''
        for packet in sessions[session]:
            try:
                if packet[TCP].dport == 80 or packet[TCP].sport == 80:
                    if not isinstance(packet[TCP].payload, scapy.packet.NoPayload):
                        payload = bytes(packet[TCP].payload)
                        http_session += payload
            except Exception:
                pass
        headers = get_http_headers(http_session)
        if headers is None:
            continue

        images = extract_images(headers, http_session)
        index = 0
        if images:
            for image_data in images:
                image = image_data[0]
                image_type = image_data[1]
                
                if image is not None and image_type is not None:
                    file_name = '{}-pic_carver_{}_{}.{}'.format(
                                    pcap_file,
                                    carved_images,
                                    index,
                                    image_type)
                    with open('{}/{}'.format(pictures_dir, file_name), 'wb') as fd:
                        fd.write(image)
                    carved_images += 1
                    index += 1
                    try:
                        result = face_detect(
                            '{}/{}'.format(pictures_dir, file_name),
                            file_name)
                        if result:
                            faces_detected += 1
                    except Exception:
                        pass
    return carved_images, faces_detected


carved_images, faces_detected = http_assembler(pcap_file)

vprint('Extracted: {}'.format(carved_images))
vprint('Detected: {}'.format(faces_detected))
