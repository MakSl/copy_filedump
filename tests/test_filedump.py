import subprocess


def test_16398():
    result = subprocess.run(
        ["python3", "src/my_filedump.py", "tests/blobs/16398"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert len(result.stdout.split("\n")) == 34


def test_16398_2():
    result = subprocess.run(
        ["python3", "src/my_filedump.py", "tests/blobs/16398-2"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert len(result.stdout.split("\n")) == 274


def test_24585():
    result = subprocess.run(
        ["python3", "src/my_filedump.py", "tests/blobs/24585"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert len(result.stdout.split("\n")) == 50551
