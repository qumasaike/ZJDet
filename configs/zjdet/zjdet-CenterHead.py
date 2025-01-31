# Copyright (c) Phigent Robotics. All rights reserved.

_base_ = ['../_base_/datasets/nus-3d.py', '../_base_/default_runtime.py']
# Global
# If point cloud range is changed, the models should also change their point
# cloud range accordingly
point_cloud_range = [-6.8, -32.0, -3.0, 70.0, 32.0, 1.0]
# For nuScenes we usually do 10-class detection
class_names = [
    'Car', 'Van', 'Pedestrian', 'Cyclist', 'Trafficcone', 'Others'
]

data_config = {
    'cams': [
        'image0', 'image1', 'image2', 'image5', 
    ],
    'Ncams':
    4,
    'input_size': (720, 1280),#(256, 704),
    'src_size': (720, 1280),

    # Augmentation
    # 'resize': (0.00, 0.00),#(-0.06, 0.11),#1.0 + resize
    # 'rot': (0, 0),  #(-5.4, 5.4),
    # 'flip': False, #True,
    # 'crop_h': (0.0, 0.0),
    # 'resize_test': 0.00,
    'resize': (-0.06, 0.11),#1.0 + resize
    'rot': (-5.4, 5.4),
    'flip': True,
    'crop_h': (0.0, 0.0),
    'resize_test': 0.00,
}

# Model


voxel_size = [0.2, 0.2, 0.2]

numC_Trans = 80

# self.module_topology = [
#     'backbone', 'gridsample', 'voxel_feature', 'temporal_self_attention', 'dense_head_2d', 'dense_head'
# ]

model = dict(
    type='ZJDet',
    img_backbone=dict(
        # pretrained='ckpts/resnet34-333f7ec4.pth',
        type='ResNet34ZJ',
        block='BasicBlock',
        layers=[3, 4, 6, 3],
        ),
    img_neck=dict(
        # pretrained='ckpts/resnet34-333f7ec4.pth',
        type='FeatureExtractionNeck',
        cfg=dict(in_dims=[3, 64, 128, 128, 128],
                    start_level=2,
            stereo_dim=[32, 32],
            with_upconv=True,
            cat_img_feature=False,
            sem_dim=[128, 32],
            GN=True),
        ),
    img_view_transformer=dict(
        type='GridSample',
        voxel_size=[0.2, 0.2, 0.2],
        point_cloud_range=[-6.8, -32.0, -3.0, 70, 32.0, 1.0],
        ),
    voxel_feature_encoder=dict(
        type='VoxelFeature',
        input_channels=160,
        output_channels=64,
        Ncams=data_config['Ncams'],
        gn=True),
    # temporal_fusion=dict(
    #     type='TemporalSelfAttention',),
    # dense_head=dict(type='DenseHead'),



    pts_bbox_head=dict(
        type='CenterHead',
        in_channels=64,
        tasks=[
            dict(num_class=6, class_names=class_names),
        ],
        common_heads=dict(
            reg=(2, 2), height=(1, 2), dim=(3, 2), rot=(2, 2), vel=(2, 2)),
        share_conv_channel=64,
        bbox_coder=dict(
            type='CenterPointBBoxCoder',
            pc_range=point_cloud_range[:2],
            post_center_range=[-61.2, -61.2, -10.0, 61.2, 61.2, 10.0],
            max_num=500,
            score_threshold=0.1,
            out_size_factor=2,
            voxel_size=voxel_size[:2],
            code_size=9),
        separate_head=dict(
            type='SeparateHead', init_bias=-2.19, final_kernel=3),
        loss_cls=dict(type='GaussianFocalLoss', reduction='mean'),
        loss_bbox=dict(type='L1Loss', reduction='mean', loss_weight=0.25),
        norm_bbox=True),

    # model training and testing settings
    train_cfg=dict(
        pts=dict(
            point_cloud_range=point_cloud_range,
            grid_size=[768, 640, 40],
            voxel_size=voxel_size,
            out_size_factor=2,
            dense_reg=1,
            gaussian_overlap=0.1,
            max_objs=500,
            min_radius=2,
            code_weights=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.2, 0.2])),
    test_cfg=dict(
        pts=dict(
            pc_range=point_cloud_range[:2],
            post_center_limit_range=[-61.2, -61.2, -10.0, 61.2, 61.2, 10.0],
            max_per_img=500,
            max_pool_nms=False,
            min_radius=[4, 12, 10, 1, 0.85, 0.175],
            score_threshold=0.1,
            out_size_factor=2,
            voxel_size=voxel_size[:2],
            pre_max_size=1000,
            post_max_size=500,

            # Scale-NMS
            nms_type=['rotate'],
            nms_thr=[0.2],
            nms_rescale_factor=[[1.0, 0.7, 0.7, 0.4, 0.55,
                                 1.1, 1.0, 1.0, 1.5, 3.5]]
        )
    )
)

