git clone https://github.com/maftukh/test_delivery_api.git
sudo apt install virtualenv gunicorn
virtualenv -p python3 venv
source venv/bin/activate
cd test_delivery_api
pip install -r requirements.txt