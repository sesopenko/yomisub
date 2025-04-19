# sesopenko/yomisub

## Requirements

* Python 3.11

Debian 12 requirements:

```bash
sudo apt update

# install python venv
sudo apt install python3.11-venv

# install gtk dependencies

sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 libgirepository1.0-dev gir1.2-gtk-3.0

# add system site package to venv
python3 -m venv .venv --system-site-packages

# reload venv
source .venv/bin/activate

# test that gi can now be imported
python -c "import gi"
```

Install pip requirements

```bash
source .venv/bin/activate
pip install -r requirements.txt
```