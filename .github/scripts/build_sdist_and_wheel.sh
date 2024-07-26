# Build sdist and wheel
python -m pip install -U pip
python -m pip install build
python -m build

# Check sdist install and imports
mkdir -p test-sdist
cd test-sdist
python -m venv venv-sdist
venv-sdist/bin/python -m pip install ../dist/prompts-*.tar.gz
venv-sdist/bin/python -c "import prompts"
cd ..

# Check wheel install and imports
mkdir -p test-wheel
cd test-wheel
python -m venv venv-wheel
venv-wheel/bin/python -m pip install ../dist/prompts-*.whl
venv-wheel/bin/python -c "import prompts"
cd ..
