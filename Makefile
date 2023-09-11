CODE := population_restorator

lint:
	poetry run pylint $(CODE)

format:
	poetry run isort $(CODE)
	poetry run black $(CODE)

install:
	pip install .

install-dev:
	poetry install --with dev

install-dev-pip:
	pip install -e . --config-settings editable_mode=strict

clean:
	rm -rf ./build ./dist ./population_restorator.egg-info

build:
	poetry build

udpate-pypi: clean build
	$(info Do not forget to execute `poetry config pypi-token.pypi <my-token>` and bump version)
	poetry publish

install-from-build:
	python -m wheel install dist/population_restorator-*.whl
