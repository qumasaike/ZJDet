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


voxel_size = [0.8, 0.8, 0.8]

numC_Trans = 80

# self.module_topology = [
#     'backbone', 'gridsample', 'voxel_feature', 'temporal_self_attention', 'dense_head_2d', 'dense_head'
# ]

model = dict(
    type='ZJDet',
    img_backbone=dict(
        pretrained='torchvision://resnet50',
        type='ResNet',
        depth=50,
        num_stages=4,
        out_indices=(2, 3),
        frozen_stages=-1,
        norm_cfg=dict(type='BN', requires_grad=True),
        norm_eval=False,
        with_cp=True,
        style='pytorch'),
    img_neck=dict(
        type='CustomFPN',
        in_channels=[1024, 2048],
        out_channels=32,
        num_outs=1,
        start_level=0,
        out_ids=[0]),
    img_view_transformer=dict(
        type='GridSample',
        voxel_size=voxel_size,
        point_cloud_range=[-6.8, -32.0, -3.0, 70, 32.0, 1.0],
        ),
    voxel_feature_encoder=dict(
        type='VoxelFeature',
        input_channels=40,
        output_channels=64,
        Ncams=data_config['Ncams'],
        gn=True),
    # temporal_fusion=dict(
    #     type='TemporalSelfAttention',),
    # dense_head=dict(type='DenseHead'),
    pts_bbox_head=dict(
        type='Anchor3DHead',
        num_classes=6,
        in_channels=64,
        feat_channels=64,
        use_direction_classifier=True,
        anchor_generator=dict(
            type='AlignedAnchor3DRangeGenerator',
            ranges=[[-6.8, -32.0, -3.0, 70, 32.0, 1.0]],
            # scales=[1, 2, 4],
            scales=[1],
            sizes=[
                [3.9, 1.6, 1.56],
                [7.0, 5.0, 5.0],
                [0.8, 0.6, 1.73],
                [1.76, 0.6, 1.73],
                [0.6, 0.6, 0.6]
            ],
            custom_values=[0, 0],
            rotations=[0, 1.57],
            reshape_out=True),
        assigner_per_size=False,
        diff_rad_by_sin=True,
        dir_offset=-0.7854,  # -pi / 4
        bbox_coder=dict(type='DeltaXYZWLHRBBoxCoder', code_size=9),
        loss_cls=dict(
            type='FocalLoss',
            use_sigmoid=True,
            gamma=2.0,
            alpha=0.25,
            loss_weight=1.0),
        loss_bbox=dict(type='SmoothL1Loss', beta=1.0 / 9.0, loss_weight=1.0),
        loss_dir=dict(
            type='CrossEntropyLoss', use_sigmoid=False, loss_weight=0.2)),
    # model training and testing settings
    train_cfg=dict(
        pts=dict(
            assigner=dict(
                type='MaxIoUAssigner',
                iou_calculator=dict(type='BboxOverlapsNearest3D'),
                pos_iou_thr=0.6,
                neg_iou_thr=0.3,
                min_pos_iou=0.3,
                ignore_iof_thr=-1),
            allowed_border=0,
            code_weight=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.2, 0.2],
            pos_weight=-1,
            debug=False)),
    test_cfg=dict(
        pts=dict(
            use_rotate_nms=True,
            nms_across_levels=False,
            nms_pre=1000,
            nms_thr=0.2,
            score_thr=0.05,
            min_bbox_size=0,
            max_num=500))


    # pts_bbox_head=dict(
    #     type='CenterHead',
    #     in_channels=64,
    #     tasks=[
    #         dict(num_class=1, class_names=['Car']),
    #         dict(num_class=1, class_names=['Truck']),
    #         dict(num_class=1, class_names=['Pedestrian']),
    #         dict(num_class=1, class_names=['Cyclist']),
    #         dict(num_class=1, class_names=['Trafficcone']),
    #         dict(num_class=1, class_names=['Others']),
    #     ],
    #     common_heads=dict(
    #         reg=(2, 2), height=(1, 2), dim=(3, 2), rot=(2, 2), vel=(2, 2)),
    #     share_conv_channel=64,
    #     bbox_coder=dict(
    #         type='CenterPointBBoxCoder',
    #         pc_range=point_cloud_range[:2],
    #         post_center_range=[-6.8, -32.0, -3.0, 70, 32.0, 1.0],
    #         max_num=500,
    #         score_threshold=0.1,
    #         out_size_factor=2,
    #         voxel_size=voxel_size[:2],
    #         code_size=9),
    #     separate_head=dict(
    #         type='SeparateHead', init_bias=-2.19, final_kernel=3),
    #     loss_cls=dict(type='GaussianFocalLoss', reduction='mean'),
    #     loss_bbox=dict(type='L1Loss', reduction='mean', loss_weight=0.25),
    #     norm_bbox=True),
    # model training and testing settings
    # train_cfg=dict(
    #     pts=dict(
    #         point_cloud_range=point_cloud_range,
    #         grid_size=[768, 640, 40],
    #         voxel_size=voxel_size,
    #         out_size_factor=2,
    #         dense_reg=1,
    #         gaussian_overlap=0.1,
    #         max_objs=500,
    #         min_radius=2,
    #         code_weights=[1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.2, 0.2])),
    # test_cfg=dict(
    #     pts=dict(
    #         pc_range=point_cloud_range[:2],
    #         post_center_limit_range=[-61.2, -61.2, -10.0, 61.2, 61.2, 10.0],
    #         max_per_img=500,
    #         max_pool_nms=False,
    #         min_radius=[4, 12, 10, 1, 0.85, 0.175],
    #         score_threshold=0.1,
    #         out_size_factor=2,
    #         voxel_size=voxel_size[:2],
    #         pre_max_size=1000,
    #         post_max_size=83,

    #         # Scale-NMS
    #         nms_type=[
    #             'rotate', 'rotate', 'rotate', 'circle', 'rotate', 'rotate'
    #         ],
    #         nms_thr=[0.2, 0.2, 0.2, 0.2, 0.2, 0.5],
    #         nms_rescale_factor=[
    #             1.0, [0.7, 0.7], [0.4, 0.55], 1.1, [1.0, 1.0], [4.5, 9.0]
    #         ]))
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
        data_config=data_config,
        sequential=False,
        # ego_cam='image0',
        ),
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
        # ego_cam='image0',
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

