git clone https://github.com/maftukh/test_delivery_api.git
cd test_delivery_api
sudo apt install virtualenv gunicorn
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt