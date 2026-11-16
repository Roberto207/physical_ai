import time, zlib, struct, math
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan, Image

def png(path, w, h, rgb):
    raw = b''.join(b'\x00' + rgb[y*w*3:(y+1)*w*3] for y in range(h))
    def ch(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ch(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + ch(b'IDAT', zlib.compress(raw)) + ch(b'IEND', b''))

class N(Node):
    def __init__(self):
        super().__init__('sensores')
        self.t = {'scan': [], 'img': []}
        self.scan = None; self.img = None
        self.create_subscription(LaserScan, '/scan', self.cs, qos_profile_sensor_data)
        self.create_subscription(Image, '/oakd/rgb/preview/image_raw', self.ci, qos_profile_sensor_data)
    def cs(self, m): self.t['scan'].append(time.time()); self.scan = m
    def ci(self, m): self.t['img'].append(time.time()); self.img = m

rclpy.init(); n = N(); fim = time.time() + 20
while time.time() < fim: rclpy.spin_once(n, timeout_sec=0.2)
for k, v in n.t.items():
    print(k, 'mensagens em 20 s:', len(v), '-> %.1f Hz (tempo real)' % (len(v)/20))
s = n.scan
if s:
    r = [x for x in s.ranges if math.isfinite(x)]
    print('LIDAR: %d raios, angulo %.0f a %.0f graus, alcance %.2f a %.1f m' % (len(s.ranges), math.degrees(s.angle_min), math.degrees(s.angle_max), s.range_min, s.range_max))
    print('  raios com leitura valida:', len(r), '| mais perto: %.2f m | mais longe: %.2f m' % (min(r), max(r)) if r else '  nenhum raio bateu em nada (mundo vazio)')
i = n.img
if i:
    print('CAMERA:', i.width, 'x', i.height, i.encoding)
    d = bytes(i.data)
    if i.encoding in ('rgb8', 'bgr8'):
        rgb = d if i.encoding == 'rgb8' else b''.join(d[j+2:j+3] + d[j+1:j+2] + d[j:j+1] for j in range(0, len(d), 3))
        png('/tmp/camera.png', i.width, i.height, rgb)
        print('PNG salvo em /tmp/camera.png (no container)')