# Data
dataset_type = 'NuScenesDataset'
data_root = 'datasets/zjdata/'
file_client_args = dict(backend='disk')

bda_aug_conf = dict(
    rot_lim=(0.0, 0.0),
    scale_lim=(1.0, 1.0),
    flip_dx_ratio=0.0,
    flip_dy_ratio=0.0,)

    # rot_lim=(-22.5, 22.5),
    # scale_lim=(0.95, 1.05),
    # flip_dx_ratio=0.5,
    # flip_dy_ratio=0.5),

    # 'resize': (0.00, 0.00),#(-0.06, 0.11),#1.0 + resize
    # 'rot': (0, 0),  #(-5.4, 5.4),
    # 'flip': False, #True,
    # 'crop_h': (0.0, 0.0),
    # 'resize_test': 0.00,

train_pipeline = [
    dict(
        type='PrepareImageInputs',
        is_train=True,
        data_config=data_config),
    dict(
        type='LoadAnnotationsBEVDepth',
        bda_aug_conf=bda_aug_conf,
        classes=class_names),
    dict(type='ObjectRangeFilter', point_cloud_range=point_cloud_range),
    dict(type='ObjectNameFilter', classes=class_names),
    dict(type='DefaultFormatBundle3D', class_names=class_names),
    dict(
        type='Collect3D', keys=['img_inputs', 'gt_bboxes_3d', 'gt_labels_3d'])
]

test_pipeline = [
    dict(type='PrepareImageInputs', data_config=data_config,
        sequential=False,
        ),
    dict(
        type='LoadAnnotationsBEVDepth',
        bda_aug_conf=bda_aug_conf,
        classes=class_names,
        is_train=False),
    dict(
        type='LoadPointsFromFile',
        coord_type='LIDAR',
        load_dim=4,
        use_dim=4,
        file_client_args=file_client_args),
    dict(
        type='MultiScaleFlipAug3D',
        img_scale=(1333, 800),
        pts_scale_ratio=1,
        flip=False,
        transforms=[
            dict(
                type='DefaultFormatBundle3D',
                class_names=class_names,
                with_label=False),
            dict(type='Collect3D', keys=['points', 'img_inputs'])
        ])
]

input_modality = dict(
    use_lidar=False,
    use_camera=True,
    use_radar=False,
    use_map=False,
    use_external=False)

share_data_config = dict(
    type=dataset_type,
    classes=class_names,
    modality=input_modality,
    img_info_prototype='bevdet',
)

test_data_config = dict(
    data_root=data_root,
    pipeline=test_pipeline,
    classes=class_names,
    ann_file=data_root + 'bevdetv2-zjdata_infos_val.pkl')

data = dict(
    samples_per_gpu=4,
    workers_per_gpu=4,
    train=dict(
        data_root=data_root,
        ann_file=data_root + 'bevdetv2-zjdata_infos_train.pkl',
        pipeline=train_pipeline,
        classes=class_names,
        test_mode=False,
        use_valid_flag=True,
        # we use box_type_3d='LiDAR' in kitti and nuscenes dataset
        # and box_type_3d='Depth' in sunrgbd and scannet dataset.
        box_type_3d='LiDAR'),
    val=test_data_config,
    test=test_data_config)

for key in ['train', 'val', 'test']:
    data[key].update(share_data_config)

# Optimizer
optimizer = dict(type='AdamW', lr=2e-4, weight_decay=1e-07)
optimizer_config = dict(grad_clip=dict(max_norm=5, norm_type=2))
lr_config = dict(
    policy='step',
    warmup='linear',
    warmup_iters=200,
    warmup_ratio=0.001,
    step=[24,])
runner = dict(type='EpochBasedRunner', max_epochs=24)

custom_hooks = [
    dict(
        type='MEGVIIEMAHook',
        init_updates=10560,
        priority='NORMAL',
    ),
]

# unstable
# fp16 = dict(loss_scale='dynamic')
