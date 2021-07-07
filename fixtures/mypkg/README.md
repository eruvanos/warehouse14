# Fixture package to test API

```
# requirements
pip install --upgrade build twine

# build with
python -m build

# upload
twine upload -u eruvanos -p xxx --repository-url http://localhost:5000/simple/ dist/*

```


## Example code

```python
def greet(name="User"):
    print(f"Hello {name}")
```