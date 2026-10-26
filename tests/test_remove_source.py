"""`removeSource` must only delete the Team Files source after a complete import.

Before the fix each dataset upload was wrapped in a bare `except: ... continue`, the
point cloud counter was incremented before related images were uploaded, only
`pcd_cnt == 0` aborted, and then `api.file.remove(team_id, INPUT_PATH)` ran - so a
dataset whose related images failed (or that failed outright) was deleted from Team
Files although it was not (completely) imported.
"""
import json

META = json.dumps({"deviceId": "cam", "sensorsData": {}}).encode()


def _layout(bad_meta=False):
    return {
        "/pcd/ds1/a.pcd": b"pcd-a",
        "/pcd/ds1/b.pcd": b"pcd-b",
        "/pcd/ds2/c.pcd": b"pcd-c",
        "/pcd/ds2/related_images/c_pcd/c.png": b"png-c",
        "/pcd/ds2/related_images/c_pcd/c.png.json": b"{not json" if bad_meta else META,
    }


def test_full_success_removes_source(run_app):
    err, api = run_app(_layout())

    assert err is None
    assert len(api.pointcloud.uploaded) == 3
    assert len(api.pointcloud.related_images) == 1
    assert api.file.removed == ["/pcd/"]
    assert api.output_project == 100


def test_malformed_related_image_meta_keeps_source_and_fails_task(run_app):
    err, api = run_app(_layout(bad_meta=True))

    assert api.file.removed == []  # source kept: c.png was never imported
    assert len(api.pointcloud.uploaded) == 3  # what was imported stays in the project
    assert api.pointcloud.related_images == []
    assert api.output_project == 100
    assert err is not None and "ds2" in str(err)  # task not reported as success


def test_rejected_dataset_keeps_source_and_fails_task(run_app):
    err, api = run_app(_layout(), reject_names={"a.pcd"})

    assert api.file.removed == []  # source kept: ds1 is not in the project
    assert sorted(n for _, n in api.pointcloud.uploaded) == ["c.pcd"]
    assert err is not None and "ds1" in str(err)


def test_unsupported_files_keep_source(run_app):
    files = _layout()
    files["/pcd/ds1/scan.ply"] = b"ply"
    err, api = run_app(files)

    assert err is None  # skipping is not an error
    assert len(api.pointcloud.uploaded) == 3
    assert api.file.removed == []


def test_orphan_image_keeps_source(run_app):
    # an image that is not a related image of any point cloud is not imported
    files = _layout()
    files["/pcd/ds1/photo.jpg"] = b"jpg"
    err, api = run_app(files)

    assert err is None
    assert api.file.removed == []


def test_remove_source_off_never_removes(run_app):
    err, api = run_app(_layout(), remove_source=False)

    assert err is None
    assert api.file.removed == []
