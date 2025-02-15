import cv2
import numpy as np

from multiprocessing import Process

from .infer.utility import parse_args, init_args
from .infer import TextSystem, predict_system
from .infer import TextDetector, predict_det
from .infer import TextClassifier, predict_cls
from .infer import TextRecognizer, predict_rec


class OCRSystem:
    def __init__(self, config=None, args=None):
        if args is None and config is not None:
            self.args = parse_args(config)
        elif args is not None:
            self.args = args
        else:
            raise ValueError ('Please check the config.')

        self.load()

    def load(self):
        self.text_sys = TextSystem(self.args)

    def run(self, func, image_dir):
        del self.text_sys
        if self.args.total_process_num > 1:
            p_list = []
            for process_id in range(self.args.total_process_num):
                p = Process(target=func, args=(self.args, image_dir, process_id))
                p.start()
                p_list.append(p)
            for p in p_list:
                p.join()
        else:
            func(self.args, image_dir)
        self.load()

    def __call__(self, img, det=True, cls=True, rec=True, return_cls=False):
        return self.ocr(img, det=det, cls=cls, rec=rec, return_cls=return_cls)

    def ocr(self, img, det=True, cls=True, rec=True, return_cls=False):
        if isinstance(img, np.ndarray):
            results = self.text_sys(img, det=det, cls=cls, rec=rec, return_cls=return_cls)
        elif isinstance(img, str):
            results = self.text_sys(cv2.imread(img), det=det, cls=cls, rec=rec, return_cls=return_cls)
        return results

    def predict_det(self, image_dir):
        self.run(predict_det, image_dir)

    def predict_cls(self, image_dir):
        self.run(predict_cls, image_dir)

    def predict_rec(self, image_dir):
        self.run(predict_rec, image_dir)

    def predict_system(self, image_dir):
        self.run(predict_system, image_dir)


def command():
    import json
    parser = init_args()
    parser.add_argument(dest='mode', type=str)
    parser.add_argument("--config", type=str)
    parser.add_argument("--image_dir", type=str, required=True)
    args = parser.parse_known_args()[0]

    if args.config:
        with open(args.config, 'r', encoding='UTF-8') as f:
            json_dict = json.load(f)

        argparse_dict = vars(args)
        argparse_dict.update(json_dict)

    ocr = OCRSystem(args=args)

    if args.mode == 'cls':
        ocr.predict_cls(args.image_dir)
    elif args.mode == 'det':
        ocr.predict_det(args.image_dir)
    elif args.mode == 'rec':
        ocr.predict_rec(args.image_dir)
    elif args.mode == 'system':
        ocr.predict_system(args.image_dir)
    else:
        raise ValueError ('Please check the mode.')

    