# Python 编程指南

## 装饰器原理

Python 装饰器是一种高阶函数，它接受一个函数作为参数，返回一个新的函数。装饰器常用于日志记录、权限检查、缓存等场景。

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print(f"调用 {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def greet(name):
    return f"你好, {name}"
```

## 上下文管理器

Python 的上下文管理器通过 `__enter__` 和 `__exit__` 方法实现，使用 `with` 语句自动管理资源。

```python
with open("file.txt", "r") as f:
    content = f.read()
```

## 列表推导式

```python
squares = [x**2 for x in range(10)]
```

## 异步编程

使用 async/await 语法进行异步编程，asyncio 是标准库。