# data = dict(
#     samples_per_gpu=4,
#     workers_per_gpu=4,
#     train=dict(
#         data_root=data_root,
#         ann_file=data_root + 'bevdetv2-zjdata_infos_train.pkl',
#         pipeline=train_pipeline,
#         classes=class_names,
#         test_mode=False,
#         use_valid_flag=True,
#         # we use box_type_3d='LiDAR' in kitti and nuscenes dataset
#         # and box_type_3d='Depth' in sunrgbd and scannet dataset.
#         box_type_3d='LiDAR'),
#     val=test_data_config,
#     test=test_data_config)

data = dict(
    samples_per_gpu=8,
    workers_per_gpu=4,
    train=dict(
        type='CBGSDataset',
        dataset=dict(
        data_root=data_root,
        ann_file=data_root + 'bevdetv2-zjdata_infos_train.pkl',
        pipeline=train_pipeline,
        classes=class_names,
        test_mode=False,
        use_valid_flag=False,
        # we use box_type_3d='LiDAR' in kitti and nuscenes dataset
        # and box_type_3d='Depth' in sunrgbd and scannet dataset.
        box_type_3d='LiDAR')),
    val=test_data_config,
    test=test_data_config)

for key in ['val', 'test']:
    data[key].update(share_data_config)
data['train']['dataset'].update(share_data_config)


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
