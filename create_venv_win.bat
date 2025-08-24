python -m venv venv
cd venv/scripts
call activate.bat

echo "upgrade pip"
python -m pip install --upgrade pip

echo "installing requirements"
pip install -r "../../requirements.txt"

echo "done"
pause
