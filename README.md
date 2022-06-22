<div align="center" markdown>
<img src="https://github.com/supervisely-ecosystem/import-pointcloud-pcd/releases/download/v0.0.1/poster.png"/>  

# Import Pointclouds PCD

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#Demo-data">Demo Data</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/import-pointcloud-pcd)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/import-pointcloud-pcd)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/import-pointcloud-pcd&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/import-pointcloud-pcd&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/import-pointcloud-pcd&counter=runs&label=runs&123)](https://supervise.ly)

</div>

# Overview

This app allows you to upload pointcloud PCD files with (or without) related images to Supervisely.
The new pointloud project will be created. 

Be aware that "remove files after successful import" flag is enabled by default, it will automatically remove source directory after import.

**Input files structure**

Directory name defines project name, subdirectories define dataset names. Files in root directory will be moved to dataset with name "`ds0`".

**Example 1. Import structure:**

```
my_project
├── xxx.pcd
├── ds_ny
│   └── frame.pcd
└── ds_sf
    └── kitti_0000000001.pcd
```

In this case the following datasets will be created:

- `ds_0` with a single file `xxx.pcd`
- `ds_ny` with a single file `frame.pcd`
- `ds_sf` with a single file `kitti_0000000001.pcd`


**Example 2. Import structure:**

```
my_project
└── dataset_01
    ├── xxx.pcd
    ├── ds_ny
    │   └── frame.pcd
    └── ds_sf
        └── kitti_0000000001.pcd
```

In this case only the one dataset `dataset_01` will be created with all pointcloud files.


**Example 3. PCD files with photo context:**


```
my_project
└── dataset_01
    ├── frame.pcd
    ├── kitti_0000000001.pcd
    └── related_images
        └── kitti_0000000001_pcd
            ├── 0000000000.png
            └── 0000000000.png.json
```

if you want to attach photo context to ply file just create a directory `related_images` near the file. 
Then create directory <filename_with_ext> (in this example we name directory kitti_0000000001_pcd - it's a filename + extension + all symbols . are replaced to _) 
and put there images and corresponding json files with projection matrix. See example for more info.

As a result we will get project `my_project` with 1 dataset `dataset_01`. Dataset will contain 2 pointcloud files, `kitti_0000000001.pcd` with related image, and `frame.pcd` without related image.

### Demo Data
Download [zip archive](https://github.com/supervisely-ecosystem/demo-poinctloud-episodes-annotated/releases/download/v0.0.4/demo_pointcloud.zip) with demo pointcloud project with related image (0.79 MB)
