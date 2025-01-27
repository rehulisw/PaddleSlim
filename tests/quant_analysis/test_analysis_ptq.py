import os
import sys
import unittest
sys.path.append("../")
import paddle
from PIL import Image
from paddle.vision.datasets import DatasetFolder
from paddle.vision.transforms import transforms
from paddleslim.quant.analysis_ptq import AnalysisPTQ
paddle.enable_static()


class ImageNetDataset(DatasetFolder):
    def __init__(self, path, image_size=224):
        super(ImageNetDataset, self).__init__(path)
        normalize = transforms.Normalize(
            mean=[123.675, 116.28, 103.53], std=[58.395, 57.120, 57.375])
        self.transform = transforms.Compose([
            transforms.Resize(256), transforms.CenterCrop(image_size),
            transforms.Transpose(), normalize
        ])

    def __getitem__(self, idx):
        img_path, _ = self.samples[idx]
        return self.transform(Image.open(img_path).convert('RGB'))

    def __len__(self):
        return len(self.samples)


class AnalysisPTQDemo(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(AnalysisPTQDemo, self).__init__(*args, **kwargs)
        if not os.path.exists('MobileNetV1_infer'):
            os.system(
                'wget -q https://paddle-imagenet-models-name.bj.bcebos.com/dygraph/inference/MobileNetV1_infer.tar'
            )
            os.system('tar -xf MobileNetV1_infer.tar')
        if not os.path.exists('ILSVRC2012_data_demo'):
            os.system(
                'wget -q https://sys-p0.bj.bcebos.com/slim_ci/ILSVRC2012_data_demo.tar.gz'
            )
            os.system('tar -xf ILSVRC2012_data_demo.tar.gz')

    def test_demo(self):
        train_dataset = ImageNetDataset(
            "./ILSVRC2012_data_demo/ILSVRC2012/train/")
        image = paddle.static.data(
            name='inputs', shape=[None] + [3, 224, 224], dtype='float32')
        train_loader = paddle.io.DataLoader(
            train_dataset, feed_list=[image], batch_size=8, return_list=False)

        analyzer = AnalysisPTQ(
            model_dir="./MobileNetV1_infer",
            model_filename="inference.pdmodel",
            params_filename="inference.pdiparams",
            save_dir="MobileNetV1_analysis",
            ptq_config={
                'quantizable_op_type': ["conv2d", "depthwise_conv2d"],
                'weight_quantize_type': 'abs_max',
                'activation_quantize_type': 'moving_average_abs_max',
                'is_full_quantize': False,
                'batch_size': 8,
                'batch_nums': 1,
            },
            data_loader=train_loader)
        analyzer.statistical_analyse()
        analyzer.metric_error_analyse()
        os.system('rm -rf MobileNetV1_analysis')


if __name__ == '__main__':
    unittest.main()
